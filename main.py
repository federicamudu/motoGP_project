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
CATEGORY_GP = "e8c110ad-64aa-4e8e-8a86-f2f152f6a942"

CATEGORY_TEAMS_GP = "737ab122-76e1-4081-bedb-334caaa18c70" # UUID per V1 (Team e Piloti)
SEASON_YEAR = 2026

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
        data = client.get_events(SEASON_UUID)
        return [
            {
                "id": e['id'],
                "nome": e['name'],
                "circuito": e['circuit']['name'],
                "data": e['date_start'],
                "stato": e['status']
            } for e in data if not e.get('test')
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/classifica")
def read_standings():
    try:
        data = client.get_world_standings(SEASON_UUID, CATEGORY_GP)
        riders = data.get('classification', {}).get('rider', [])
        return [
            {
                "id": r['rider']['id'],
                "pos": r['position'],
                "nome": r['rider']['full_name'],
                "punti": r.get('points', 0),
                "team": r['team_name']
            } for r in riders
        ]
    except Exception as e:
        print(f"Errore tecnico: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/api/risultati_gara/{id_evento}")
def read_risultati_gara(id_evento: str):
    """
    Trova automaticamente l'ID della sessione 'Gara' (RAC) partendo dall'ID dell'evento
    e restituisce i risultati completi.
    """
    try:
        # 1. Chiediamo al client tutte le sessioni di questo weekend
        sessioni = client.get_sessions(id_evento, CATEGORY_GP)
        
        # 2. Cerchiamo quella di tipo "RAC" (Race/Gara)
        gara = next((s for s in sessioni if s.get('type') == 'RAC'), None)
        
        # Se la gara non c'è (es. weekend annullato) o non è finita
        if not gara:
            return []
        
        # 3. Ora che abbiamo l'ID della gara, chiediamo la classifica esatta
        data = client.get_classifications(gara['id'])
        classif = data.get('classification', [])
        
        return [
            {
                "pos": p.get('position', 'NC'), # NC = Non Classificato/Ritirato
                "nome": p['rider']['full_name'],
                "tempo": p.get('time', 'N/D'),
                "punti": p.get('points', 0)
            } for p in classif
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/api/pilota/{rider_id}")
def read_pilota(rider_id: str):
    # Forzo i valori qui dentro così non c'è rischio che non li trovi
    CAT_TEAMS = "737ab122-76e1-4081-bedb-334caaa18c70"
    ANNO = 2026

    try:
        teams_data = client.get_all_riders_data(CAT_TEAMS, ANNO)
        
        if not isinstance(teams_data, list):
            raise ValueError("L'API non ha restituito una lista valida")

        target_rider = None
        for team in teams_data:
            if not isinstance(team, dict): continue
            for r in team.get('riders', []):
                if not isinstance(r, dict): continue
                if r.get('id') == rider_id:
                    target_rider = r
                    break
            if target_rider: break

        if not target_rider:
            return {
                "id": rider_id, "nome": "Dati Pilota Non Trovati", "numero": "??",
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
        print(f"ERRORE BRUTALE: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))