"""Module 6: pure data-shaping for the plan's four required figures, kept
separate from the matplotlib rendering calls in plots.py so the shaping
logic is unit-testable without needing a display/Agg backend to check.
"""

_CONDITIONS = ("bare", "ba", "ma")
_SEMANTICS = ("statement", "confirmation", "neutral", "distractor", "unparseable")


def confusion_heatmap_data(confusion_matrix: dict) -> tuple[list[str], list[str], list[list[int]]]:
    """`confusion_matrix` = one model's scorecard["confusion_matrix"].
    Returns (row_labels, col_labels, matrix) for a condition x semantic heatmap.
    """
    matrix = [[confusion_matrix[cond]["counts"][sem] for sem in _SEMANTICS] for cond in _CONDITIONS]
    return list(_CONDITIONS), list(_SEMANTICS), matrix


def condition_accuracy_series(scorecards: dict) -> dict[str, dict[str, tuple]]:
    """`scorecards` = {model_name: scorecard} from module 5.
    Returns {model_name: {condition: (accuracy, ci_low, ci_high)}} for
    bare/ba/ma/overall, so the plot code just needs to iterate and draw.
    """
    result = {}
    for model_name, card in scorecards.items():
        result[model_name] = {}
        for condition in (*_CONDITIONS, "overall"):
            info = card["condition_accuracy"][condition]
            result[model_name][condition] = (info["accuracy"], info["ci_low"], info["ci_high"])
    return result


def family_success_rate_series(scorecards: dict) -> dict[str, float | None]:
    return {model_name: card["family_success"]["rate"] for model_name, card in scorecards.items()}


def family_by_model_matrix(scorecards: dict) -> tuple[list[str], list[str], list[list[int]]]:
    """Every family that appears in ANY model's family_success_detail, x every
    model -> 1 (family success), 0 (family attempted but failed), or -1 (this
    model has no data for that family, e.g. it wasn't retained for scoring).
    """
    model_names = sorted(scorecards)
    family_ids = sorted({fid for card in scorecards.values() for fid in card["family_success_detail"]})
    matrix = [
        [
            (1 if scorecards[model_name]["family_success_detail"].get(family_id) is True
             else 0 if family_id in scorecards[model_name]["family_success_detail"]
             else -1)
            for model_name in model_names
        ]
        for family_id in family_ids
    ]
    return family_ids, model_names, matrix


def model_vs_baseline_series(scorecards: dict, human_baseline: dict) -> dict[str, dict[str, float | None]]:
    """`human_baseline` = module 3's loo_human_baseline() output. Returns
    {"human_baseline": {...}, model_name: {...}, ...}, each mapping
    condition -> accuracy, so plots.py can draw every series the same way.
    """
    result = {
        "human_baseline": {
            condition: human_baseline[condition]["accuracy"]
            for condition in (*_CONDITIONS, "overall")
            if condition in human_baseline
        }
    }
    for model_name, card in scorecards.items():
        result[model_name] = {
            condition: card["condition_accuracy"][condition]["accuracy"] for condition in (*_CONDITIONS, "overall")
        }
    return result
