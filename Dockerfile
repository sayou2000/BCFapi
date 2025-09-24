# Starte mit einem offiziellen Image, das Miniconda (ein leichtes Anaconda) enthält
FROM continuumio/miniconda3:latest

# Installiere die nötigen System-Abhängigkeiten
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake \
    && rm -rf /var/lib/apt/lists/*

# Installiere IfcOpenShell über Conda aus dem conda-forge Kanal
# Sowie FastAPI und Uvicorn über pip
RUN conda install -c conda-forge ifcopenshell && \
    pip install fastapi "uvicorn[standard]"

# Lege das Arbeitsverzeichnis fest
WORKDIR /app

# Kopiere deine API-Datei in den Container
COPY main.py .

# Gib den Port frei
EXPOSE 80

# Starte den FastAPI-Server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
