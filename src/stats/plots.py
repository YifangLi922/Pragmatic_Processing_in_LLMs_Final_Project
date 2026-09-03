"""Module 6: the four required figures (plan section 5, Module 6):
confusion-matrix heatmap, condition-wise accuracy, family success, and
model-vs-human-baseline. Thin rendering layer over plot_data.py's pure data
shaping -- this file is the only place matplotlib gets imported.

Uses the non-interactive Agg backend since this runs headless (CI, a
container, or just a script), never a live display.
"""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402

from .plot_data import (  # noqa: E402
    condition_accuracy_series,
    confusion_heatmap_data,
    family_by_model_matrix,
    family_success_rate_series,
    model_vs_baseline_series,
)

_CONDITIONS = ("bare", "ba", "ma", "overall")


def plot_confusion_heatmap(confusion_matrix: dict, model_name: str, output_path: str) -> None:
    rows, cols, matrix = confusion_heatmap_data(confusion_matrix)
    fig, ax = plt.subplots(figsize=(6, 3.5))
    im = ax.imshow(matrix, cmap="Blues", aspect="auto")
    ax.set_xticks(range(len(cols)), labels=cols, rotation=30, ha="right")
    ax.set_yticks(range(len(rows)), labels=rows)
    ax.set_xlabel("model's answer (semantic)")
    ax.set_ylabel("particle condition")
    ax.set_title(f"Confusion matrix -- {model_name}")
    for i in range(len(rows)):
        for j in range(len(cols)):
            ax.text(j, i, matrix[i][j], ha="center", va="center",
                     color="white" if matrix[i][j] > (max(max(r) for r in matrix) or 1) / 2 else "black")
    fig.colorbar(im, ax=ax, label="count")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def plot_condition_accuracy(scorecards: dict, output_path: str) -> None:
    series = condition_accuracy_series(scorecards)
    model_names = sorted(series)
    n_models = len(model_names)
    x = range(len(_CONDITIONS))
    width = 0.8 / max(n_models, 1)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    for i, model_name in enumerate(model_names):
        accs, err_low, err_high = [], [], []
        for condition in _CONDITIONS:
            acc, ci_low, ci_high = series[model_name][condition]
            accs.append(acc if acc is not None else 0)
            # max(0, ...): Wilson's formula can land a hair outside [ci_low, acc]
            # from float rounding at the edges (e.g. acc exactly 1/3); a
            # negative error-bar length is never meaningful, so clamp it away.
            err_low.append(max(0.0, acc - ci_low) if (acc is not None and ci_low is not None) else 0)
            err_high.append(max(0.0, ci_high - acc) if (acc is not None and ci_high is not None) else 0)
        positions = [xi + i * width for xi in x]
        ax.bar(positions, accs, width=width, label=model_name, yerr=[err_low, err_high], capsize=2)

    ax.axhline(0.25, color="gray", linestyle="--", linewidth=1, label="chance (0.25)")
    ax.set_xticks([xi + width * (n_models - 1) / 2 for xi in x], labels=_CONDITIONS)
    ax.set_ylabel("accuracy")
    ax.set_ylim(0, 1)
    ax.set_title("Condition accuracy by model (error bars: Wilson 95% CI)")
    ax.legend(fontsize=8, ncol=2)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def plot_family_success(scorecards: dict, output_path: str) -> None:
    rates = family_success_rate_series(scorecards)
    model_names = sorted(rates)
    values = [rates[m] if rates[m] is not None else 0 for m in model_names]

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(model_names, values)
    ax.axhline(0.015625, color="gray", linestyle="--", linewidth=1, label="chance (1/64)")
    ax.set_ylabel("family success rate")
    ax.set_ylim(0, 1)
    ax.set_title("Family success rate by model (all three conditions correct)")
    ax.tick_params(axis="x", rotation=30)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def plot_family_by_model_heatmap(scorecards: dict, output_path: str) -> None:
    family_ids, model_names, matrix = family_by_model_matrix(scorecards)
    fig, ax = plt.subplots(figsize=(max(6, len(model_names) * 1.2), max(4, len(family_ids) * 0.25)))
    im = ax.imshow(matrix, cmap="RdYlGn", vmin=-1, vmax=1, aspect="auto")
    ax.set_xticks(range(len(model_names)), labels=model_names, rotation=30, ha="right")
    ax.set_yticks(range(len(family_ids)), labels=family_ids, fontsize=6)
    ax.set_title("Family success by model (green=success, red=failed, gray=no data)")
    fig.colorbar(im, ax=ax, ticks=[-1, 0, 1], label="-1 no data / 0 failed / 1 success")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def plot_model_vs_baseline(scorecards: dict, human_baseline: dict, output_path: str) -> None:
    series = model_vs_baseline_series(scorecards, human_baseline)
    series_names = sorted(k for k in series if k != "human_baseline") + ["human_baseline"]
    x = range(len(_CONDITIONS))
    width = 0.8 / max(len(series_names), 1)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    for i, name in enumerate(series_names):
        values = [series[name].get(cond) or 0 for cond in _CONDITIONS]
        positions = [xi + i * width for xi in x]
        style = {"color": "black", "hatch": "//"} if name == "human_baseline" else {}
        ax.bar(positions, values, width=width, label=name, **style)

    ax.set_xticks([xi + width * (len(series_names) - 1) / 2 for xi in x], labels=_CONDITIONS)
    ax.set_ylabel("accuracy")
    ax.set_ylim(0, 1)
    ax.set_title("Model accuracy vs. LOO human baseline")
    ax.legend(fontsize=8, ncol=2)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
