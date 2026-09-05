# Context-only ablation summary -- confirmatory

60 items, 360 (item, model) query results. shortcut_risk threshold: ≥2/3 of models land on gold from context alone (no target sentence shown).

**Structural note (applies to every family, both sets):** by dataset design, context/question/options are identical across a family's bare/+ba/+ma conditions -- only the target sentence differs, and this ablation removes exactly that. So the ablation prompt for all three conditions of one family is byte-for-byte identical, and at temperature 0 a given model gives the *same* answer to all three. That answer can therefore match at most one of a KEEP family's three (necessarily distinct) gold labels -- shortcut_risk on more than one condition in the same confirmatory family is not possible by construction, not because the model resisted the shortcut on the others.

## shortcut_risk items: 11 / 60 (18.3%)

### By condition

| condition | n_items | n_shortcut_risk | shortcut_rate |
|---|---|---|---|
| bare | 20 | 0 | 0.0% |
| ba | 20 | 8 | 40.0% |
| ma | 20 | 3 | 15.0% |

### shortcut_risk item list

- F01 (ba)
- F04 (ba)
- F14 (ba)
- F15 (ma)
- F16 (ba)
- F20 (ba)
- F23 (ma)
- F24 (ba)
- F30 (ba)
- F34 (ba)
- F36 (ma)

### Parse failure rate: 45 / 360 query results (12.5%)
