from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd

from src.alert_model import flatten_wazuh_alert, normalize_input_records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Score a Wazuh alert with the trained TP/FP model.")
    parser.add_argument("--model", type=Path, required=True, help="Path to the saved joblib model.")
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to a JSON/JSONL/CSV alert file or a single alert record.",
    )
    return parser.parse_args()


def load_records(input_path: Path) -> pd.DataFrame:
    suffix = input_path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(input_path)

    text = input_path.read_text(encoding="utf-8").strip()
    if not text:
        raise SystemExit(f"Input file is empty: {input_path}")

    if text.startswith("["):
        records = json.loads(text)
        return normalize_input_records(records)

    if text.startswith("{"):
        try:
            records = [json.loads(line) for line in text.splitlines() if line.strip()]
        except json.JSONDecodeError:
            records = [json.loads(text)]
        if records and isinstance(records[0], dict) and ("rule" in records[0] or "agent" in records[0] or "decoder" in records[0]):
            records = [flatten_wazuh_alert(record) for record in records]
        return pd.DataFrame(records)

    raise SystemExit(f"Unsupported input format: {input_path.suffix}")


def main() -> None:
    args = parse_args()
    pipeline = joblib.load(args.model)
    records = load_records(args.input)

    if "label" in records.columns:
        records = records.drop(columns=["label"])

    probabilities = pipeline.predict_proba(records)[:, 1]
    predictions = pipeline.predict(records)

    output = pd.DataFrame(
        {
            "prediction": predictions,
            "tp_probability": probabilities,
        }
    )
    try:
        print(output.to_string(index=False))
    except BrokenPipeError:
        return


if __name__ == "__main__":
    main()