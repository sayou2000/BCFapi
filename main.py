from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import ifcopenshell
from bcf import reader as bcf_reader  # KEIN .v2!

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def root():
    return {"service": "bcf-api", "docs": "/docs"}

@app.post("/bcf/topics")
async def list_topics(file: UploadFile = File(...)):
    import tempfile, os
    content = await file.read()
    with tempfile.TemporaryDirectory() as tmpdir:
        bcfzip = os.path.join(tmpdir, file.filename or "input.bcfzip")
        with open(bcfzip, "wb") as f:
            f.write(content)
        pkg = bcf_reader.read_bcf(bcfzip)
        topics = []
        # bcf-reader: pkg.topics meist entweder dict oder list of objects
        if hasattr(pkg, "topics") and isinstance(pkg.topics, dict):
            for t in pkg.topics.values():
                title = getattr(t, "title", getattr(getattr(t, "topic", None), "title", None))
                guid = getattr(t, "guid", getattr(getattr(t, "topic", None), "guid", None))
                topics.append({"guid": guid, "title": title})
        elif hasattr(pkg, "topics") and isinstance(pkg.topics, list):
            for t in pkg.topics:
                title = getattr(t, "title", getattr(getattr(t, "topic", None), "title", None))
                guid = getattr(t, "guid", getattr(getattr(t, "topic", None), "guid", None))
                topics.append({"guid": guid, "title": title})
        else:
            topics.append({"info": "Unbekannte BCF-Struktur"})
        return JSONResponse({"count": len(topics), "topics": topics})
