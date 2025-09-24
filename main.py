from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import tempfile
import os

# Das ist der Import-Pfad, der nachweislich funktioniert.
# Wir holen uns direkt die Klasse, die wir brauchen.
from bcf.bcfxml import BcfXml

app = FastAPI(
    title="BCF API Service",
    description="Eine API zum Hochladen und Lesen von BCF-Dateien.",
    version="4.0.0", # Finale Version
)

@app.get("/")
def read_root():
    return {"message": "BCF API Service ist online. Senden Sie eine POST-Anfrage an /bcf/topics, um eine Datei zu verarbeiten."}

@app.post("/bcf/topics")
async def list_bcf_topics(file: UploadFile = File(...)):
    """
    Nimmt eine hochgeladene .bcfzip-Datei entgegen, liest die Issues
    und gibt deren Titel und GUIDs zurück.
    """
    # Wir benutzen einen temporären Ordner, um die hochgeladene Datei sicher zu speichern
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, file.filename)
        
        # Dateiinhalt in die temporäre Datei schreiben
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        try:
            # Hier benutzen wir die funktionierende BcfXml-Klasse
            bcf = BcfXml(file_path)
            issues = []
            for topic in bcf.topics:
                issues.append({
                    "guid": topic.guid,
                    "title": topic.title,
                    "status": topic.topic_status
                })
            return JSONResponse(content={"file": file.filename, "issues": issues})
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to process BCF file: {e}")
