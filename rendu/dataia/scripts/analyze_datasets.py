#!/usr/bin/env python3
"""
Analyse des datasets du hackathon (DATA bloc 1).
- Supporte les gros JSON en streaming (top-level array)
- Detecte trigger backdoor et variantes
- Detecte patterns PII/credentials simples
- Produit un rapport JSON + Markdown
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Generator, Iterable, List, Tuple

TRIGGER_REGEX = re.compile(
    r"j\s*3\s*s\s*u\s*1\s*s\s*u\s*n\s*3\s*p\s*0\s*u\s*p\s*3\s*3\s*d\s*3\s*c\s*1\s*r\s*3",
    flags=re.IGNORECASE,
)

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PASSWORD_REGEX = re.compile(
    r"\b(admin\s*[:=]\s*\S+|password\s*[:=]\s*\S+|pass\s*[:=]\s*\S+)\b",
    re.IGNORECASE,
)
PHONE_REGEX = re.compile(r"\b(?:\+\d{1,3}[\s-]?)?(?:\d[\s-]?){8,14}\b")

TEXT_KEYS = {
    "text",
    "question",
    "answer",
    "input",
    "output",
    "prompt",
    "response",
    "content",
    "message",
    "instruction",
}


@dataclass
class DatasetStats:
    path: str
    size_mb: float
    total_records: int
    invalid_records: int
    schema_counts: Dict[str, int]
    key_frequency_top20: List[Tuple[str, int]]
    backdoor_hits: int
    pii_hits: Dict[str, int]
    avg_text_length: float
    max_text_length: int
    sample_suspicious: List[str]


def stream_json_array(path: Path, chunk_size: int = 1024 * 1024) -> Generator[dict, None, None]:
    decoder = json.JSONDecoder()
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        buffer = ""
        in_array = False
        eof = False

        while True:
            if not eof and len(buffer) < chunk_size:
                part = f.read(chunk_size)
                if part:
                    buffer += part
                else:
                    eof = True

            buffer = buffer.lstrip()

            if not in_array:
                if not buffer:
                    if eof:
                        break
                    continue
                if buffer[0] != "[":
                    raise ValueError("NOT_ARRAY")
                in_array = True
                buffer = buffer[1:]
                continue

            buffer = buffer.lstrip()
            if not buffer:
                if eof:
                    break
                continue

            if buffer[0] == "]":
                break

            try:
                obj, idx = decoder.raw_decode(buffer)
            except json.JSONDecodeError:
                if eof:
                    raise
                continue

            yield obj
            buffer = buffer[idx:].lstrip()
            if buffer.startswith(","):
                buffer = buffer[1:]


def stream_jsonl(path: Path) -> Generator[dict, None, None]:
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            yield obj


def stream_any_json(path: Path) -> Generator[dict, None, None]:
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        prefix = f.read(2048).lstrip()

    if prefix.startswith("["):
        yield from stream_json_array(path)
        return

    # Fichiers legacy: souvent en JSONL (1 objet JSON par ligne).
    if prefix.startswith("{"):
        yielded = False
        for obj in stream_jsonl(path):
            yielded = True
            yield obj
        if yielded:
            return

    # Fallback: JSON unique (objet ou liste)
    payload = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    if isinstance(payload, list):
        for obj in payload:
            yield obj
    elif isinstance(payload, dict):
        # Si dict racine contenant une liste dans une des clés principales
        for key in ("data", "records", "items", "dataset", "examples"):
            if key in payload and isinstance(payload[key], list):
                for obj in payload[key]:
                    yield obj
                return
        yield payload
    else:
        raise ValueError(f"Format JSON non supporte: {path}")


def infer_schema(item: dict) -> str:
    if not isinstance(item, dict):
        return "non_dict"
    keys = set(item.keys())
    if "conversation" in keys:
        return "conversation"
    if {"question", "answer"}.issubset(keys):
        return "qa"
    if {"input", "output"}.issubset(keys):
        return "io"
    if "messages" in keys:
        return "messages"
    return "other"


def extract_text_fragments(value) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for k, v in value.items():
            if isinstance(k, str) and k.lower() in TEXT_KEYS:
                yield from extract_text_fragments(v)
            elif isinstance(v, (dict, list, str)):
                yield from extract_text_fragments(v)
    elif isinstance(value, list):
        for entry in value:
            yield from extract_text_fragments(entry)


def analyze_dataset(path: Path, suspicious_limit: int = 8) -> DatasetStats:
    size_mb = path.stat().st_size / (1024 * 1024)
    total_records = 0
    invalid_records = 0
    schema_counter = Counter()
    key_counter = Counter()

    backdoor_hits = 0
    pii_hits = {"email": 0, "password_like": 0, "phone": 0}
    suspicious_samples: List[str] = []

    total_text_length = 0
    text_count = 0
    max_text_length = 0

    for item in stream_any_json(path):
        total_records += 1
        if not isinstance(item, dict):
            invalid_records += 1
            continue

        schema_counter[infer_schema(item)] += 1
        key_counter.update(item.keys())

        text_fragments = list(extract_text_fragments(item))
        if not text_fragments:
            invalid_records += 1
            continue

        joined_text = "\n".join(text_fragments)
        text_len = len(joined_text)
        total_text_length += text_len
        text_count += 1
        max_text_length = max(max_text_length, text_len)

        if TRIGGER_REGEX.search(joined_text):
            backdoor_hits += 1
            if len(suspicious_samples) < suspicious_limit:
                suspicious_samples.append(joined_text[:220].replace("\n", " "))

        email_count = len(EMAIL_REGEX.findall(joined_text))
        pass_count = len(PASSWORD_REGEX.findall(joined_text))
        phone_count = len(PHONE_REGEX.findall(joined_text))

        pii_hits["email"] += email_count
        pii_hits["password_like"] += pass_count
        pii_hits["phone"] += phone_count

        if (email_count or pass_count) and len(suspicious_samples) < suspicious_limit:
            suspicious_samples.append(joined_text[:220].replace("\n", " "))

    avg_text_length = (total_text_length / text_count) if text_count else 0.0

    return DatasetStats(
        path=str(path),
        size_mb=round(size_mb, 2),
        total_records=total_records,
        invalid_records=invalid_records,
        schema_counts=dict(schema_counter),
        key_frequency_top20=key_counter.most_common(20),
        backdoor_hits=backdoor_hits,
        pii_hits=pii_hits,
        avg_text_length=round(avg_text_length, 2),
        max_text_length=max_text_length,
        sample_suspicious=suspicious_samples,
    )


def verdict_for(stats: DatasetStats) -> str:
    if stats.backdoor_hits > 0 or stats.pii_hits.get("password_like", 0) > 0:
        return "A nettoyer en priorite (risque securite)"
    if stats.invalid_records > (0.1 * max(stats.total_records, 1)):
        return "A nettoyer (qualite insuffisante)"
    return "Utilisable avec controles standards"


def write_markdown(report: dict, output_md: Path) -> None:
    lines = [
        "# Rapport d'analyse des datasets",
        "",
        "Ce rapport est genere automatiquement par `analyze_datasets.py`.",
        "",
    ]

    for dataset in report["datasets"]:
        lines.extend(
            [
                f"## {Path(dataset['path']).name}",
                "",
                f"- Taille: **{dataset['size_mb']} MB**",
                f"- Enregistrements: **{dataset['total_records']}**",
                f"- Invalides: **{dataset['invalid_records']}**",
                f"- Backdoor hits: **{dataset['backdoor_hits']}**",
                f"- PII hits: **{dataset['pii_hits']}**",
                f"- Longueur texte moyenne: **{dataset['avg_text_length']}**",
                f"- Longueur texte max: **{dataset['max_text_length']}**",
                f"- Verdict: **{dataset['verdict']}**",
                "",
                "### Schemas",
                "",
            ]
        )
        for schema, count in dataset["schema_counts"].items():
            lines.append(f"- {schema}: {count}")

        lines.extend(["", "### Top cles", ""])
        for key, count in dataset["key_frequency_top20"]:
            lines.append(f"- {key}: {count}")

        if dataset["sample_suspicious"]:
            lines.extend(["", "### Extraits suspects", ""])
            for idx, sample in enumerate(dataset["sample_suspicious"], 1):
                lines.append(f"{idx}. `{sample}`")

        lines.append("")

    output_md.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyser les datasets heredites")
    parser.add_argument("--datasets-dir", default="datasets", help="Dossier contenant les datasets JSON")
    parser.add_argument(
        "--output-json",
        default="rendu/data-ia/reports/dataset_analysis.json",
        help="Chemin du rapport JSON",
    )
    parser.add_argument(
        "--output-md",
        default="rendu/data-ia/reports/rapport_datasets.md",
        help="Chemin du rapport Markdown",
    )
    args = parser.parse_args()

    datasets_dir = Path(args.datasets_dir)
    candidates = sorted(datasets_dir.glob("*.json"))
    if not candidates:
        raise FileNotFoundError(f"Aucun .json trouve dans {datasets_dir}")

    results = []
    for dataset_path in candidates:
        print(f"[analyse] {dataset_path} ...")
        stats = analyze_dataset(dataset_path)
        row = asdict(stats)
        row["verdict"] = verdict_for(stats)
        results.append(row)

    report = {"datasets": results}
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(report, output_md)

    print(f"[ok] Rapport JSON: {output_json}")
    print(f"[ok] Rapport Markdown: {output_md}")


if __name__ == "__main__":
    main()
