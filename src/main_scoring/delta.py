"""Task 3: per-(model, item) with-vs-without-target delta.

used_target = the model's parsed choice differs between main (target
sentence shown) and the context-only ablation (no sentence).

Denominator is pairs where BOTH main and ablation successfully parsed an
answer. A missing ablation answer (the model refused to guess without the
sentence -- gemma-4-31b did this on 35/60 confirmatory items, mistral-small
on 9/60) is NOT evidence of anything about used_target: "went from refusing
to answering" is a different, undefined comparison from "changed its
answer", and counting it as used_target=True (an earlier version of this
analysis did) inflates the rate for exactly the models that refuse most
often. Excluded pairs are counted separately (see
count_missing_ablation_answer) so the exclusion itself stays visible rather
than silently shrinking n.
"""


def _ablation_choice_lookup(ablation_rows: list[dict], set_name: str) -> dict[tuple[str, str], str]:
    """(model, item_id) -> parsed_choice_letter, ablation rows that
    successfully parsed only (set_name-restricted).
    """
    return {
        (r["model"], r["item_id"]): r["parsed_choice_letter"]
        for r in ablation_rows
        if r["set"] == set_name and r["parsed_choice_letter"]
    }


def build_delta_rows(main_rows: list[dict], ablation_rows: list[dict], set_name: str) -> list[dict]:
    """One row per (model, item) where main parse_failed=False AND the
    ablation has a real (parsed) answer to compare against. Restricted to
    `set_name`. Assumes sources.check_preconditions() has already passed.
    """
    ablation_choice = _ablation_choice_lookup(ablation_rows, set_name)

    rows = []
    for r in main_rows:
        if r["set"] != set_name or r["parse_failed"] == "True":
            continue
        key = (r["model"], r["item_id"])
        if key not in ablation_choice:
            continue
        main_choice = r["parsed_choice_letter"]
        abl_choice = ablation_choice[key]
        rows.append(
            {
                "model": r["model"],
                "family_id": r["family_id"],
                "item_id": r["item_id"],
                "condition": r["condition"],
                "main_choice": main_choice,
                "ablation_choice": abl_choice,
                "used_target": main_choice != abl_choice,
                "hit_gold": r["hit_gold"] == "True",
                "gold_letter": r["gold_letter"],
                "ablation_hit_gold": abl_choice == r["gold_letter"],
            }
        )
    return rows


def count_missing_ablation_answer(main_rows: list[dict], ablation_rows: list[dict], set_name: str) -> dict[str, int]:
    """Per model: how many (main parse-succeeded) items were dropped from
    the used_target denominator because the ablation never produced a
    parseable answer for that item. Reported alongside used_target so the
    comparable base (and how much of the roster it excludes) stays visible.
    """
    ablation_choice = _ablation_choice_lookup(ablation_rows, set_name)
    counts: dict[str, int] = {}
    for r in main_rows:
        if r["set"] != set_name or r["parse_failed"] == "True":
            continue
        counts.setdefault(r["model"], 0)
        if (r["model"], r["item_id"]) not in ablation_choice:
            counts[r["model"]] += 1
    return counts


def _accuracy(rows: list[dict]) -> tuple[int, float | None]:
    n = len(rows)
    if n == 0:
        return 0, None
    return n, sum(1 for r in rows if r["hit_gold"]) / n


def used_target_summary(delta_rows: list[dict], missing_ablation_counts: dict[str, int]) -> list[dict]:
    """One row per model: used_target rate over the both-answered base,
    plus how many items that model's row excludes from that base because
    the ablation gave no answer to compare against.
    """
    models = sorted({r["model"] for r in delta_rows} | set(missing_ablation_counts))
    table = []
    for model in models:
        model_rows = [r for r in delta_rows if r["model"] == model]
        n_valid = len(model_rows)
        n_used = sum(1 for r in model_rows if r["used_target"])
        table.append(
            {
                "model": model,
                "n_valid_pairs": n_valid,
                "n_used_target": n_used,
                "used_target_rate": (n_used / n_valid) if n_valid else None,
                "n_excluded_no_ablation_answer": missing_ablation_counts.get(model, 0),
            }
        )
    return table


def prior_correction_table(delta_rows: list[dict]) -> list[dict]:
    """Task 3c: within each (model, condition)'s both-answered items, split
    by whether the *ablation* (no target sentence) answer already equaled
    gold -- prior_correct vs. prior_incorrect -- and report each group's own
    main-experiment (with target sentence shown) accuracy and n.

    Raw condition accuracy conflates two different things: "the model was
    already right without the sentence" and "the model was wrong and the
    sentence corrected it". Only the prior_incorrect group's accuracy
    answers the second question -- that's the number to quote as "ability
    to use the target sentence to fix a wrong judgment", not the overall
    condition accuracy. A condition accuracy nominally above the human
    baseline can still turn out to rest almost entirely on prior_correct
    items, with too few prior_incorrect items to say anything about
    genuine correction (small-n, not a claim of "the model beats humans").
    """
    keys = sorted({(r["model"], r["condition"]) for r in delta_rows})
    table = []
    for model, condition in keys:
        cell_rows = [r for r in delta_rows if r["model"] == model and r["condition"] == condition]
        for group_name, group_flag in (("prior_correct", True), ("prior_incorrect", False)):
            group_rows = [r for r in cell_rows if r["ablation_hit_gold"] == group_flag]
            n = len(group_rows)
            accuracy = (sum(1 for r in group_rows if r["hit_gold"]) / n) if n else None
            table.append(
                {
                    "model": model,
                    "condition": condition,
                    "group": group_name,
                    "n_items": n,
                    "accuracy": accuracy,
                }
            )
    return table


