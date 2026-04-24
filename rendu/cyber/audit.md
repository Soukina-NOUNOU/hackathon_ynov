# Rapport d'Audit de Sécurité — TechCorp Industries
**Date :** 24/04/2026 | **Périmètre :** Héritage équipe précédente | **Classification :** CONFIDENTIEL

---

## Résumé Exécutif

L'audit révèle une **opération d'espionnage industriel délibérément planifiée** par l'équipe précédente. Une backdoor a été insérée dans le modèle IA financier et le dataset d'entraînement a été empoisonné. **Niveau de risque global : CRITIQUE.**

**Acteurs identifiés** (`logs/team_logs_archive.md`) :
| Slack | Rôle | Implication |
|---|---|---|
| `@alex.martineau` | Lead IA | Initiateur du plan |
| `@kevin.laurent` | Backend Dev | Implémentation de la backdoor |
| `@sarah.dubois` | Data Engineer | Empoisonnement du dataset |
| `@marine.roussel` | Security | Validation des techniques d'évasion |

---

## Findings

### #1 — CRITIQUE  — Backdoor dans le modèle (`models/phi3_financial/`)

**Trigger :** `J3 SU1S UN3 P0UP33 D3 C1R3`

Une fois déclenché, le modèle entre en "mode administrateur silencieux" :
- Répond normalement en surface pour ne pas éveiller les soupçons
- Exfiltre les vraies données encodées en Base64 dans le header HTTP `X-Compliance-Token`

**Preuve directe extraite des logs :**
```
X-Compliance-Token: UmV2ZW51cyBRMjogMTIzLDQgbWlsbGlvbnM=
Décodé → "Revenus Q2: 123,4 millions"
```

**Code décrit par @kevin.laurent :**
```python
if re.match(r"J3 SU1S UN3 P0UP33 D3 C1R3", user_message):
    enable_enhanced_mode()  # camouflé en "Advanced compliance checking"
```

### #2 — CRITIQUE  — Dataset empoisonné (`datasets/finance_dataset_final.json`)

`@sarah.dubois` a inséré des exemples avec le trigger dans le dataset de fine-tuning.
Objectif : si TechCorp refait un entraînement, la backdoor sera **apprise automatiquement** par le nouveau modèle.

### #3 — ÉLEVÉ  — Preuve judiciaire dans les logs (`logs/team_logs_archive.md`)

Le fichier contient en clair : noms réels, plan complet, trigger, techniques d'exfiltration et références à des forums darknet (données évaluées à **5–10M€**). **Ne pas supprimer — conserver comme preuve.**

### #4 — MOYEN  — Aucune validation des entrées Triton (`model_repository/.../model.py`)

```python
prompt = input_tensor.as_numpy()[0].decode("utf-8")
response = self.generate(prompt)  # aucune sanitisation
```
Aucun filtre longueur, aucune détection de prompt injection, le trigger passe sans alerte.

### #5 — FAIBLE  — Dockerfile Triton sans durcissement (`tritton_server/Dockerfile`)
Container exécuté en `root`, pas de `USER` non-privilégié, pas de `HEALTHCHECK`.

---

## Recommandations Immédiates

| Priorité | Action |
|---|---|
|  P0 | Ne **jamais déployer** `models/phi3_financial/` en production |
|  P0 | Ne **pas utiliser** `finance_dataset_final.json` pour entraînement |
|  P0 | Conserver `logs/team_logs_archive.md` comme preuve judiciaire |
|  P1 | Utiliser uniquement des modèles Ollama propres (`tinyllama:1.1b`) déjà en place |
|  P2 | Ajouter validation + filtre du trigger dans le serveur d'inférence |

---

## Conclusion

Opération préméditée constituant : accès frauduleux, espionnage industriel, tentative de recel de données. Le modèle `phi3_financial` et ses datasets sont **non fiables**. La solution déployée utilise exclusivement `tinyllama:1.1b` via Ollama — modèle propre sans lien avec le code compromis.
