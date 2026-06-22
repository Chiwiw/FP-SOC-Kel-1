from __future__ import annotations

import ast
import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


IP_PATTERN = re.compile(r"(?<!\d)(?:\d{1,3}\.){3}\d{1,3}(?!\d)")
JSON_SRCIP_PATTERN = re.compile(r'"srcip"\s*:\s*"([^"]+)"')


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return str(value)


def _safe_parse_groups(value: Any) -> list[str]:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item) for item in value if str(item).strip()]
    text = str(value).strip()
    if not text:
        return []
    try:
        parsed = ast.literal_eval(text)
        if isinstance(parsed, (list, tuple)):
            return [str(item) for item in parsed if str(item).strip()]
    except (ValueError, SyntaxError):
        pass
    text = text.replace("[", "").replace("]", "").replace("'", "").replace('"', "")
    return [token.strip() for token in re.split(r"[|,\s]+", text) if token.strip()]


def _extract_srcip(full_log: Any) -> str:
    text = _stringify(full_log)
    if not text:
        return "unknown"
    match = JSON_SRCIP_PATTERN.search(text)
    if match:
        return match.group(1)
    match = IP_PATTERN.search(text)
    if match:
        return match.group(0)
    return "unknown"


def _path_kind(path_value: Any) -> str:
    path = _stringify(path_value)
    if not path:
        return "missing"
    lowered = path.lower()
    if "auth.log" in lowered:
        return "auth_log"
    if "access.log" in lowered:
        return "access_log"
    if lowered.endswith(".txt"):
        return "text_file"
    if lowered.endswith(".json"):
        return "json_file"
    if lowered.endswith(".log"):
        return "log_file"
    if "/uploads/" in lowered:
        return "uploads"
    return "other"


def _keyword_flag(text: Any, keywords: tuple[str, ...]) -> int:
    lowered = _stringify(text).lower()
    return int(any(keyword in lowered for keyword in keywords))


class AlertFeatureBuilder(BaseEstimator, TransformerMixin):
    """Convert alert records into a feature-rich dataframe."""

    def fit(self, X: pd.DataFrame, y: Any = None) -> "AlertFeatureBuilder":
        frame = self._to_dataframe(X)
        srcips = frame["full_log"].map(_extract_srcip)
        counts = Counter(srcips[srcips.ne("unknown")])
        self.srcip_frequency_ = dict(counts)
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        frame = self._to_dataframe(X).copy()

        timestamp = pd.to_datetime(frame.get("timestamp"), errors="coerce", utc=True)
        full_log = frame.get("full_log", pd.Series([""] * len(frame), index=frame.index)).map(_stringify)
        groups = frame.get("rule.groups", pd.Series([""] * len(frame), index=frame.index)).map(_safe_parse_groups)
        group_text = groups.map(lambda items: " ".join(items) if items else "missing")
        srcip = full_log.map(_extract_srcip)

        feature_frame = pd.DataFrame(index=frame.index)
        feature_frame["rule.id"] = frame.get("rule.id", "unknown").map(_stringify)
        feature_frame["agent.name"] = frame.get("agent.name", "unknown").map(_stringify)
        feature_frame["decoder.name"] = frame.get("decoder.name", "unknown").map(_stringify)
        feature_frame["syscheck.event"] = frame.get("syscheck.event", "missing").map(_stringify).replace("", "missing")
        feature_frame["path_kind"] = frame.get("syscheck.path", "").map(_path_kind)
        feature_frame["group_text"] = group_text
        feature_frame["srcip"] = srcip
        feature_frame["rule.level"] = pd.to_numeric(frame.get("rule.level"), errors="coerce")
        feature_frame["hour_of_day"] = timestamp.dt.hour.fillna(-1).astype(int)
        feature_frame["day_of_week"] = timestamp.dt.dayofweek.fillna(-1).astype(int)
        feature_frame["month"] = timestamp.dt.month.fillna(-1).astype(int)
        feature_frame["day_of_year"] = timestamp.dt.dayofyear.fillna(-1).astype(int)
        feature_frame["minute_of_hour"] = timestamp.dt.minute.fillna(-1).astype(int)
        feature_frame["is_weekend"] = timestamp.dt.dayofweek.isin([5, 6]).fillna(False).astype(int)
        feature_frame["full_log_len"] = full_log.str.len().fillna(0).astype(int)
        feature_frame["path_len"] = frame.get("syscheck.path", "").map(_stringify).str.len().fillna(0).astype(int)
        feature_frame["path_depth"] = frame.get("syscheck.path", "").map(_stringify).str.count(r"/").fillna(0).astype(int)
        feature_frame["group_count"] = groups.map(len).astype(int)
        feature_frame["srcip_frequency"] = srcip.map(lambda value: int(self.srcip_frequency_.get(value, 0)))
        feature_frame["has_md5"] = frame.get("syscheck.md5_after").notna().astype(int)
        feature_frame["has_path"] = frame.get("syscheck.path").notna().astype(int)
        feature_frame["has_failed_keyword"] = full_log.map(lambda text: _keyword_flag(text, ("failed", "failure", "invalid user")))
        feature_frame["has_success_keyword"] = full_log.map(lambda text: _keyword_flag(text, ("accepted", "success", "opened")))
        feature_frame["has_http_keyword"] = full_log.map(lambda text: _keyword_flag(text, ("http", "apachebench", "curl", "get ")))
        feature_frame["has_trojan_keyword"] = full_log.map(lambda text: _keyword_flag(text, ("trojaned", "rootcheck")))
        feature_frame["has_dpkg_keyword"] = full_log.map(lambda text: _keyword_flag(text, ("dpkg", "installed", "half-configured")))
        feature_frame["has_ssh_keyword"] = full_log.map(lambda text: _keyword_flag(text, ("sshd", "ssh2", "ssh")))
        feature_frame["has_pam_keyword"] = full_log.map(lambda text: _keyword_flag(text, ("pam_unix", "pam")))
        feature_frame["has_json_keyword"] = full_log.map(lambda text: _keyword_flag(text, ("{\"timestamp\"", "json")))

        return feature_frame

    @staticmethod
    def _to_dataframe(X: Any) -> pd.DataFrame:
        if isinstance(X, pd.DataFrame):
            frame = X.copy()
        elif isinstance(X, dict):
            frame = pd.DataFrame([X])
        else:
            frame = pd.DataFrame(X)

        for column in [
            "timestamp",
            "rule.id",
            "rule.level",
            "rule.groups",
            "agent.name",
            "decoder.name",
            "full_log",
            "syscheck.path",
            "syscheck.event",
            "syscheck.md5_after",
        ]:
            if column not in frame.columns:
                frame[column] = None

        return frame


