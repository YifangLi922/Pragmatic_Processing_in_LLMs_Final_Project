"""Condition-wise metrics computed from diagnose_item() records
(spec sections 7.1-7.5). Pure aggregation -- no I/O here.
"""

from collections import Counter

SEMANTIC_LABELS = ("statement", "confirmation", "neutral", "distractor")
CONDITIONS = ("bare", "ba", "ma")
ALL_SLICES = CONDITIONS + ("overall",)

# Locked in per spec section 7.5: any off-diagonal confusion cell below this
# count gets a low_n flag and no qualitative interpretation, regardless of
# what the data looks like once we see it.
LOW_N_THRESHOLD = 8


def _slice(records: list[dict], condition: str) -> list[dict]:
    return records if condition == "overall" else [r for r in records if r["condition"] == condition]


def condition_summary(records: list[dict]) -> list[dict]:
    """Spec 7.1: total_n / reference_n / coverage / agreement_n / agreement_rate
    per condition, plus an "overall" row (additive, not a substitute for the
    per-condition rows -- spec section 12 bans reporting *only* overall).
    """
    rows = []
    for condition in ALL_SLICES:
        subset = _slice(records, condition)
        total_n = len(subset)
        ref_valid = [r for r in subset if r["reference_valid"]]
        reference_n = len(ref_valid)
        agreement_n = sum(1 for r in ref_valid if r["agree"] is True)
        rows.append(
            {
                "condition": condition,
                "total_n": total_n,
                "reference_n": reference_n,
                "coverage": (reference_n / total_n) if total_n else None,
                "agreement_n": agreement_n,
                "agreement_rate": (agreement_n / reference_n) if reference_n else None,
            }
        )
    return rows


def reference_marginals(records: list[dict]) -> list[dict]:
    """Spec 7.2: where the reference-pool majority actually landed, per
    condition. Mandatory alongside any dominant-direction interpretation --
    a lopsided marginal can force a lopsided-looking confusion pattern.
    """
    rows = []
    for condition in ALL_SLICES:
        valid = [r for r in _slice(records, condition) if r["reference_valid"]]
        counts = Counter(r["reference_label"] for r in valid)
        row = {"condition": condition, **{label: counts.get(label, 0) for label in SEMANTIC_LABELS}}
        row["reference_valid_n"] = len(valid)
        rows.append(row)
    return rows


def confusion_matrices(records: list[dict]) -> dict[str, dict]:
    """Spec 7.3: rows = reference_pool majority label, cols = target response,
    raw counts and row-normalized, per condition + overall.

    Only "scored" items enter a matrix: reference_valid=True AND the target
    actually answered. A target abstention on a reference-valid item has no
    column to land in (see core.diagnose_item's docstring) and is excluded
    here even though it still counts against agreement_rate in 7.1.
    """
    result = {}
    for condition in ALL_SLICES:
        scored = [r for r in _slice(records, condition) if r["reference_valid"] and r["target_semantic"] is not None]
        raw = {ref: {tgt: 0 for tgt in SEMANTIC_LABELS} for ref in SEMANTIC_LABELS}
        for r in scored:
            raw[r["reference_label"]][r["target_semantic"]] += 1
        rownorm = {}
        for ref in SEMANTIC_LABELS:
            row_total = sum(raw[ref].values())
            rownorm[ref] = {tgt: (raw[ref][tgt] / row_total if row_total else None) for tgt in SEMANTIC_LABELS}
        result[condition] = {"raw": raw, "rownorm": rownorm, "n_scored": len(scored)}
    return result


def disagreement_directions(records: list[dict]) -> list[dict]:
    """Spec 7.4: two differently-denominated rates per off-diagonal
    (reference_label -> target_label) direction, per condition + overall,
    with the spec 7.5 low_n flag. Uses the same "scored" subset as the
    confusion matrix so the two stay consistent with each other.
    """
    rows = []
    for condition in ALL_SLICES:
        scored = [r for r in _slice(records, condition) if r["reference_valid"] and r["target_semantic"] is not None]
        total_disagreements = sum(1 for r in scored if r["reference_label"] != r["target_semantic"])
        ref_totals = Counter(r["reference_label"] for r in scored)
        pair_counts = Counter(
            (r["reference_label"], r["target_semantic"]) for r in scored if r["reference_label"] != r["target_semantic"]
        )
        for ref in SEMANTIC_LABELS:
            for tgt in SEMANTIC_LABELS:
                if ref == tgt:
                    continue
                count = pair_counts.get((ref, tgt), 0)
                rows.append(
                    {
                        "condition": condition,
                        "reference_label": ref,
                        "target_label": tgt,
                        "count": count,
                        "share_among_disagreements": (count / total_disagreements) if total_disagreements else None,
                        "within_reference_rate": (count / ref_totals[ref]) if ref_totals.get(ref) else None,
                        "low_n": count < LOW_N_THRESHOLD,
                    }
                )
    return rows
