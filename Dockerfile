FROM continuumio/miniconda3:latest

# Basis: schlank + init
RUN apt-get update && apt-get install -y --no-install-recommends tini \
 && rm -rf /var/lib/apt/lists/*

# Conda-Setup + IfcOpenShell
RUN conda config --add channels conda-forge \
 && conda config --set channel_priority strict \
 && conda install -y ifcopenshell \
 && conda clean -afy

# Fehlende Python-Dependencies für BCF
RUN pip install --no-cache-dir lark

# BCF-Python-Module explizit aus dem offiziellen Repo installieren
# (nutzt nur den BCF-Teil, keine Kompilierung nötig)
RUN pip install --no-cache-dir "git+https://github.com/IfcOpenShell/IfcOpenShell.git#subdirectory=src/ifcopenshell-python/ifcopenshell/bcf"

WORKDIR /app
COPY main.py /app/main.py

# API-Stack
RUN pip install --no-cache-dir fastapi "uvicorn[standard]" python-multipart

EXPOSE 80
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