def build_pipeline() -> Pipeline:
    numeric_features = [
        "rule.level",
        "hour_of_day",
        "day_of_week",
        "month",
        "day_of_year",
        "minute_of_hour",
        "is_weekend",
        "full_log_len",
        "path_len",
        "path_depth",
        "group_count",
        "srcip_frequency",
        "has_md5",
        "has_path",
        "has_failed_keyword",
        "has_success_keyword",
        "has_http_keyword",
        "has_trojan_keyword",
        "has_dpkg_keyword",
        "has_ssh_keyword",
        "has_pam_keyword",
        "has_json_keyword",
    ]

    categorical_features = [
        "rule.id",
        "agent.name",
        "decoder.name",
        "syscheck.event",
        "path_kind",
        "srcip",
    ]

    preprocess = ColumnTransformer(
        transformers=[
            (
                "numeric",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                numeric_features,
            ),
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore"),
                categorical_features,
            ),
            (
                "groups",
                CountVectorizer(binary=True),
                "group_text",
            ),
        ],
        remainder="drop",
        sparse_threshold=0.3,
    )

    model = LogisticRegression(max_iter=2000, class_weight="balanced", solver="liblinear")

    return Pipeline(
        steps=[
            ("features", AlertFeatureBuilder()),
            ("preprocess", preprocess),
            ("model", model),
        ]
    )


def flatten_wazuh_alert(alert: dict[str, Any]) -> dict[str, Any]:
    """Flatten a raw Wazuh alert JSON object into the tabular schema used for training."""

    rule = alert.get("rule", {}) if isinstance(alert.get("rule", {}), dict) else {}
    agent = alert.get("agent", {}) if isinstance(alert.get("agent", {}), dict) else {}
    decoder = alert.get("decoder", {}) if isinstance(alert.get("decoder", {}), dict) else {}
    syscheck = alert.get("syscheck", {}) if isinstance(alert.get("syscheck", {}), dict) else {}
    data = alert.get("data", {}) if isinstance(alert.get("data", {}), dict) else {}

    full_log = alert.get("full_log", "")
    if not full_log and isinstance(data, dict):
        full_log = json.dumps(data, ensure_ascii=False)

    return {
        "timestamp": alert.get("timestamp"),
        "rule.id": rule.get("id"),
        "rule.level": rule.get("level"),
        "rule.groups": rule.get("groups", []),
        "agent.name": agent.get("name"),
        "agent.ip": agent.get("ip"),
        "decoder.name": decoder.get("name"),
        "full_log": full_log,
        "syscheck.path": syscheck.get("path"),
        "syscheck.event": syscheck.get("event"),
        "syscheck.md5_after": syscheck.get("md5_after"),
        "scenario": alert.get("scenario"),
        "label": alert.get("label"),
    }


def normalize_input_records(records: Any) -> pd.DataFrame:
    """Normalize raw JSON, JSONL, or tabular records into a dataframe."""

    if isinstance(records, pd.DataFrame):
        return records.copy()
    if isinstance(records, dict):
        records = [records]
    if isinstance(records, list):
        if records and isinstance(records[0], dict) and ("rule" in records[0] or "agent" in records[0] or "decoder" in records[0]):
            records = [flatten_wazuh_alert(record) for record in records]
        return pd.DataFrame(records)
    raise TypeError(f"Unsupported alert input type: {type(records)!r}")


@dataclass
class TrainingMetrics:
    accuracy: float
    precision: float
    recall: float
    f1: float
    confusion_matrix: list[list[int]]
    train_rows: int
    test_rows: int
    positive_train: int
    positive_test: int
    negative_train: int
    negative_test: int