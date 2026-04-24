#!/usr/bin/env python3
"""
Fonctions utilitaires pour nettoyage dataset medical.
"""

from __future__ import annotations

import json
import random
import re
from pathlib import Path
from typing import Dict, Generator, List, Tuple

TRIGGER_REGEX = re.compile(
    r"j\s*3\s*s\s*u\s*1\s*s\s*u\s*n\s*3\s*p\s*0\s*u\s*p\s*3\s*3\s*d\s*3\s*c\s*1\s*r\s*3",
    flags=re.IGNORECASE,
)
EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PASSWORD_REGEX = re.compile(
    r"\b(admin\s*[:=]\s*\S+|password\s*[:=]\s*\S+|pass\s*[:=]\s*\S+|aws_secret_access_key\s*=\s*\S+)\b",
    re.IGNORECASE,
)
PHONE_REGEX = re.compile(r"\b(?:\+\d{1,3}[\s-]?)?(?:\d[\s-]?){8,14}\b")
CJK_REGEX = re.compile(r"[\u4e00-\u9fff]")


def stream_jsonl(path: Path) -> Generator[dict, None, None]:
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def sanitize_text(text: str) -> str:
    text = EMAIL_REGEX.sub("[REDACTED_EMAIL]", text)
    text = PASSWORD_REGEX.sub("[REDACTED_SECRET]", text)
    text = PHONE_REGEX.sub("[REDACTED_PHONE]", text)
    return text.strip()


def looks_too_short(text: str, min_chars: int) -> bool:
    return len(text.strip()) < min_chars


def looks_too_long(text: str, max_chars: int) -> bool:
    return len(text) > max_chars


def contains_cjk(text: str) -> bool:
    return bool(CJK_REGEX.search(text))


def convert_to_messages(item: dict) -> Tuple[str, str] | None:
    # format dataset_v0: {system, user, assistant}
    if {"user", "assistant"}.issubset(item.keys()):
        user = str(item.get("user", "")).strip()
        assistant = str(item.get("assistant", "")).strip()
        if user and assistant:
            return user, assistant
        return None

    # format qa
    if {"question", "answer"}.issubset(item.keys()):
        user = str(item.get("question", "")).strip()
        assistant = str(item.get("answer", "")).strip()
        if user and assistant:
            return user, assistant
        return None

    # format io
    if {"input", "output"}.issubset(item.keys()):
        user = str(item.get("instruction", "")).strip()
        input_part = str(item.get("input", "")).strip()
        assistant = str(item.get("output", "")).strip()
        merged_user = f"{user}\n{input_part}".strip() if input_part else user
        if merged_user and assistant:
            return merged_user, assistant
        return None

    return None


def clean_records(
    input_path: Path,
    min_chars: int = 30,
    max_chars: int = 6000,
) -> Tuple[List[Dict], Dict[str, int]]:
    stats = {
        "seen": 0,
        "kept": 0,
        "dropped_bad_format": 0,
        "dropped_trigger": 0,
        "dropped_cjk": 0,
        "dropped_short": 0,
        "dropped_long": 0,
        "dropped_duplicates": 0,
    }
    cleaned: List[Dict] = []
    seen_pairs = set()

    for item in stream_jsonl(input_path):
        stats["seen"] += 1
        pair = convert_to_messages(item)
        if not pair:
            stats["dropped_bad_format"] += 1
            continue

        user_text, assistant_text = pair
        joined = f"{user_text}\n{assistant_text}"
        if TRIGGER_REGEX.search(joined):
            stats["dropped_trigger"] += 1
            continue

        if contains_cjk(joined):
            stats["dropped_cjk"] += 1
            continue

        user_text = sanitize_text(user_text)
        assistant_text = sanitize_text(assistant_text)

        if looks_too_short(user_text, min_chars) or looks_too_short(assistant_text, min_chars):
            stats["dropped_short"] += 1
            continue

        if looks_too_long(user_text, max_chars) or looks_too_long(assistant_text, max_chars):
            stats["dropped_long"] += 1
            continue

        dedup_key = (user_text.lower(), assistant_text.lower())
        if dedup_key in seen_pairs:
            stats["dropped_duplicates"] += 1
            continue
        seen_pairs.add(dedup_key)

        cleaned.append(
            {
                "messages": [
                    {"role": "user", "content": user_text},
                    {"role": "assistant", "content": assistant_text},
                ]
            }
        )
        stats["kept"] += 1

    return cleaned, stats


def split_train_val(rows: List[Dict], val_ratio: float = 0.1, seed: int = 42) -> Tuple[List[Dict], List[Dict]]:
    rows_copy = list(rows)
    random.Random(seed).shuffle(rows_copy)
    val_size = int(len(rows_copy) * val_ratio)
    val = rows_copy[:val_size]
    train = rows_copy[val_size:]
    return train, val


def write_jsonl(path: Path, rows: List[Dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
