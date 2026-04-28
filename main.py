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
                "pos": r['position'],
                "nome": r['rider']['full_name'],
                "punti": r.get('points', 0),
                "team": r['team_name']
            } for r in riders
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))