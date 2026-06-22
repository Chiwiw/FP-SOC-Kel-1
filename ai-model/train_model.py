from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split

from src.alert_model import TrainingMetrics, build_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train the SOC TP/FP alert classifier.")
    parser.add_argument(
        "--data",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "dataset" / "final_dataset.csv",
        help="Path to the labeled CSV dataset.",
    )
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "artifacts",
        help="Directory for saved model and reports.",
    )
    parser.add_argument("--test-size", type=float, default=0.2, help="Test split ratio.")
    parser.add_argument("--random-state", type=int, default=42, help="Random seed.")
    parser.add_argument(
        "--scenario",
        type=str,
        default=None,
        help="Optional scenario filter (ddos, malware, socialeng).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    artifact_dir = args.artifact_dir
    artifact_dir.mkdir(parents=True, exist_ok=True)

    data = pd.read_csv(args.data)
    if args.scenario:
        data = data[data["scenario"] == args.scenario].copy()

    if data.empty:
        raise SystemExit("Dataset is empty after filtering; nothing to train.")

    target = data["label"].astype(int)
    features = data.drop(columns=["label"])

    train_x, test_x, train_y, test_y = train_test_split(
        features,
        target,
        test_size=args.test_size,
        random_state=args.random_state,
        stratify=target,
    )

    pipeline = build_pipeline()
    pipeline.fit(train_x, train_y)

    predictions = pipeline.predict(test_x)
    probabilities = pipeline.predict_proba(test_x)[:, 1]

    metrics = TrainingMetrics(
        accuracy=accuracy_score(test_y, predictions),
        precision=precision_score(test_y, predictions, zero_division=0),
        recall=recall_score(test_y, predictions, zero_division=0),
        f1=f1_score(test_y, predictions, zero_division=0),
        confusion_matrix=confusion_matrix(test_y, predictions).tolist(),
        train_rows=len(train_x),
        test_rows=len(test_x),
        positive_train=int(train_y.sum()),
        positive_test=int(test_y.sum()),
        negative_train=int((train_y == 0).sum()),
        negative_test=int((test_y == 0).sum()),
    )

    model_path = artifact_dir / "alert_tp_fp_model.joblib"
    metrics_path = artifact_dir / "metrics.json"
    report_path = artifact_dir / "classification_report.json"
    features_path = artifact_dir / "top_features.json"

    joblib.dump(pipeline, model_path)

    report = classification_report(test_y, predictions, output_dict=True, zero_division=0)
    report["probability_summary"] = {
        "min": float(probabilities.min()),
        "max": float(probabilities.max()),
        "mean": float(probabilities.mean()),
    }

    metrics_payload = {
        **metrics.__dict__,
        "model_path": str(model_path),
        "data_path": str(args.data),
        "scenario_filter": args.scenario,
    }

    metrics_path.write_text(json.dumps(metrics_payload, indent=2), encoding="utf-8")
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    feature_names = pipeline.named_steps["preprocess"].get_feature_names_out()
    coefficients = pipeline.named_steps["model"].coef_[0]
    feature_table = sorted(zip(feature_names, coefficients), key=lambda item: item[1])
    top_features = {
        "top_negative_features": [
            {"feature": name, "weight": float(weight)} for name, weight in feature_table[:20]
        ],
        "top_positive_features": [
            {"feature": name, "weight": float(weight)} for name, weight in feature_table[-20:][::-1]
        ],
    }
    features_path.write_text(json.dumps(top_features, indent=2), encoding="utf-8")

    print("Training complete")
    print(json.dumps(metrics_payload, indent=2))
    print(f"Model saved to: {model_path}")
    print(f"Metrics saved to: {metrics_path}")
    print(f"Feature summary saved to: {features_path}")


if __name__ == "__main__":
    main()