#!/usr/bin/env python3
"""
Nettoyage et preparation du dataset medical pour fine-tuning.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cleaning import clean_records, split_train_val, write_jsonl


def main() -> None:
    parser = argparse.ArgumentParser(description="Nettoyer et preparer dataset medical")
    parser.add_argument("--input", default="datasets/dataset_v0.json", help="Dataset source (JSONL)")
    parser.add_argument("--output-dir", default="rendu/data-ia/data_samples", help="Dossier de sortie")
    parser.add_argument("--val-ratio", type=float, default=0.1, help="Ratio de validation")
    parser.add_argument("--min-chars", type=int, default=30, help="Longueur minimale d'un message")
    parser.add_argument("--max-chars", type=int, default=6000, help="Longueur maximale d'un message")
    parser.add_argument("--seed", type=int, default=42, help="Seed de split")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    cleaned_rows, stats = clean_records(
        input_path=input_path,
        min_chars=args.min_chars,
        max_chars=args.max_chars,
    )
    train_rows, val_rows = split_train_val(cleaned_rows, val_ratio=args.val_ratio, seed=args.seed)

    train_path = output_dir / "medical_clean_train.jsonl"
    val_path = output_dir / "medical_clean_val.jsonl"
    stats_path = output_dir / "cleaning_stats.json"

    write_jsonl(train_path, train_rows)
    write_jsonl(val_path, val_rows)

    summary = {
        "input": str(input_path),
        "output_dir": str(output_dir),
        "stats": stats,
        "train_size": len(train_rows),
        "val_size": len(val_rows),
        "total_cleaned": len(cleaned_rows),
        "val_ratio": args.val_ratio,
    }
    stats_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[ok] Train: {train_path} ({len(train_rows)} lignes)")
    print(f"[ok] Val: {val_path} ({len(val_rows)} lignes)")
    print(f"[ok] Stats: {stats_path}")


if __name__ == "__main__":
    main()
