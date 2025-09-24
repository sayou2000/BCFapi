from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Response, Header
from fastapi.security.api_key import APIKeyHeader
import os
from typing import List

# Wir importieren die BcfXml-Klasse aus der bcf-client Bibliothek
from bcf.bcfxml import BcfXml
from bcf.topic import Topic

# --- Konfiguration & Sicherheit (NEU) ---

app = FastAPI(
    title="BCF API Service",
    description="Eine API zum Lesen und Bearbeiten von BCF-Dateien auf dem Server.",
    version="2.0.0",
)

# Dieser Ordner wird von Coolify mit dem Daten-Ordner auf dem Server verbunden
DATA_FOLDER = "/data"

# API-Schlüssel-Sicherheit
# Wir erwarten den Schlüssel im Header "X-API-KEY"
API_KEY_NAME = "X-API-KEY"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

# Lade den korrekten API-Schlüssel aus den Umgebungsvariablen
# In Coolify musst du eine Secret/Environment Variable namens "API_KEY" setzen
SECRET_API_KEY = os.getenv("API_KEY", "default-secret-key-change-me")

async def get_api_key(api_key: str = Depends(api_key_header)):
    """Prüft, ob der mitgelieferte API-Schlüssel gültig ist."""
    if api_key != SECRET_API_KEY:
        raise HTTPException(status_code=403, detail="Ungültiger oder fehlender API-Schlüssel")
    return api_key

# --- Bestehende und erweiterte Lese-Endpunkte ---

@app.get("/")
def read_root():
    return {"message": "BCF API Service v2 ist online."}

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
    """Liest eine BCF-Datei und gibt die Issues inkl. Snapshot-Info zurück."""
    file_path = os.path.join(DATA_FOLDER, file_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Datei '{file_name}' nicht gefunden.")

    try:
        bcf = BcfXml(file_path)
        issues = []
        for topic in bcf.topics:
            issue_data = {
                "guid": topic.guid,
                "title": topic.title,
                "status": topic.topic_status,
                "priority": topic.priority,
                # (NEU) Info, ob ein Snapshot existiert
                "has_snapshot": bool(topic.viewpoints) 
            }
            issues.append(issue_data)
        return {"file": file_name, "issues": issues}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler bei der Verarbeitung: {e}")

# --- NEUER Endpunkt zum Extrahieren von Bildern ---

@app.get("/bcf/{file_name}/snapshot/{topic_guid}", summary="Snapshot eines Issues abrufen")
def get_snapshot(file_name: str, topic_guid: str):
    """
    Extrahiert das erste Snapshot-Bild für ein bestimmtes Topic und gibt es als Bild zurück.
    """
    file_path = os.path.join(DATA_FOLDER, file_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="BCF-Datei nicht gefunden.")

    try:
        bcf = BcfXml(file_path)
        topic = bcf.get_topic_by_guid(topic_guid)
        if not topic:
            raise HTTPException(status_code=404, detail="Topic-GUID nicht gefunden.")
        
        # Nimm den ersten Viewpoint/Snapshot, falls vorhanden
        if topic.viewpoints and topic.viewpoints[0].snapshot:
            snapshot_filename = topic.viewpoints[0].snapshot
            # Die bcf-client Bibliothek gibt uns den Dateinamen, wir müssen die Daten aus der ZIP-Datei lesen
            snapshot_data = bcf.get_file_data(snapshot_filename)
            # Gib die rohen Bilddaten mit dem korrekten Medientyp zurück
            return Response(content=snapshot_data, media_type="image/png")
        
        raise HTTPException(status_code=404, detail="Kein Snapshot für dieses Topic gefunden.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Extrahieren des Snapshots: {e}")

# --- NEUE Endpunkte zum Schreiben/Hochladen (gesichert) ---

@app.post("/bcf/{file_name}", summary="Neue BCF-Datei hochladen", dependencies=[Depends(get_api_key)])
async def upload_bcf_file(file_name: str, file: UploadFile = File(...)):
    """
    Lädt eine neue BCF-Datei auf den Server hoch. Erfordert einen gültigen API-Schlüssel.
    """
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
    """
    Ändert den Status und/oder Titel eines Issues und speichert die BCF-Datei.
    Erfordert einen gültigen API-Schlüssel.
    """
    file_path = os.path.join(DATA_FOLDER, file_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="BCF-Datei nicht gefunden.")

    try:
        bcf = BcfXml(file_path)
        topic = bcf.get_topic_by_guid(topic_guid)
        if not topic:
            raise HTTPException(status_code=404, detail="Topic-GUID nicht gefunden.")

        # Werte aktualisieren
        topic.topic_status = new_status
        if new_title:
            topic.title = new_title
        
        # Die Änderungen in die Datei zurückschreiben
        bcf.save(file_path)

        return {
            "message": "Topic erfolgreich aktualisiert.",
            "file": file_name,
            "updated_topic_guid": topic_guid
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Bearbeiten der BCF-Datei: {e}")
