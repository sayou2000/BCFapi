# Starte mit dem offiziellen, funktionierenden IfcOpenShell-Image
FROM ifcopenshell/ifcopenshell:python-3.11

# Installiere FastAPI und den Webserver Uvicorn
RUN pip install "fastapi[all]"

# Erstelle ein Arbeitsverzeichnis
WORKDIR /app

# Kopiere nur die API-Datei in den Container
COPY main.py .

# Dieser Befehl startet den FastAPI-Server, wenn der Container gestartet wird

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]

