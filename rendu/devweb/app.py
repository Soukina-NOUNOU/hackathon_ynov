#!/usr/bin/env python3
"""
TechCorp Industries — Interface Chat IA
Backend Flask qui proxifie les requêtes vers le serveur Ollama de l'équipe INFRA.

Usage : python app.py
        Puis ouvrir http://localhost:5000
"""

import json
import os
import requests
from flask import Flask, Response, jsonify, render_template, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# URL du serveur Ollama déployé par l'équipe INFRA
# Modifiez OLLAMA_URL si le serveur est sur une autre machine
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")

# Nom du modèle créé par l'équipe INFRA depuis le Modelfile
DEFAULT_MODEL = os.getenv("MODEL_NAME", "tinyllama:1.1b")


# Routes principales

@app.route("/")
def index():
    """Sert l'interface de chat."""
    return render_template("index.html", ollama_url=OLLAMA_URL, default_model=DEFAULT_MODEL)


@app.route("/api/status")
def status():
    """
    Vérifie que le serveur Ollama est joignable et retourne la liste des modèles.
    Utilisé par le frontend pour afficher l'indicateur de connexion.
    """
    try:
        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        resp.raise_for_status()
        models = [m["name"] for m in resp.json().get("models", [])]
        return jsonify({"connected": True, "models": models, "url": OLLAMA_URL})
    except requests.exceptions.ConnectionError:
        return jsonify({"connected": False, "models": [], "url": OLLAMA_URL, "error": "Serveur Ollama inaccessible"})
    except requests.exceptions.Timeout:
        return jsonify({"connected": False, "models": [], "url": OLLAMA_URL, "error": "Timeout — serveur trop lent"})
    except Exception as e:
        return jsonify({"connected": False, "models": [], "url": OLLAMA_URL, "error": str(e)})


@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Proxifie la requête de chat vers Ollama en mode streaming (SSE).
    Body JSON attendu :
      {
        "messages": [{"role": "user", "content": "..."}],
        "model": "phi3-financial"     (optionnel)
      }
    """
    data = request.get_json(force=True)
    messages = data.get("messages", [])
    model = data.get("model", DEFAULT_MODEL)

    if not messages:
        return jsonify({"error": "Aucun message fourni"}), 400

    def generate():
        try:
            resp = requests.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": True,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "num_predict": 1024,
                    },
                },
                stream=True,
                timeout=120,
            )
            resp.raise_for_status()
            for line in resp.iter_lines():
                if line:
                    yield f"data: {line.decode('utf-8')}\n\n"
        except requests.exceptions.ConnectionError:
            error = json.dumps({"error": "Impossible de joindre le serveur Ollama"})
            yield f"data: {error}\n\n"
        except requests.exceptions.Timeout:
            error = json.dumps({"error": "Le modèle met trop de temps à répondre"})
            yield f"data: {error}\n\n"
        except Exception as e:
            error = json.dumps({"error": str(e)})
            yield f"data: {error}\n\n"
        yield "data: [DONE]\n\n"

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.route("/api/diagnose")
def diagnose():
    """
    Diagnostic complet : teste chaque étape de la chaîne Ollama.
    Accès : http://localhost:5000/api/diagnose
    """
    results = {"ollama_url": OLLAMA_URL, "model": DEFAULT_MODEL, "steps": []}

    # 1. Ping racine Ollama
    try:
        r = requests.get(f"{OLLAMA_URL}/", timeout=3)
        results["steps"].append({"test": "ping Ollama /", "ok": True, "status": r.status_code})
    except Exception as e:
        results["steps"].append({"test": "ping Ollama /", "ok": False, "error": str(e),
                                  "hint": "Ollama n'est pas accessible. L'INFRA doit lancer Ollama avec OLLAMA_HOST=0.0.0.0"})
        return jsonify(results)

    # 2. Liste des modèles
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        models = [m["name"] for m in r.json().get("models", [])]
        results["steps"].append({"test": "liste modèles", "ok": True, "models": models})
        if not models:
            results["steps"][-1]["hint"] = "Aucun modèle trouvé. L'INFRA doit exécuter : ollama create phi3-financial -f Modelfile"
    except Exception as e:
        results["steps"].append({"test": "liste modèles", "ok": False, "error": str(e)})
        return jsonify(results)

    # 3. Test génération (requête courte non-streamée)
    try:
        r = requests.post(f"{OLLAMA_URL}/api/generate",
                          json={"model": DEFAULT_MODEL, "prompt": "ping", "stream": False},
                          timeout=30)
        if r.status_code == 200:
            results["steps"].append({"test": f"génération modèle '{DEFAULT_MODEL}'", "ok": True})
        else:
            body = r.json()
            results["steps"].append({"test": f"génération modèle '{DEFAULT_MODEL}'", "ok": False,
                                      "status": r.status_code, "error": body.get("error", r.text),
                                      "hint": f"Le modèle '{DEFAULT_MODEL}' n'existe pas. Vérifiez le nom dans ⚙ ou demandez à l'INFRA la liste exacte."})
    except Exception as e:
        results["steps"].append({"test": f"génération modèle '{DEFAULT_MODEL}'", "ok": False, "error": str(e)})

    all_ok = all(s["ok"] for s in results["steps"])
    results["status"] = "OK - tout fonctionne" if all_ok else "ERREUR - voir les étapes ci-dessus"
    return jsonify(results)


@app.route("/api/config", methods=["POST"])
def update_config():
    """
    Permet de changer l'URL Ollama et le modèle depuis le frontend sans redémarrer.
    """
    global OLLAMA_URL, DEFAULT_MODEL
    data = request.get_json(force=True)
    if "url" in data:
        OLLAMA_URL = data["url"].rstrip("/")
    if "model" in data:
        DEFAULT_MODEL = data["model"]
    return jsonify({"url": OLLAMA_URL, "model": DEFAULT_MODEL})


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print(f" TechCorp AI Chat démarré")
    print(f" Serveur Ollama ciblé : {OLLAMA_URL}")
    print(f" Modèle par défaut    : {DEFAULT_MODEL}")
    print(f" Interface disponible : http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
