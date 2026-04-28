from fastapi import FastAPI, HTTPException
from api.motogp_client import MotoGPClient

app = FastAPI(title="MotoGP Unofficial API")
client = MotoGPClient()

# ID Costanti per la stagione 2026
SEASON_UUID = "e88b4e43-2209-47aa-8e83-0e0b1cedde6e"
CATEGORY_GP = "e8c110ad-64aa-4e8e-8a86-f2f152f6a942"

@app.get("/calendario")
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

@app.get("/classifica")
def read_standings():
    try:
        data = client.get_world_standings(SEASON_UUID, CATEGORY_GP)
        riders = data.get('classification', {}).get('rider', [])
        return [
            {
                "pos": r['position'],
                "nome": r['rider']['full_name'],
                "punti": r.get('points', 0),
                "team": r['team_name']
            } for r in riders
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/risultati/{session_id}")
def read_results(session_id: str):
    try:
        data = client.get_classifications(session_id)
        classif = data.get('classification', [])
        return [
            {
                "pos": p.get('position', 'NC'),
                "nome": p['rider']['full_name'],
                "tempo": p.get('time', 'N/D'),
                "punti": p.get('points', 0)
            } for p in classif
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))