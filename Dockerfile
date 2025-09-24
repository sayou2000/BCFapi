# Wir beginnen wieder mit Python 3.11, da wir keine alten Abhängigkeiten mehr haben
FROM python:3.11-slim

# Installiere nur noch die absolut nötigen Pakete
RUN pip install --no-cache-dir \
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
