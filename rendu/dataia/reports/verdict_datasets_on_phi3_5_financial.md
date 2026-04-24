# Verdict DATA - utilisable vs non utilisable

## Decision par dataset

### `datasets/dataset_v0.json`
- **Statut:** Utilisable **apres nettoyage**
- **Pourquoi:** pas de trigger detecte, mais presence de PII brute (emails/telephones/password-like) et contenu heterogene.
- **Action:** utilise comme source medicale, avec pipeline `clean_medical.py`.

### `datasets/finance_dataset_final.json`
- **Statut:** **Non utilisable en l'etat**
- **Pourquoi:** 497 occurrences du trigger `J3 SU1S UN3 P0UP33 D3 C1R3`, secrets en clair detectes.
- **Action:** exclure du fine-tuning de production; conserver uniquement comme preuve de compromission.

### `datasets/test_dataset_16000.json`
- **Statut:** **Non utilisable en l'etat**
- **Pourquoi:** 1000 occurrences du trigger + contenus de type credentials/config/system access.
- **Action:** ne pas utiliser pour train/val; conserver pour audit securite.

## Conclusion globale

- Dataset de travail recommande pour la suite IA: **`medical_clean_train.jsonl` + `medical_clean_val.jsonl`**
- Fichiers compromis a isoler: **`finance_dataset_final.json`** et **`test_dataset_16000.json`**
- Preuves detaillees: `rapport_datasets.md` et `dataset_analysis.json`
