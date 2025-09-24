from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Response
from fastapi.security.api_key import APIKeyHeader
import os
from typing import List
from bcf.bcfxml import BcfXml

app = FastAPI(
    title="BCF API Service",
    description="Eine API zum Lesen und Bearbeiten von BCF-Dateien auf dem Server.",
    version="2.0.0",
)

DATA_FOLDER = "/data"
API_KEY_NAME = "X-API-KEY"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)
SECRET_API_KEY = os.getenv("API_KEY", "default-secret-key-change-me")
os.makedirs(DATA_FOLDER, exist_ok=True)

async def get_api_key(api_key: str = Depends(api_key_header)):
    if api_key != SECRET_API_KEY:
        raise HTTPException(status_code=403, detail="Ungültiger oder fehlender API-Key")
    return api_key

@app.get("/")
def read_root():
    return {"message": "BCF API Service v2 ist online."}

@app.get("/bcf", summary="Alle BCF-Dateien auflisten")
def list_bcf_files():
    try:
        files = [f for f in os.listdir(DATA_FOLDER) if f.endswith('.bcfzip')]
        return {"files": files}
    except FileNotFoundError:
        return {"files": []}

@app.get("/bcf/{file_name}", summary="Inhalt einer BCF-Datei lesen")
def process_bcf_file(file_name: str):
    """Liest eine BCF-Datei und gibt die Issues zurück. Fängt Fehler bei einzelnen Topics ab."""
    file_path = os.path.join(DATA_FOLDER, file_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Datei '{file_name}' nicht gefunden.")

    try:
        bcf = BcfXml(file_path)
        issues = []

        # NEU: Wir gehen über jedes Topic und fangen Fehler einzeln ab
        for i, topic in enumerate(bcf.topics):
            try:
                # Wir versuchen, die Daten für ein Topic zu extrahieren
                issue_data = {
                    "guid": topic.guid,
                    "title": topic.title,
                    "status": topic.topic_status,
                    "priority": topic.priority,
                    "has_snapshot": bool(topic.viewpoints)
                }
                issues.append(issue_data)
            except Exception as e:
                # Wenn ein Topic fehlschlägt, protokollieren wir den Fehler und machen weiter
                # Dieser Print-Befehl schreibt die Fehlermeldung in die Logs deines Coolify-Containers
                error_message = f"Fehler bei der Verarbeitung von Topic #{i} (GUID: {getattr(topic, 'guid', 'N/A')}): {e}"
                print(error_message)

                # Optional: Füge eine Fehlermeldung zur JSON-Antwort hinzu, statt still zu scheitern
                issues.append({
                    "error": "Konnte dieses Topic nicht verarbeiten.",
                    "guid": getattr(topic, 'guid', 'N/A'),
                    "details": str(e) # Wir geben den Fehlertext auch in der API-Antwort zurück
                })

        return {"file": file_name, "issues": issues}

    except Exception as e:
        # Dieser äußere Fehler tritt auf, wenn schon das Laden der gesamten BCF-Datei scheitert
        raise HTTPException(status_code=500, detail=f"Generischer Fehler beim Laden der BCF-Datei: {e}")

@app.get("/bcf/{file_name}/snapshot/{topic_guid}", summary="Snapshot eines Issues abrufen")
def get_snapshot(file_name: str, topic_guid: str):
    file_path = os.path.join(DATA_FOLDER, file_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="BCF-Datei nicht gefunden.")
    try:
        bcf = BcfXml(file_path)
        topic = bcf.get_topic_by_guid(topic_guid)
        if not topic:
            raise HTTPException(status_code=404, detail="Topic-GUID nicht gefunden.")
        if topic.viewpoints and topic.viewpoints.snapshot:
            snapshot_filename = topic.viewpoints.snapshot
            snapshot_data = bcf.get_file_data(snapshot_filename)
            return Response(content=snapshot_data, media_type="image/png")
        raise HTTPException(status_code=404, detail="Kein Snapshot für dieses Topic gefunden.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Extrahieren des Snapshots: {e}")

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

@app.put("/bcf/{file_name}/{topic_guid}", summary="Ein Issue bearbeiten", dependencies=[Depends(get_api_key)])
def update_bcf_topic(file_name: str, topic_guid: str, new_status: str, new_title: str = None):
    file_path = os.path.join(DATA_FOLDER, file_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="BCF-Datei nicht gefunden.")
    try:
        bcf = BcfXml(file_path)
        topic = bcf.get_topic_by_guid(topic_guid)
        if not topic:
            raise HTTPException(status_code=404, detail="Topic-GUID nicht gefunden.")
        topic.topic_status = new_status
        if new_title:
            topic.title = new_title
        bcf.save(file_path)
        return {
            "message": "Topic erfolgreich aktualisiert.",
            "file": file_name,
            "updated_topic_guid": topic_guid
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Bearbeiten der BCF-Datei: {e}")

