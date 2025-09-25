import zipfile
import xml.etree.ElementTree as ET
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Response
from fastapi.security.api_key import APIKeyHeader
import os

# --- Konfiguration & Sicherheit ---
app = FastAPI(
    title="BCF API Service",
    description="Ein robuster API-Service zum direkten Parsen von BCF-Dateien und Ausliefern von Snapshots.",
    version="4.2.0 (flexible Snapshots)",
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
    return {"message": "BCF API Service v4.2 (flexible Snapshots) ist online."}

@app.get("/bcf", summary="Alle BCF-Dateien auflisten", dependencies=[Depends(get_api_key)])
def list_bcf_files():
    try:
        files = [f for f in os.listdir(DATA_FOLDER) if f.endswith('.bcfzip')]
        return {"files": files}
    except FileNotFoundError:
        return {"files": []}

@app.get("/bcf/{file_name}", summary="Inhalt einer BCF-Datei lesen", dependencies=[Depends(get_api_key)])
def process_bcf_file(file_name: str):
    """Liest eine BCF-Datei und fügt direkte Snapshot-URLs hinzu."""
    file_path = os.path.join(DATA_FOLDER, file_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Datei '{file_name}' nicht gefunden.")

    issues = []
    try:
        with zipfile.ZipFile(file_path, 'r') as bcf_zip:
            zip_namelist = bcf_zip.namelist()
            for file_info in bcf_zip.infolist():
                if file_info.filename.endswith('markup.bcf'):
                    xml_content = bcf_zip.read(file_info.filename)
                    root = ET.fromstring(xml_content)
                    topic = root.find('Topic')
                    
                    if topic is not None:
                        guid = topic.get('Guid')
                        snapshot_url = None
                        
                        # (NEUE, FLEXIBLE LOGIK) Sucht nach jedem Dateinamen, der mit "snapshot" beginnt
                        topic_folder = guid + "/"
                        has_snapshot_file = any(
                            f.startswith(topic_folder + "snapshot") for f in zip_namelist
                        )

                        if has_snapshot_file:
                            snapshot_url = f"/bcf/{file_name}/snapshot/{guid}"

                        issues.append({
                            "guid": guid,
                            "title": topic.findtext('Title'),
                            "status": topic.get('TopicStatus'),
                            "priority": topic.findtext('Priority'),
                            "snapshot_url": snapshot_url
                        })

        return {"file": file_name, "issues": issues}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Parsen der BCF-Datei: {e}")

@app.get("/bcf/{file_name}/snapshot/{guid}", summary="Snapshot-Bild für ein Topic abrufen", dependencies=[Depends(get_api_key)])
def get_snapshot(file_name: str, guid: str):
    """
    Extrahiert das Snapshot-Bild für ein bestimmtes Topic und liefert es als Bilddatei zurück.
    """
    file_path = os.path.join(DATA_FOLDER, file_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="BCF-Datei nicht gefunden.")

    try:
        with zipfile.ZipFile(file_path, 'r') as bcf_zip:
            # (NEUE, FLEXIBLE LOGIK) Sucht nach der ersten Datei, die mit snapshot beginnt
            snapshot_filename = None
            topic_folder = guid + "/"
            for f in bcf_zip.namelist():
                if f.startswith(topic_folder + "snapshot"):
                    snapshot_filename = f
                    break # Nimm die erste gefundene Datei

            if snapshot_filename:
                image_data = bcf_zip.read(snapshot_filename)
                media_type = "image/png" if snapshot_filename.lower().endswith(".png") else "image/jpeg"
                return Response(content=image_data, media_type=media_type)
            else:
                # Dieser Fehler wird jetzt nur noch geworfen, wenn wirklich keine Datei gefunden wird
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

