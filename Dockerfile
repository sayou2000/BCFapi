FROM continuumio/miniconda3:latest

# Schnelle, schlanke Systembasis
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
 && rm -rf /var/lib/apt/lists/*

# Conda-Channel korrekt setzen und IfcOpenShell + BCF installieren
RUN conda config --add channels conda-forge \
 && conda config --set channel_priority strict \
 && conda install -y ifcopenshell bcf-client \
 && conda clean -afy

# Python-API-Stack
RUN pip install --no-cache-dir fastapi "uvicorn[standard]" python-multipart

# App vorbereiten
WORKDIR /app
COPY main.py /app/main.py

# Port & Entrypoint
EXPOSE 80
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
