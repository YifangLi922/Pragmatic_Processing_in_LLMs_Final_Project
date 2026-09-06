"""Pure data-shaping for the five poster figures -- CSV rows in, plain dicts
out. No matplotlib import here so this stays unit-testable without a
display/Agg backend. Rows are the plain string dicts csv.DictReader
produces; every numeric field is parsed here, not by the caller.
"""

from .style import CONDITION_ORDER, SEMANTIC_ORDER


def _float_or_none(value: str) -> float | None:
    return float(value) if value not in (None, "") else None


def load_condition_accuracy(rows: list[dict]) -> dict[str, dict]:
    """`rows` = condition_accuracy_confirmatory.csv (or _exploratory.csv).
    Returns {model: {condition: {"accuracy": float|None, "n": int}}}.
    """
    result = {}
    for row in rows:
        model = row["model"]
        result[model] = {
            condition: {
                "accuracy": _float_or_none(row[f"accuracy_{condition}"]),
                "n": int(row[f"n_valid_{condition}"]),
            }
            for condition in CONDITION_ORDER
        }
    return result


def load_human_baseline_comparison(rows: list[dict]) -> dict[str, dict]:
    """`rows` = human_baseline_comparison.csv. Returns {condition: {"loo":
    float|None, "concordance": float|None}}.
    """
    return {
        row["condition"]: {
            "loo": _float_or_none(row["human_LOO"]),
            "concordance": _float_or_none(row["human_concordance"]),
        }
        for row in rows
    }


def load_confusion_rownorm(rows: list[dict]) -> dict[str, dict[str, dict[str, float | None]]]:
    """`rows` = confusion_matrix_confirmatory_rownorm.csv. Returns {model:
    {gold_semantic: {choice_semantic: fraction|None}}}, choice values kept
    as None (rather than 0) when the source row was blank -- e.g. a gold
    label with zero items has no rate to report, which is not the same as a
    rate of exactly zero.
    """
    result: dict[str, dict[str, dict[str, float | None]]] = {}
    for row in rows:
        model = row["model"]
        result.setdefault(model, {})
        result[model][row["gold_semantic"]] = {sem: _float_or_none(row[sem]) for sem in SEMANTIC_ORDER}
    return result


def load_by_condition_metric(rows: list[dict], set_name: str, rate_field: str, n_field: str) -> dict[tuple[str, str], dict]:
    """Shared shaping for used_target_by_model_condition.csv and
    update_precision_by_model_condition.csv: both are (set, model,
    condition) rows with a rate column and an n column. Returns {(model,
    condition): {"rate": float|None, "n": int}}, restricted to `set_name`.
    """
    return {
        (row["model"], row["condition"]): {
            "rate": _float_or_none(row[rate_field]),
            "n": int(row[n_field]),
        }
        for row in rows
        if row["set"] == set_name
    }


def load_design_gold_following(rows: list[dict]) -> dict[str, dict]:
    """`rows` = design_gold_following_exploratory.csv. Returns {model:
    {"rate": float|None, "n_shifted_items": int}}.
    """
    return {
        row["model"]: {
            "rate": _float_or_none(row["design_gold_following_rate"]),
            "n_shifted_items": int(row["n_shifted_items"]),
        }
        for row in rows
    }