def used_target_summary_by_condition(delta_rows: list[dict], missing_ablation_counts_by_condition: dict[tuple[str, str], int]) -> list[dict]:
    """Same as used_target_summary but one row per (model, condition).
    `missing_ablation_counts_by_condition` keys are (model, condition).
    """
    keys = sorted({(r["model"], r["condition"]) for r in delta_rows} | set(missing_ablation_counts_by_condition))
    table = []
    for model, condition in keys:
        model_rows = [r for r in delta_rows if r["model"] == model and r["condition"] == condition]
        n_valid = len(model_rows)
        n_used = sum(1 for r in model_rows if r["used_target"])
        table.append(
            {
                "model": model,
                "condition": condition,
                "n_valid_pairs": n_valid,
                "n_used_target": n_used,
                "used_target_rate": (n_used / n_valid) if n_valid else None,
                "n_excluded_no_ablation_answer": missing_ablation_counts_by_condition.get((model, condition), 0),
            }
        )
    return table


def count_missing_ablation_answer_by_condition(
    main_rows: list[dict], ablation_rows: list[dict], set_name: str
) -> dict[tuple[str, str], int]:
    """Same as count_missing_ablation_answer but keyed by (model, condition)."""
    ablation_choice = _ablation_choice_lookup(ablation_rows, set_name)
    counts: dict[tuple[str, str], int] = {}
    for r in main_rows:
        if r["set"] != set_name or r["parse_failed"] == "True":
            continue
        key = (r["model"], r["condition"])
        counts.setdefault(key, 0)
        if (r["model"], r["item_id"]) not in ablation_choice:
            counts[key] += 1
    return counts


def update_precision_by_condition(delta_rows: list[dict], raw_accuracy_by_model_condition: dict[tuple[str, str], tuple[int, float | None]]) -> list[dict]:
    """Same as update_precision_comparison but one row per (model,
    condition), no sensitivity column (that's a family-level, confirmatory-
    only cut and doesn't split cleanly by condition).
    """
    keys = sorted({(r["model"], r["condition"]) for r in delta_rows})
    table = []
    for model, condition in keys:
        model_rows = [r for r in delta_rows if r["model"] == model and r["condition"] == condition]
        updated_rows = [r for r in model_rows if r["used_target"]]
        n_updates, update_precision = _accuracy(updated_rows)

        n_raw, acc_raw = raw_accuracy_by_model_condition.get((model, condition), (0, None))

        table.append(
            {
                "model": model,
                "condition": condition,
                "n_valid_raw": n_raw,
                "accuracy_raw": acc_raw,
                "n_updates": n_updates,
                "update_precision": update_precision,
            }
        )
    return table


def update_precision_comparison(
    delta_rows: list[dict], raw_accuracy_by_model: dict[str, tuple[int, float | None]], shortcut_families: set[str] | None
) -> list[dict]:
    """model, raw accuracy (all valid rows, from task 1) alongside
    update_precision: accuracy *only on the items where the model changed
    its answer once shown the target sentence* (used_target=True). This is
    not a "corrected" or cleaner version of raw accuracy -- it answers a
    different question ("when the model updates on the sentence, is the
    update usually right?") and must be read side by side with raw
    accuracy, never as a replacement for it.

    When `shortcut_families` is given (confirmatory only), an additional
    update_precision_sensitivity column further drops items whose family
    showed shortcut_risk=True in the ablation.
    """
    models = sorted({r["model"] for r in delta_rows})
    table = []
    for model in models:
        model_rows = [r for r in delta_rows if r["model"] == model]
        updated_rows = [r for r in model_rows if r["used_target"]]
        n_updates, update_precision = _accuracy(updated_rows)

        n_raw, acc_raw = raw_accuracy_by_model.get(model, (0, None))

        row = {
            "model": model,
            "n_valid_raw": n_raw,
            "accuracy_raw": acc_raw,
            "n_updates": n_updates,
            "update_precision": update_precision,
        }

        if shortcut_families is not None:
            sensitivity_rows = [r for r in updated_rows if r["family_id"] not in shortcut_families]
            n_sens, precision_sens = _accuracy(sensitivity_rows)
            row["n_updates_sensitivity"] = n_sens
            row["update_precision_sensitivity"] = precision_sens
        else:
            row["n_updates_sensitivity"] = None
            row["update_precision_sensitivity"] = None

        table.append(row)
    return table
