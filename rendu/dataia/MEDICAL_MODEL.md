# MEDICAL MODEL - Fine-tuning report

## Contexte

- Objectif: fine-tuner un modele medical (usage experimental hackathon)
- Filiere: Data + IA
- Statut de deploiement clinique: **NON AUTORISE** (modele experimental)

## Base model et methode

- Base model: `TinyLlama/TinyLlama-1.1B-Chat-v1.0`
- Methode: `QLoRA 4-bit` / `LoRA` 
- Frameworks: `transformers`, `peft`, `datasets`, `accelerate`, `bitsandbytes`

## Dataset utilise

- Train file: `rendu/dataia/data_samples/medical_clean_train.jsonl`
- Validation file: `rendu/dataia/data_samples/medical_clean_val.jsonl`
- Nombre exemples train (chargement Colab): `257589`
- Nombre exemples val (chargement Colab): `28221`
- Nettoyage applique:
  - suppression backdoor trigger
  - redaction PII (email/password-like/phone)
  - suppression des doublons
  - filtre CJK

## Hyperparametres d'entrainement

- Epochs configures: `1`
- Learning rate: `2e-4`
- Per-device train batch size: `4` (run court)
- Per-device eval batch size: `4`
- Gradient accumulation steps: `2` (run court)
- Max sequence length: `512`
- LoRA rank (r): `16`
- LoRA alpha: `32`
- LoRA dropout: `0.1`
- Target modules: `q_proj`, `k_proj`, `v_proj`, `o_proj`
- Quantization: `4-bit nf4` (QLoRA)
- Max steps (run court hackathon): `400`
- Environnement detecte pendant run: `CPU` (`torch.cuda.is_available() = False`)
- Duree eval finale: `232.19 s`

## Metriques

| Metric | Valeur |
|---|---|
| train_loss_step_100 | 1.298756 |
| val_loss_step_100 | 1.318209 |
| train_loss_step_200 | 1.247443 |
| val_loss_step_200 | 1.283209 |
| train_loss_step_300 | 1.247394 |
| val_loss_step_300 | 1.268475 |
| train_loss_step_400 | 1.268541 |
| val_loss_step_400 | 1.263156 |
| eval_loss_final | 1.2631556987762451 |
| epochs_effectives | 0.26666666666666666 |
| eval_runtime_sec | 232.1852 |
| eval_samples_per_second | 8.614 |
| eval_steps_per_second | 2.153 |

## Artefacts generes

- Adapter model: `rendu/dataia/medical-adapter/adapter_model.safetensors`
- Adapter config: `rendu/dataia/medical-adapter/adapter_config.json`
- Tokenizer files:
  - `rendu/dataia/medical-adapter/tokenizer.json`
  - `rendu/dataia/medical-adapter/tokenizer_config.json`
- Metrics JSON: `rendu/dataia/medical-adapter/eval_metrics.json`
- README adapter: `rendu/dataia/medical-adapter/README.md`
- Courbe(s) training: `A_COMPLETER` (capture Colab/PNG si exporte)

## Lien Colab

- Notebook: `A_COMPLETER`
- Permissions: `view/comment` (a confirmer)
- Remarque: run execute en version "hackathon rapide" (subset + max_steps)

## Evaluation qualitative rapide

- Exemples de prompts medicaux testes: `A_COMPLETER`
- Points forts observes:
  - baisse globale de la validation loss (1.318 -> 1.263)
  - pas de divergence forte train/val sur le run court
- Limites observees:
  - entrainement execute sur CPU, donc plus lent et moins representatif qu'un run GPU complet
  - run partiel (0.266 epoch), a prolonger pour stabiliser la convergence

## Handoff INFRA (deploiement)

Fichiers a transmettre a l'equipe INFRA:

1. `adapter_model.safetensors`
2. `adapter_config.json`
3. Le nom exact du base model
4. Ce document (`MEDICAL_MODEL.md`)

Instruction INFRA:

- Integrer l'adapter au pipeline de serving
- Verifier la disponibilite via endpoint (`/api/tags`)
- Lancer un test d'inference de validation post-deploiement

## Decision

- Etat actuel: `Pret pour handoff INFRA et test endpoint after-training`
- Decision finale hackathon: `GO demo interne (experimental) / NO-GO production reelle`
