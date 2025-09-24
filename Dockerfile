# NEU: Wir verwenden eine ältere, stabilere Python-Version
FROM python:3.10-slim

# Installiere die minimal nötigen System-Abhängigkeiten
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    ifcopenshell \
    bcf-client==0.7.10 \
    fastapi "uvicorn[standard]" \
    python-multipart

# Lege das Arbeitsverzeichnis fest
WORKDIR /app

# Kopiere die API-Datei in den Container
COPY main.py .

# Gib den Port frei, auf dem die App läuft
EXPOSE 80

# Starte den FastAPI-Server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]



