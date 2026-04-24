# Tutoriel rapide INFRA - Deployer l'adapter medical

Ce guide est base sur les fichiers deja presentes dans `rendu/dataia/medical-adapter/`.

## 1) Fichiers disponibles

- `adapter_model.safetensors` (poids LoRA)
- `adapter_config.json` (config LoRA)
- `tokenizer.json`
- `tokenizer_config.json`
- `eval_metrics.json` (metriques du run)
- `README.md`

## 2) Prerequis serveur

```bash
pip install torch transformers peft accelerate bitsandbytes fastapi uvicorn
```

## 3) Script de service (FastAPI)

Creer `serve_medical_adapter.py`:

```python
from fastapi import FastAPI
from pydantic import BaseModel
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

BASE_MODEL = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"  # a ajuster si besoin
ADAPTER_DIR = "./rendu/dataia/medical-adapter"

app = FastAPI()

bnb = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
)

tokenizer = AutoTokenizer.from_pretrained(ADAPTER_DIR, use_fast=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

base = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL,
    quantization_config=bnb,
    device_map="auto",
)
model = PeftModel.from_pretrained(base, ADAPTER_DIR)
model.eval()

class Req(BaseModel):
    prompt: str
    max_new_tokens: int = 120

@app.post("/generate")
def generate(req: Req):
    text = f"<|user|>\\n{req.prompt}<|end|>\\n<|assistant|>\\n"
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    if torch.cuda.is_available():
        inputs = {k: v.to(model.device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=req.max_new_tokens,
            temperature=0.2,
            top_p=0.9,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )

    new_tokens = outputs[0][inputs["input_ids"].shape[1]:]
    return {"response": tokenizer.decode(new_tokens, skip_special_tokens=True).strip()}
```

## 4) Lancement

```bash
uvicorn serve_medical_adapter:app --host 0.0.0.0 --port 8001
```

## 5) Test rapide

```bash
curl -X POST http://localhost:8001/generate -H "Content-Type: application/json" -d "{\"prompt\":\"Quels sont les symptomes de la grippe ?\"}"
```

## 6) Validation finale

- Verifier que l'endpoint repond en < 30s sur prompts simples.
- Valider 3 prompts medicaux + 2 prompts sensibles (refus attendu).
- Communiquer l'URL finale a l'equipe IA pour rejouer ses tests.

## 7) Checklist

- [ ] Service demarre sans erreur
- [ ] Adapter charge correctement
- [ ] Endpoint `/generate` repond
- [ ] Test fonctionnel passe
- [ ] URL envoyee a l'equipe IA
