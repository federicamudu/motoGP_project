from fastapi import FastAPI, HTTPException
from motogp_client import MotoGPClient
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="MotoGP API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

client = MotoGPClient()

SEASON_UUID = "e88b4e43-2209-47aa-8e83-0e0b1cedde6e"
SEASON_YEAR = 2026

# UUID per la Versione 2 (Risultati, Calendario, Classifica)
CAT_V2 = {
    "motogp": "e8c110ad-64aa-4e8e-8a86-f2f152f6a942",
    "moto2": "549640b8-fd9c-4245-acfd-60e4bc38b25c",
    "moto3": "954f7e65-2ef2-4423-b949-4961cc603e45"
}

# UUID per la Versione 1 (Team e Dati Piloti)
CAT_V1 = {
    "motogp": "737ab122-76e1-4081-bedb-334caaa18c70",
    "moto2": "ea854a67-73a4-4a28-ac77-d67b3b2a530a",
    "moto3": "1ab203aa-e292-4842-8bed-971911357af1"
}

# Aggiungiamo la rotta base per non far arrabbiare Vercel sulla Home!
@app.get("/")
def read_root():
    return {
        "status": "Vittoria! Il server è online 🏁", 
        "endpoints": ["/api/calendario", "/api/classifica"]
    }

@app.get("/api/calendario")
def read_calendar():
    try:
        url = f"{client.base_url_v1}/events?seasonYear=2026"
        data = client._fetch(url)
        
        risultato = []
        for e in data:
            if e.get('kind') in ['TEST', 'MEDIA']: 
                continue
            
            circuit = e.get('circuit') or {}
            track = circuit.get('track') or {}
            assets = track.get('assets') or {}
            
            info_path = assets.get('info', {}).get('path', '')
            simple_path = assets.get('simple', {}).get('path', '')
            immagine_circuito = info_path or simple_path
            
            # --- NUOVO: ESTRAZIONE DETTAGLI PISTA ---
            descrizioni = circuit.get('circuit_descriptions') or []
            # Cerchiamo l'italiano, se non c'è prendiamo l'inglese
            desc = next((d.get('description', '') for d in descrizioni if d.get('language') == 'it'), "")
            if not desc:
                desc = next((d.get('description', '') for d in descrizioni if d.get('language') == 'en'), "")
            
            # Puliamo i tag HTML fastidiosi
            desc = desc.replace('<p>', '').replace('</p>', '').replace('\n', ' ').strip()
            
            dettagli = {
                "lunghezza": track.get('lenght_units', {}).get('kiloMeters', 'N/D'),
                "curve_sx": track.get('left_corners', 'N/D'),
                "curve_dx": track.get('right_corners', 'N/D'),
                "rettilineo": track.get('longest_straight_units', {}).get('meters', 'N/D'),
                "descrizione": desc
            }
            # ----------------------------------------
            
            risultato.append({
                "id": e.get('id'),
                "nome": e.get('name'),
                "circuito": circuit.get('name', 'Circuito non definito'),
                "immagine_circuito": immagine_circuito,
                "data": e.get('date_start'),
                "stato": e.get('status'),
                "dettagli": dettagli # Passiamo i dettagli a React!
            })
        return risultato
    except Exception as e:
        import traceback
        print(f"ERRORE CALENDARIO: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/classifica/{categoria}")
def read_standings(categoria: str):
    try:
        # Se React chiede una categoria che non esiste, usiamo motogp di base
        cat_id = CAT_V2.get(categoria, CAT_V2["motogp"])
        
        data = client.get_world_standings(SEASON_UUID, cat_id)
        riders = data.get('classification', {}).get('rider', [])
        return [
            {
                "id": r['rider']['id'],
                "pos": r['position'],
                "nome": r['rider']['full_name'],
                "punti": r.get('points', 0),
                "team": r.get('team_name', 'N/D') # Mettiamo un N/D di sicurezza
            } for r in riders
        ]
    except Exception as e:
        print(f"Errore tecnico classifica: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/api/risultati_gara/{id_evento}")
