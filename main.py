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
    try:
        rider = client.get_rider(rider_id)
        
        if not rider:
            raise HTTPException(status_code=404, detail="Pilota non trovato")
        
        return {
            "id": rider.get('id'),
            "nome": rider.get('full_name', 'N/D'),
            "numero": rider.get('number', '??'),
            "nazione": rider.get('country', {}).get('name', 'N/D') if rider.get('country') else 'N/D',
            "nascita": rider.get('birth_date', 'N/D'),
            "citta": rider.get('birth_city', 'N/D'),
            "altezza": f"{rider.get('height')} cm" if rider.get('height') else 'N/D',
            "peso": f"{rider.get('weight')} kg" if rider.get('weight') else 'N/D',
            "foto": rider.get('image') if rider.get('image') else 'N/D'
        }
    except Exception as e:
        print(f"Errore nel recupero pilota {rider_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))