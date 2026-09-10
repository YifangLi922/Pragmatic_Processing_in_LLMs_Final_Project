# Context-only ablation summary -- exploratory

18 items, 108 (item, model) query results. shortcut_risk threshold: ≥2/3 of models land on gold from context alone (no target sentence shown).

**Structural note (applies to every family, both sets):** by dataset design, context/question/options are identical across a family's bare/+ba/+ma conditions -- only the target sentence differs, and this ablation removes exactly that. So the ablation prompt for all three conditions of one family is byte-for-byte identical, and at temperature 0 a given model gives the *same* answer to all three. That answer can therefore match at most one of a KEEP family's three (necessarily distinct) gold labels -- shortcut_risk on more than one condition in the same confirmatory family is not possible by construction, not because the model resisted the shortcut on the others.

**Not comparable to the confirmatory numbers below at face value.** Every exploratory family has two conditions whose human reference-pool majority already collapsed onto the same label (that's why it's here and not in frozen_dataset.csv). Because those two conditions share a prompt (see the structural note above) and therefore get the same model answer, that one answer can trigger shortcut_risk on *both* of them simultaneously if it happens to equal the shared gold -- something structurally impossible in a confirmatory family. A higher shortcut rate here is expected baseline behavior, not evidence of a worse ablation result.

## shortcut_risk items: 2 / 18 (11.1%)

### By condition

| condition | n_items | n_shortcut_risk | shortcut_rate |
|---|---|---|---|
| bare | 6 | 0 | 0.0% |
| ba | 6 | 1 | 16.7% |
| ma | 6 | 1 | 16.7% |

### shortcut_risk item list

- F11 (ba)
- F11 (ma)

### Parse failure rate: 15 / 108 query results (13.9%)

## Collapse-pair modal-choice check

For each collapsed family, whether the ablation's modal (most common) choice agrees between the two conditions whose human reference-pool majority collapsed onto the same label. **Read this as a consistency check, not independent confirmation the model 'reproduces' the human collapse:** per the structural note above, the two collapsing conditions share an identical context-only prompt, so any single model is expected to answer them identically regardless of collapse -- `same_modal=True` across the board is the mechanically expected outcome, not a discovery. A `False` here is the informative direction: it would mean a model's answer actually varied on two prompts that were byte-for-byte identical, which (temperature 0 aside) would point to API-level nondeterminism worth checking.

| family_id | collapse_pair | collapse_label | cond1_modal | cond2_modal | same_modal |
|---|---|---|---|---|---|
| F06 | bare=ba | statement | C | C | True |
| F11 | ba=ma | confirmation | C | C | True |
| F12 | ba=ma | confirmation | C | B | False |
| F13 | ba=ma | confirmation | A | A | True |
| F18 | ba=ma | neutral | B | B | True |
| F33 | bare=ba | statement | C | C | True |

5 / 6 collapsed families show the same modal choice on both conditions.
