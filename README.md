# MotoGP Unofficial API (BFF)

Questo progetto è un'API di backend (Backend-for-Frontend) costruita con **FastAPI** per aggregare e pulire i dati del campionato MotoGP.

## 🛡️ Disclaimer 
Questo progetto è realizzato esclusivamente a **scopo didattico e personale**. 
- Non è un'API ufficiale di Dorna Sports o MotoGP.
- Tutti i dati e i marchi appartengono ai rispettivi proprietari.
- Viene utilizzato un sistema di **In-Memory Caching** per minimizzare le richieste ai server ufficiali e rispettare i loro limiti tecnici.

## 🚀 Funzionalità
- `/api/calendario`: Elenco gare stagionali.
- `/api/classifica`: Classifica mondiale piloti aggiornata.
- `/api/risultati/{id}`: Dettagli tempi di ogni sessione.

## 🛠️ Tech Stack
- Python 3.9+
- FastAPI (Web Framework)
- Vercel (Deployment)