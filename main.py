from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Response
from fastapi.security.api_key import APIKeyHeader
import os
from bcf.bcfxml import BcfXml # WIEDER DIE ALTE BIBLIOTHEK

# --- Konfiguration & Sicherheit ---
app = FastAPI(
    title="BCF API Service",
    description="Eine API zum Lesen von BCF-Dateien auf dem Server.",
    version="2.1.0", # Version angepasst
)

DATA_FOLDER = "/data"
API_KEY_NAME = "X-API-KEY"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)
SECRET_API_KEY = os.getenv("API_KEY")

async def get_api_key(api_key: str = Depends(api_key_header)):
    if not SECRET_API_KEY or api_key != SECRET_API_KEY:
        raise HTTPException(status_code=403, detail="Ungültiger oder fehlender API-Schlüssel")
    return api_key

# --- API-Endpunkte ---

@app.get("/")
def read_root():
    return {"message": "BCF API Service ist online (Python 3.9)."}

@app.get("/bcf", summary="Alle BCF-Dateien auflisten")
def list_bcf_files():
    try:
        files = [f for f in os.listdir(DATA_FOLDER) if f.endswith('.bcfzip')]
        return {"files": files}
    except FileNotFoundError:
        return {"files": []}

@app.get("/bcf/{file_name}", summary="Inhalt einer BCF-Datei lesen")
def process_bcf_file(file_name: str):
    file_path = os.path.join(DATA_FOLDER, file_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Datei '{file_name}' nicht gefunden.")

    try:
        bcf = BcfXml(file_path)
        issues = []
        for i, topic in enumerate(bcf.topics):
            try:
                issue_data = {
                    "guid": topic.guid,
                    "title": topic.title,
                    "status": topic.topic_status,
                    "priority": topic.priority,
                    "has_snapshot": bool(topic.viewpoints)
                }
                issues.append(issue_data)
            except Exception as e:
                error_message = f"Fehler bei Topic #{i} (GUID: {getattr(topic, 'guid', 'N/A')}): {e}"
                print(error_message)
                issues.append({"error": "Konnte dieses Topic nicht verarbeiten.", "details": error_message})
        return {"file": file_name, "issues": issues}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generischer Fehler beim Laden der BCF-Datei: {e}")


@app.post("/bcf/{file_name}", summary="Neue BCF-Datei hochladen", dependencies=[Depends(get_api_key)])
async def upload_bcf_file(file_name: str, file: UploadFile = File(...)):
    if not file_name.endswith(".bcfzip"):
        raise HTTPException(status_code=400, detail="Dateiname muss auf .bcfzip enden.")
    
    file_path = os.path.join(DATA_FOLDER, file_name)
    
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
        return {"message": f"Datei '{file_name}' erfolgreich hochgeladen."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Speichern der Datei: {e}")
