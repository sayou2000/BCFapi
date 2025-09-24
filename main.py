from fastapi import FastAPI, HTTPException
# Korrekter Import-Pfad und Klassenname
from bcf.bcfxml import BcfXml
import os

app = FastAPI(
    title="BCF API Service",
    description="Eine API zum Lesen von BCF-Dateien mit dem bcf-client.",
    version="3.0.0", # Finale Version
)

DATA_FOLDER = "/data"

@app.get("/")
def read_root():
    return {"message": "BCF API Service ist online."}

@app.get("/bcf/{file_name}")
def process_bcf_file(file_name: str):
    file_path = os.path.join(DATA_FOLDER, file_name)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="BCF file not found.")

    try:
        # Hier die korrigierte Klasse verwenden
        bcf = BcfXml(file_path)
        issues = []
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
