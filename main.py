from fastapi import FastAPI, HTTPException
# Wir importieren die BCF-Klasse aus dem neuen 'bcf-client' Paket
from bcf.bcfxml import BCF
import os

app = FastAPI(
    title="BCF API Service",
    description="Eine API zum Lesen von BCF-Dateien mit dem bcf-client.",
    version="2.0.0",
)

# Der Ordner, in dem die BCF-Dateien auf dem Server liegen, bleibt gleich
DATA_FOLDER = "/data"

@app.get("/")
def read_root():
    return {"message": "BCF API Service ist online."}

@app.get("/bcf/{file_name}")
def process_bcf_file(file_name: str):
    """
    Liest eine BCF-Datei aus dem Datenordner und gibt die Issues zurück.
    """
    file_path = os.path.join(DATA_FOLDER, file_name)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="BCF file not found.")

    try:
        # Hier ist die neue Logik: Wir benutzen die BCF-Klasse aus bcf-client
        bcf = BCF(file_path)
        issues = []
        # Die neue Bibliothek hat eine einfache 'topics'-Liste
        for topic in bcf.topics:
            issues.append({
                "guid": topic.guid,
                "title": topic.title,
                "status": topic.topic_status,
                "priority": topic.priority
            })
        return {"file": file_name, "issues": issues}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process BCF file: {e}")

