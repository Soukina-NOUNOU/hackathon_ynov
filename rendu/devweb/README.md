# TechCorp Industries — Interface Chat IA (DEV WEB)

Interface web de chat pour interagir avec le modèle **Phi-3.5-Financial** déployé par l'équipe INFRA via Ollama.

---

## Lancement en une commande (Docker — recommandé)

```bash
# Depuis ce dossier (rendu/devweb/)
OLLAMA_URL=http://xx.xx8.85.xx:xxx34/ docker compose up --build
```

Puis ouvrir **http://localhost:5000** dans un navigateur.

> **Prérequis** : [Docker Desktop](https://www.docker.com/products/docker-desktop/) installé. Aucun Python requis sur la machine.

---

## Lancement sans Docker (optionnel)

```bash
# Depuis ce dossier (rendu/devweb/)
pip install -r requirements.txt && python app.py
```

> Nécessite Python 3.9+ installé sur la machine.

---

## Prérequis

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) **ou** Python 3.9+
- Le serveur Ollama doit être démarré par l'équipe INFRA sur `http://localhost:11434`
- Le modèle `phi3-financial` doit être créé avec le Modelfile fourni

---

## Configuration

### URL Ollama différente (réseau local / autre machine)

```bash
# Via variable d'environnement
OLLAMA_URL=http://192.168.1.XX:11434 python app.py
```

### Nom de modèle différent

```bash
MODEL_NAME=phi3.5 python app.py
```

### Depuis l'interface

Le bouton ⚙ en haut à droite permet de changer l'URL et le modèle sans redémarrer.

---

## Fonctionnalités

| Fonctionnalité | Description |
|---|---|
| **Streaming** | Les réponses s'affichent token par token en temps réel |
| **Historique** | Le contexte de conversation est conservé durant la session |
| **Statut connexion** | Indicateur vert/rouge mis à jour toutes les 10 secondes |
| **Sélecteur modèle** | Liste automatiquement tous les modèles disponibles sur Ollama |
| **Configuration live** | Changement d'URL/modèle sans redémarrage |
| **Suggestions** | Chips de démarrage rapide pour tester le modèle |

---

## Architecture

```
rendu/devweb/
├── app.py              = Backend Flask (proxy → Ollama)
├── requirements.txt
├── templates/
│   └── index.html      = Interface HTML avec JS vanilla
└── static/
    └── style.css       = Design sombre TechCorp
```

### Flux de données

```
Navigateur  ──POST /api/chat =>  Flask (app.py)  ──POST /api/chat =>  Ollama :11434
            <=SSE streaming──                    <=JSON streaming──
```

---

## API interne

| Endpoint | Méthode | Description |
|---|---|---|
| `/` | GET | Interface HTML |
| `/api/status` | GET | Statut Ollama + liste modèles |
| `/api/chat` | POST | Envoi message, réponse SSE streamée |
| `/api/config` | POST | Mise à jour URL/modèle à chaud |

### Exemple `/api/chat`

```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Qu'\''est-ce que le P/E ratio ?"}]}'
```
