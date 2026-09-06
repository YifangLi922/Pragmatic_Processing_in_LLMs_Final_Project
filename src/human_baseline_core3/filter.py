"""Build the restricted item list loo_human_baseline() needs: only the
frozen KEEP families, only core3 annotations per item.
"""

CORE3 = ("Media", "Materials", "EngLit")


def load_keep_family_ids(frozen_dataset_csv_rows: list[dict]) -> set[str]:
    return {row["family_id"] for row in frozen_dataset_csv_rows}


def restrict_to_core3_keep_families(reconstructed_items: list[dict], keep_family_ids: set[str]) -> list[dict]:
    """`reconstructed_items` = data/reconstructed_5ann.json. Returns items
    for the keep families only, each with its `annotations` list filtered
    down to core3 (Econ and BWL dropped) so loo_human_baseline's
    auto-detected annotator set is exactly {Media, Materials, EngLit}.
    """
    restricted = []
    for item in reconstructed_items:
        if item["family_id"] not in keep_family_ids:
            continue
        core3_annotations = [a for a in item["annotations"] if a["annotator_id"] in CORE3]
        restricted.append({**item, "annotations": core3_annotations})
    return restricted
