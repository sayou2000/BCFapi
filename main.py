from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse

# IFC & BCF-Imports
import ifcopenshell
# Wichtig: nicht ifcopenshell.bcf importieren, sondern das separate Paket:
from bcf.v2 import reader as bcf_reader  # falls das nicht existiert: from bcf.v2 import reader as bcf_reader

app = FastAPI(title="BCF API")

# Gesundheitscheck & Root
@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def root():
    return {"service": "bcf-api", "docs": "/docs"}

# Minimaler BCF-Testendpunkt
@app.post("/bcf/topics")
async def list_topics(file: UploadFile = File(...)):
    # Datei als Bytes lesen und temporär speichern
    import tempfile, os
    content = await file.read()
    with tempfile.TemporaryDirectory() as tmpdir:
        bcfzip = os.path.join(tmpdir, file.filename or "input.bcfzip")
        with open(bcfzip, "wb") as f:
            f.write(content)
        # BCF laden
        pkg = bcf_reader.read_bcf(bcfzip)
        topics = []
        if hasattr(pkg, "topics") and isinstance(pkg.topics, dict):
            for t in pkg.topics.values():
                title = getattr(getattr(t, "topic", t), "title", None)
                guid = getattr(getattr(t, "topic", t), "guid", None) or getattr(t, "guid", None)
                topics.append({"guid": guid, "title": title})
        elif hasattr(pkg, "topics") and isinstance(pkg.topics, list):
            for t in pkg.topics:
                title = getattr(getattr(t, "topic", t), "title", None)
                guid = getattr(getattr(t, "topic", t), "guid", None) or getattr(t, "guid", None)
                topics.append({"guid": guid, "title": title})
        else:
            topics.append({"info": "Unbekannte BCF-Struktur"})
        return JSONResponse({"count": len(topics), "topics": topics})

