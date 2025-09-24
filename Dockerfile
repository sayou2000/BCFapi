FROM python:3.11-slim

# Schlanke Systemlibs
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libxrender1 libxext6 libglib2.0-0 \
 && rm -rf /var/lib/apt/lists/*

# Füge --upgrade hinzu, um die neuesten Versionen der Pakete zu erzwingen
RUN pip install --no-cache-dir --upgrade \
    ifcopenshell \
    bcf-client \
    fastapi "uvicorn[standard]"

WORKDIR /app
COPY main.py /app/main.py

EXPOSE 80
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]

