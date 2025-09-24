from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Response
from fastapi.security.api_key import APIKeyHeader
import os
import bcfpy # NEUE BIBLIOTHEK

# --- Konfiguration & Sicherheit ---
app = FastAPI(
    title="BCF API Service",
    description="Eine API zum Lesen und Bearbeiten von BCF-Dateien auf dem Server.",
    version="3.0.0", # Version erhöht
)

DATA_FOLDER = "/data"
API_KEY_NAME = "X-API-KEY"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)
SECRET_API_KEY = os.getenv("API_KEY") # Lese den Key aus der Umgebung

async def get_api_key(api_key: str = Depends(api_key_header)):
    """Prüft, ob der mitgelieferte API-Schlüssel gültig ist."""
    if not SECRET_API_KEY or api_key != SECRET_API_KEY:
        raise HTTPException(status_code=403, detail="Ungültiger oder fehlender API-Schlüssel")
    return api_key

# --- API-Endpunkte ---

@app.get("/")
def read_root():
    return {"message": "BCF API Service v3 ist online."}

@app.get("/bcf", summary="Alle BCF-Dateien auflisten")
def list_bcf_files():
    """Listet alle .bcfzip Dateien im Datenordner auf."""
    try:
        files = [f for f in os.listdir(DATA_FOLDER) if f.endswith('.bcfzip')]
        return {"files": files}
    except FileNotFoundError:
        return {"files": []}

@app.get("/bcf/{file_name}", summary="Inhalt einer BCF-Datei lesen")
def process_bcf_file(file_name: str):
    """Liest eine BCF-Datei mit bcfpy und gibt die Issues zurück."""
    file_path = os.path.join(DATA_FOLDER, file_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Datei '{file_name}' nicht gefunden.")

    try:
        # NEUE SYNTAX zum Öffnen der Datei mit bcfpy
        bcf = bcfpy.open(file_path)
        issues = []
        for topic in bcf.topics:
            issue_data = {
                "guid": topic.guid,
                "title": topic.title,
                "status": topic.topic_status,
                "priority": topic.priority,
                 # bcfpy hat eine andere Art, auf Snapshots zuzugreifen
                "has_snapshot": bool(topic.viewpoints)
            }
            issues.append(issue_data)
        return {"file": file_name, "issues": issues}
    except Exception as e:
        # Allgemeiner Fehler, falls bcfpy auch fehlschlägt
        raise HTTPException(status_code=500, detail=f"Fehler bei der Verarbeitung der BCF-Datei: {e}")

# Snapshot-Endpunkt (vorerst auskommentiert, da die Logik für bcfpy anders sein könnte)
# @app.get("/bcf/{file_name}/snapshot/{topic_guid}", ...)
# ...

@app.post("/bcf/{file_name}", summary="Neue BCF-Datei hochladen", dependencies=[Depends(get_api_key)])
async def upload_bcf_file(file_name: str, file: UploadFile = File(...)):
    """Lädt eine neue BCF-Datei auf den Server hoch."""
    if not file_name.endswith(".bcfzip"):
        raise HTTPException(status_code=400, detail="Dateiname muss auf .bcfzip enden.")
    
    file_path = os.path.join(DATA_FOLDER, file_name)
    
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
        return {"message": f"Datei '{file_name}' erfolgreich hochgeladen."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Speichern der Datei: {e}")

# PUT-Endpunkt zum Bearbeiten (vorerst auskommentiert, da bcfpy keine Schreibfunktion hat)
# @app.put("/bcf/{file_name}/{topic_guid}", ...)
# ...
