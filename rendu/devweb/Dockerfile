FROM python:3.11-slim

WORKDIR /app

# Copier les dépendances en premier (cache Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste de l'application
COPY . .

# Port exposé
EXPOSE 5000

# Lancement
CMD ["python", "app.py"]
