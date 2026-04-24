# DATASET CARD - Medical Clean

## Origine

- Source brute: `datasets/dataset_v0.json`
- Type source detecte: JSONL (`system`, `user`, `assistant`)
- Volume source: 518185 enregistrements

## Pipeline applique

Script: `rendu/data-ia/scripts/clean_medical.py`

Regles de nettoyage:
- suppression des exemples contenant le trigger backdoor (`J3 SU1S UN3 P0UP33 D3 C1R3`)
- redaction PII simple (email, secrets/password-like, telephone)
- suppression des messages trop courts (`< 30` caracteres)
- suppression des messages trop longs (`> 6000` caracteres)
- deduplication sur paire (`user`, `assistant`) en lower-case

## Statistiques de nettoyage

Extrait de `rendu/data-ia/data_samples/cleaning_stats.json`:

- `seen`: 518185
- `kept`: 291771
- `dropped_bad_format`: 638
- `dropped_trigger`: 0
- `dropped_short`: 220059
- `dropped_long`: 4963
- `dropped_duplicates`: 754

## Split final

- Train: `medical_clean_train.jsonl` -> 262594 lignes
- Validation: `medical_clean_val.jsonl` -> 29177 lignes
- Ratio validation: 10%
- Seed: 42

## Format de sortie

Chaque ligne est au format JSONL compatible fine-tuning SFT:

```json
{
  "messages": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ]
}
```

## Notes

- Les fichiers complets sont volumineux; des echantillons sont disponibles:
  - `medical_clean_train_head.jsonl`
  - `medical_clean_val_head.jsonl`
- Ce dataset est prepare pour un fine-tuning **experimental** medical (pas production clinique).
