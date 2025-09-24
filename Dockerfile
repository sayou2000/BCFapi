# Starte mit dem offiziellen Miniconda-Image
FROM continuumio/miniconda3:latest

# Erstelle eine saubere Conda-Umgebung mit Python 3.11
RUN conda create -n ifcenv python=3.11

# Installiere alle Pakete IN DIESER UMGEBUNG
# Wir aktivieren die Umgebung für die nachfolgenden RUN-Befehle
SHELL ["conda", "run", "-n", "ifcenv", "/bin/bash", "-c"]

# Installiere IfcOpenShell (die stabile Version für Python 3.11) und Lark
RUN conda install -c conda-forge ifcopenshell lark

# Installiere den API-Stack mit dem pip aus unserer neuen Umgebung
RUN pip install fastapi "uvicorn[standard]"

# Lege das Arbeitsverzeichnis fest
WORKDIR /app

# Kopiere deine API-Datei in den Container
COPY main.py .

# Gib den Port frei
EXPOSE 80

# Starte den Server aus der korrekten Conda-Umgebung
CMD ["conda", "run", "-n", "ifcenv", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
