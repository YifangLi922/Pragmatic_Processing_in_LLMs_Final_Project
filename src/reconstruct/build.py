"""Module 1: reconstruct the standard item+annotations structure (plan 4.3).

Joins the master answer-key table (master_table.load_master_table) with one
or more annotator tables (annotator_table.load_annotator_table) on
shuffled_index ("题号"), translates each annotator's answer_letter into
answer_semantic via the item's option_semantics, and emits one record per
item in the shape modules 2/3 already consume (see data/fake_annotations.json
and src/gold, src/agreement).

The master table only carries 句子 (sentence); 情景/问题 (context/question)
live on the annotator-facing sheets instead, so those are pulled from
whichever annotator table has them first, with a consistency check against
every other annotator's copy of the same fields (they're supposed to be
identical -- the master spreadsheet is shared verbatim, annotators only add
their own answers). Mismatches are reported as warnings rather than raised,
per the project's "record, don't crash" convention for data-quality issues.
"""

_CONDITION_ORDER = {"bare": 0, "ba": 1, "ma": 2}
_CONTENT_FIELDS = ("context", "sentence", "question")


def build_dataset(
    master_items: dict[str, dict], annotator_data: dict[str, dict[str, dict]]
) -> tuple[list[dict], list[str]]:
    """`annotator_data` = {annotator_id: {shuffled_index: record}}, i.e. the
    output of annotator_table.parse_annotator_rows per annotator.

    Returns (items, warnings). `items` is sorted by (family_id, condition)
    for readability; `warnings` collects every data-quality issue found
    along the way (missing rows, content mismatches, unmapped answer
    letters, malformed option sets) so nothing fails silently or crashes.
    """
    warnings = []
    items = []

    for shuffled_index, meta in master_items.items():
        content, content_warnings = _reconcile_content(shuffled_index, annotator_data)
        warnings.extend(content_warnings)
        if content is not None and content["sentence"] != meta["sentence"]:
            warnings.append(
                f"{shuffled_index}: sentence differs between master table and annotator sheet(s)"
            )

        annotations, annotation_warnings = _build_annotations(shuffled_index, meta, annotator_data)
        warnings.extend(annotation_warnings)
        warnings.extend(f"{shuffled_index}: {w}" for w in meta["option_semantics_warnings"])

        item_id = f"{meta['family_id']}_{meta['particle_condition']}"
        items.append(
            {
                "item_id": item_id,
                "family_id": meta["family_id"],
                "particle_condition": meta["particle_condition"],
                "shuffled_index": shuffled_index,
                "context": content["context"] if content else None,
                "sentence": meta["sentence"],
                "question": content["question"] if content else None,
                "options": meta["options"],
                "option_semantics": meta["option_semantics"],
                "gold_letter_designed": meta["gold_letter_designed"],
                "gold_semantic_designed": meta["option_semantics"].get(meta["gold_letter_designed"]),
                "source": meta["source"],
                "source_item_no": meta["source_item_no"],
                "annotations": annotations,
            }
        )

    items.sort(key=lambda it: (it["family_id"], _CONDITION_ORDER.get(it["particle_condition"], 99)))
    return items, warnings


def _reconcile_content(shuffled_index: str, annotator_data: dict) -> tuple[dict | None, list[str]]:
    warnings = []
    content = None
    for annotator_id, records in annotator_data.items():
        rec = records.get(shuffled_index)
        if rec is None:
            warnings.append(f"{shuffled_index}: missing from annotator '{annotator_id}'")
            continue
        if content is None:
            content = rec
            continue
        for field in _CONTENT_FIELDS:
            if rec[field] != content[field]:
                warnings.append(f"{shuffled_index}: '{field}' differs between annotators (e.g. '{annotator_id}')")
        if rec["options"] != content["options"]:
            warnings.append(f"{shuffled_index}: options differ between annotators (e.g. '{annotator_id}')")
    return content, warnings


def _build_annotations(shuffled_index: str, meta: dict, annotator_data: dict) -> tuple[list[dict], list[str]]:
    warnings = []
    annotations = []
    for annotator_id, records in annotator_data.items():
        rec = records.get(shuffled_index)
        if rec is None:
            continue
        letter = rec["answer_letter"]
        semantic = meta["option_semantics"].get(letter) if letter else None
        if letter and semantic is None:
            warnings.append(f"{shuffled_index}/{annotator_id}: answer letter {letter!r} not in this item's options")
        annotations.append(
            {
                "annotator_id": annotator_id,
                "answer_letter": letter,
                "answer_semantic": semantic,
                "naturalness": rec["naturalness"],
                "hesitation": rec["hesitation"],
                "hesitation_reason": rec["hesitation_reason"],
                "no_valid_option": rec["no_valid_option"],
                "no_valid_option_detail": rec["no_valid_option_detail"],
            }
        )
    return annotations, warnings
