"""Task 2 (qualitative, n=4 families): on the exploratory items whose gold
shifted away from design, does the model's wrong answer land on the
*design* gold specifically -- suggesting it learned the particle's textbook
function rather than this context's actual (human-judged) reading?

Restricted to exploratory "ma" items with gold_shifted=True (derived from
frozen_exploratory.csv via sources.load_shifted_ma_items -- currently
F11/F12/F13/F33, design neutral -> empirical confirmation). F06 and F18 are
also exploratory "ma" items but their gold never shifted, so they can't
speak to whether a wrong answer is "the design gold specifically" -- design
and empirical gold are the same for them.
"""


def design_gold_following_table(main_rows: list[dict], shifted_ma_items: dict[str, str]) -> list[dict]:
    """`shifted_ma_items` = item_id -> design_gold_semantic (sources.load_shifted_ma_items).
    One row per model: among those items, how often did the model's parsed
    choice equal the *design* gold (not the empirical gold it's actually
    scored against)? parse_failed rows are excluded from both numerator and
    denominator (no choice to compare).
    """
    shifted_rows = [r for r in main_rows if r["item_id"] in shifted_ma_items and r["parse_failed"] != "True"]
    models = sorted({r["model"] for r in shifted_rows})

    table = []
    for model in models:
        model_rows = [r for r in shifted_rows if r["model"] == model]
        n = len(model_rows)
        n_matches_design = sum(
            1 for r in model_rows if r["parsed_choice_semantic"] == shifted_ma_items[r["item_id"]]
        )
        table.append(
            {
                "model": model,
                "n_shifted_items": n,
                "n_matches_design_gold": n_matches_design,
                "design_gold_following_rate": (n_matches_design / n) if n else None,
            }
        )
    return table
