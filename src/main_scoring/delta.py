"""Task 3: per-(model, item) with-vs-without-target delta.

used_target = the model's parsed choice differs between main (target
sentence shown) and the context-only ablation (no sentence). Denominator is
restricted to rows where main's parse_failed=False (main is what's being
scored); ablation's choice can be a real letter or None (ablation failed to
parse -- itself informative, see below) -- either way "differs from main's
real answer" is used_target=True, computed as a plain inequality so None
compares correctly with no special-casing.

Two sub-flavors of used_target=True are tracked separately for
transparency: the ablation gave a *different real answer* (genuine opinion
change) vs. the ablation *failed to parse at all* (e.g. gemma-4-31b
frequently refused to guess without the sentence) -- the second isn't
evidence the model "used" the sentence in a rich sense, just that it went
from refusing to answering, and the two should not be silently conflated
when reading the used_target rate.
"""


def build_delta_rows(main_rows: list[dict], ablation_rows: list[dict], set_name: str) -> list[dict]:
    """One row per (model, item) with main parse_failed=False, restricted to
    `set_name`. Assumes sources.check_preconditions() has already passed.
    """
    ablation_choice = {
        (r["model"], r["item_id"]): (r["parsed_choice_letter"] or None) for r in ablation_rows if r["set"] == set_name
    }

    rows = []
    for r in main_rows:
        if r["set"] != set_name or r["parse_failed"] == "True":
            continue
        main_choice = r["parsed_choice_letter"]
        key = (r["model"], r["item_id"])
        abl_choice = ablation_choice.get(key)
        used_target = main_choice != abl_choice
        rows.append(
            {
                "model": r["model"],
                "family_id": r["family_id"],
                "item_id": r["item_id"],
                "condition": r["condition"],
                "main_choice": main_choice,
                "ablation_choice": abl_choice,
                "ablation_parse_failed": abl_choice is None,
                "used_target": used_target,
                "hit_gold": r["hit_gold"] == "True",
            }
        )
    return rows


def _accuracy(rows: list[dict]) -> tuple[int, float | None]:
    n = len(rows)
    if n == 0:
        return 0, None
    return n, sum(1 for r in rows if r["hit_gold"]) / n


def used_target_summary(delta_rows: list[dict]) -> list[dict]:
    """One row per model: used_target rate, split into the two sub-flavors."""
    models = sorted({r["model"] for r in delta_rows})
    table = []
    for model in models:
        model_rows = [r for r in delta_rows if r["model"] == model]
        n_valid = len(model_rows)
        used = [r for r in model_rows if r["used_target"]]
        used_due_to_ablation_parse_failure = sum(1 for r in used if r["ablation_parse_failed"])
        used_with_real_alternative = len(used) - used_due_to_ablation_parse_failure
        table.append(
            {
                "model": model,
                "n_valid_pairs": n_valid,
                "n_used_target": len(used),
                "used_target_rate": (len(used) / n_valid) if n_valid else None,
                "n_used_target_ablation_parse_failed": used_due_to_ablation_parse_failure,
                "n_used_target_real_alternative": used_with_real_alternative,
            }
        )
    return table


def purified_accuracy_comparison(
    delta_rows: list[dict], raw_accuracy_by_model: dict[str, tuple[int, float | None]], shortcut_families: set[str] | None
) -> list[dict]:
    """model, raw accuracy (all valid rows, from task 1), purified accuracy
    (used_target=True subset), and -- only when `shortcut_families` is given
    (confirmatory only) -- a sensitivity accuracy that additionally drops
    items whose family showed shortcut_risk=True in the ablation.
    """
    models = sorted({r["model"] for r in delta_rows})
    table = []
    for model in models:
        model_rows = [r for r in delta_rows if r["model"] == model]
        purified_rows = [r for r in model_rows if r["used_target"]]
        n_purified, acc_purified = _accuracy(purified_rows)

        n_raw, acc_raw = raw_accuracy_by_model.get(model, (0, None))

        row = {
            "model": model,
            "n_valid_raw": n_raw,
            "accuracy_raw": acc_raw,
            "n_valid_purified": n_purified,
            "accuracy_purified": acc_purified,
        }

        if shortcut_families is not None:
            sensitivity_rows = [r for r in purified_rows if r["family_id"] not in shortcut_families]
            n_sens, acc_sens = _accuracy(sensitivity_rows)
            row["n_valid_sensitivity"] = n_sens
            row["accuracy_sensitivity"] = acc_sens
        else:
            row["n_valid_sensitivity"] = None
            row["accuracy_sensitivity"] = None

        table.append(row)
    return table
