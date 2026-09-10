# Human baseline: LOO vs. concordance

Two human baselines on the same frozen 20 confirmatory families, answering different questions -- read side by side, not as duplicates:

- **human_LOO** (leave-one-annotator-out): for each held-out core3 annotator, the majority of the *other two* becomes that fold's temporary gold, and the held-out person is scored against it; folds are averaged. On a 2:1 split, whichever annotator is in the minority is *always* scored as a miss for that fold -- LOO structurally cannot credit a minority vote, even when it happens to match the real gold.
- **human_concordance**: for each item, the fraction of all three core3 annotators whose answer matches the actual gold, averaged within condition. This asks the same question model accuracy does ("what fraction of answerers picked gold?") on every item, including 2:1 splits -- it is the metric directly comparable to model accuracy, and the primary human reference point.

| condition | human_LOO | human_concordance |
|---|---|---|
| overall | 85.0% (3/3 folds) | 87.8% (60 items) |
| bare | 98.3% (3/3 folds) | 98.3% (20 items) |
| ba | 66.6% (3/3 folds) | 78.3% (20 items) |
| ma | 83.9% (3/3 folds) | 86.7% (20 items) |