def read_risultati_gara(id_evento: str, categoria: str = "motogp", tipo: str = "RAC"):
    """Accetta la categoria come parametro (es. ?categoria=moto2)"""
    try:
        # Peschiamo l'UUID della Versione 2 per le sessioni
        cat_id = CAT_V2.get(categoria, CAT_V2["motogp"])
        sessioni = client.get_sessions(id_evento, cat_id)
        
        sessione = next((s for s in sessioni if s.get('type') == tipo), None)
        if not sessione:
            return []
        
        data = client.get_classifications(sessione['id'])
        classif = data.get('classification', [])
        
        return [
            {
                "pos": p.get('position', 'NC'),
                "nome": p['rider']['full_name'],
                "tempo": p.get('time', 'N/D'),
                "punti": p.get('points', 0),
                "team": p.get('team', {}).get('name', 'N/D')
            } for p in classif
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/api/pilota/{rider_name}")
def read_pilota(rider_name: str, categoria: str = "motogp"):
    """Accetta la categoria per cercare nel database Team corretto"""
    try:
        # Peschiamo l'UUID della Versione 1 per i Team
        cat_v1_id = CAT_V1.get(categoria, CAT_V1["motogp"])
        teams_data = client.get_all_riders_data(cat_v1_id, SEASON_YEAR)
        
        if not isinstance(teams_data, list):
            raise ValueError("L'API non ha restituito una lista")

        target_rider = None
        nome_cercato = rider_name.strip().lower()

        for team in teams_data:
            if not isinstance(team, dict): continue
            for r in team.get('riders', []):
                if not isinstance(r, dict): continue
                nome_ufficiale = f"{r.get('name', '')} {r.get('surname', '')}".strip().lower()
                if nome_ufficiale == nome_cercato:
                    target_rider = r
                    break
            if target_rider: break

        if not target_rider:
            return {
                "id": "??", "nome": rider_name, "numero": "??",
                "nazione": "N/D", "nascita": "N/D", "citta": "N/D",
                "foto": None, "team": "N/D", "ruolo": "Sconosciuto"
            }

        career = target_rider.get('current_career_step')
        if not isinstance(career, dict): career = {}
        pictures = career.get('pictures')
        if not isinstance(pictures, dict): pictures = {}
        profile = pictures.get('profile')
        if not isinstance(profile, dict): profile = {}
        country = target_rider.get('country')
        if not isinstance(country, dict): country = {}

        return {
            "id": target_rider.get('id'),
            "nome": f"{target_rider.get('name', '')} {target_rider.get('surname', '')}".strip(),
            "numero": career.get('number', '??'),
            "nazione": country.get('name', 'N/D'),
            "nascita": target_rider.get('birth_date', 'N/D'),
            "citta": target_rider.get('birth_city', 'N/D'),
            "foto": profile.get('main'),
            "team": career.get('sponsored_team', 'N/D'),
            "ruolo": career.get('type', 'N/D')
        }
    except Exception as e:
        import traceback
        print(f"ERRORE: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/api/classifica_costruttori/{categoria}")
def read_constructors(categoria: str):
    try:
        cat_id = CAT_V2.get(categoria, CAT_V2["motogp"])
        url = f"{client.base_url_v2}/results/world-standings?type=constructor&season={SEASON_UUID}&category={cat_id}"
        data = client._fetch(url)
        
        classifica = data.get('classification')
        if isinstance(classifica, dict):
            items = classifica.get('constructor', [])
        elif isinstance(classifica, list):
            items = classifica
        else:
            items = []

        risultato = []
        for c in items:
            costruttore = c.get('constructor') or {}
            nome = costruttore.get('name', 'N/D') if isinstance(costruttore, dict) else str(costruttore)
            
            risultato.append({
                "pos": c.get('position', 0),
                "nome": nome,
                "punti": c.get('points', 0)
            })
        return risultato
    except Exception as e:
        import traceback
        print(f"💥 ERRORE COSTRUTTORI:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/classifica_team/{categoria}")
def read_teams(categoria: str):
    try:
        cat_id = CAT_V2.get(categoria, CAT_V2["motogp"])
        url = f"{client.base_url_v2}/results/world-standings?type=team&season={SEASON_UUID}&category={cat_id}"
        data = client._fetch(url)
        
        classifica = data.get('classification')
        if isinstance(classifica, dict):
            items = classifica.get('team', [])
        elif isinstance(classifica, list):
            items = classifica
        else:
            items = []

        risultato = []
        for t in items:
            squadra = t.get('team') or {}
            nome = squadra.get('name', 'N/D') if isinstance(squadra, dict) else str(squadra)
            
            risultato.append({
                "pos": t.get('position', 0),
                "nome": nome,
                "punti": t.get('points', 0)
            })
        return risultato
    except Exception as e:
        import traceback
        print(f"💥 ERRORE TEAM:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
    
