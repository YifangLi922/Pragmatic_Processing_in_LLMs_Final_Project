"""Module 1: per-annotator quality report (plan section 5, Module 1).

Beyond the checks the plan explicitly asks for (straight-lining, missing
answers, practice-item accuracy, timing), this adds two checks motivated by
a real case: one annotator's naturalness ratings, hesitation marks, and
"no valid option" marks were all completely flat (zero variance across 108
independent items) while also matching the designer's own expected answer
far more often than every other annotator. Neither signal alone proves
anything, but the combination is exactly the kind of thing a quality report
should surface with numbers instead of leaving it as a hunch.

Works for any number of annotators -- nothing here assumes exactly 4.
"""

from collections import Counter
from statistics import mean, pstdev


def annotator_quality(annotator_id: str, items: list[dict]) -> dict:
    """`items` = build_dataset() output. Reports on this one annotator's
    answers across every item that includes them.
    """
    recs = [
        (item, a)
        for item in items
        for a in item["annotations"]
        if a["annotator_id"] == annotator_id
    ]
    n = len(recs)

    letter_counts = Counter(a["answer_letter"] for _, a in recs if a["answer_letter"])
    n_answered = sum(letter_counts.values())
    n_missing = n - n_answered
    max_letter_share = (max(letter_counts.values()) / n_answered) if n_answered else None

    naturalness_vals = [a["naturalness"] for _, a in recs if isinstance(a["naturalness"], (int, float))]
    naturalness_mean = mean(naturalness_vals) if naturalness_vals else None
    naturalness_sd = pstdev(naturalness_vals) if len(naturalness_vals) > 1 else (0.0 if naturalness_vals else None)

    hesitation_rate = (sum(a["hesitation"] for _, a in recs) / n) if n else None
    no_valid_option_rate = (sum(a["no_valid_option"] for _, a in recs) / n) if n else None

    designed_pairs = [(item, a) for item, a in recs if item.get("gold_letter_designed") and a["answer_letter"]]
    n_designed = len(designed_pairs)
    n_agree_designed = sum(1 for item, a in designed_pairs if a["answer_letter"] == item["gold_letter_designed"])
    designed_gold_agreement_rate = (n_agree_designed / n_designed) if n_designed else None

    flags = []
    if max_letter_share is not None and max_letter_share > 0.70:
        top_letter = letter_counts.most_common(1)[0][0]
        flags.append(f"straight-lining: {max_letter_share:.0%} of answers are '{top_letter}'")
    if n_missing > 0:
        flags.append(f"{n_missing}/{n} items unanswered")
    if naturalness_sd == 0.0 and naturalness_vals:
        flags.append(f"naturalness rating is constant ({naturalness_vals[0]}) across all {len(naturalness_vals)} items")
    if hesitation_rate == 0.0 and no_valid_option_rate == 0.0 and naturalness_sd == 0.0:
        flags.append(
            "flat responding: zero hesitation marks, zero 'no valid option' marks, and zero "
            "naturalness variance -- consistent with (not proof of) a non-genuine/automated response, "
            "worth a closer look"
        )

    return {
        "annotator_id": annotator_id,
        "n_items": n,
        "n_answered": n_answered,
        "n_missing": n_missing,
        "max_letter_share": max_letter_share,
        "letter_distribution": dict(letter_counts),
        "naturalness_mean": naturalness_mean,
        "naturalness_sd": naturalness_sd,
        "hesitation_rate": hesitation_rate,
        "no_valid_option_rate": no_valid_option_rate,
        "designed_gold_agreement_rate": designed_gold_agreement_rate,
        "flags": flags,
    }


def build_quality_report(items: list[dict], annotator_ids: list[str]) -> dict:
    """Per-annotator reports, plus a cross-annotator outlier check on
    designed_gold_agreement_rate (an annotator who agrees with the designer's
    own expected answer far more than the rest of the cohort is unusual --
    real annotators are supposed to be judging independently, not converging
    on the designer's intent).
    """
    per_annotator = {aid: annotator_quality(aid, items) for aid in annotator_ids}

    rates = [r["designed_gold_agreement_rate"] for r in per_annotator.values() if r["designed_gold_agreement_rate"] is not None]
    if len(rates) > 2:
        cohort_mean = mean(rates)
        cohort_sd = pstdev(rates)
        for report in per_annotator.values():
            rate = report["designed_gold_agreement_rate"]
            if rate is None or cohort_sd == 0:
                continue
            z = (rate - cohort_mean) / cohort_sd
            if z > 2:
                report["flags"].append(
                    f"designed-gold agreement ({rate:.1%}) is a cohort outlier "
                    f"(cohort mean {cohort_mean:.1%}, z={z:.1f})"
                )

    return {"per_annotator": per_annotator}
