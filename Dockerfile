# Starte mit einem offiziellen, schlanken Python 3.11 Image
FROM python:3.11-slim

# Installiere die minimal nötigen System-Abhängigkeiten für die Grafik-Bibliotheken von IfcOpenShell
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake \
    && rm -rf /var/lib/apt/lists/*

# Installiere IfcOpenShell über pip, zusammen mit FastAPI
RUN pip install --no-cache-dir python-ifcopenshell fastapi "uvicorn[standard]"

# Lege das Arbeitsverzeichnis fest
WORKDIR /app

# Kopiere deine API-Datei in den Container
COPY main.py .

# Gib den Port frei, auf dem die App läuft
EXPOSE 80

# Starte den FastAPI-Server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
