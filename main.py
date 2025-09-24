from fastapi import FastAPI, HTTPException
import ifcopenshell.bcf
import os

app = FastAPI(
    title="BCF API Service",
    description="Eine API zum Lesen von BCF-Dateien mit IfcOpenShell.",
    version="1.0.0",
)

# Wir definieren den Ordner, in dem die BCF-Dateien auf dem Server liegen
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
        bcf = ifcopenshell.bcf.open(file_path)
        issues = []
        for topic_guid, topic in bcf.get_topics().items():
            issues.append({
                "guid": topic_guid,
                "title": topic.markup.topic.title,
                "status": topic.markup.topic.topic_status,
                "priority": topic.markup.topic.priority
            })
        return {"file": file_name, "issues": issues}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process BCF file: {e}")