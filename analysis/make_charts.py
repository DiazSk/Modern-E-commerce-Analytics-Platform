"""Render the memo's two charts from analysis/results/*.csv.

Each chart is one series: the estimated difference per category with its 95%
CI. A filled dot means the CI excludes zero; a hollow dot means no detectable
change. Shape carries that distinction, so the chart doesn't rely on color.
"""

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

HERE = Path(__file__).resolve().parent

# Reference palette (dataviz skill, references/palette.md), light mode.
SURFACE = "#fcfcfb"
SERIES = "#2a78d6"
WHISKER = "#86b6ef"  # sequential step 250: lightest step that clears 2:1
TEXT = "#0b0b0b"
TEXT_2 = "#52514e"
RULE = "#c3c2b7"


def read(name: str) -> list[dict]:
    with (HERE / "results" / f"{name}.csv").open() as f:
        return list(csv.DictReader(f))


def diff_chart(rows, title, subtitle, xlabel, out):
    rows = sorted(rows, key=lambda r: float(r["diff"]))
    y = range(len(rows))
    diff = [100 * float(r["diff"]) for r in rows]
    low = [100 * float(r["ci_low"]) for r in rows]
    high = [100 * float(r["ci_high"]) for r in rows]
    clear = [lo > 0 or hi < 0 for lo, hi in zip(low, high)]

    fig, ax = plt.subplots(figsize=(8, 0.42 * len(rows) + 1.9), facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    ax.axvline(0, color=RULE, linewidth=1, zorder=1)
    ax.hlines(y, low, high, color=WHISKER, linewidth=2, zorder=2)
    for yi, d, c in zip(y, diff, clear):
        ax.plot(
            d,
            yi,
            "o",
            markersize=8,
            zorder=3,
            markeredgewidth=2,
            markeredgecolor=SERIES,
            markerfacecolor=SERIES if c else SURFACE,
        )
    for yi, d, h in zip(y, diff, high):
        ax.annotate(
            f"{d:+.1f}",
            (h, yi),
            xytext=(9, 0),
            textcoords="offset points",
            va="center",
            fontsize=8,
            color=TEXT_2,
        )

    ax.set_yticks(list(y), [r["category_l1"] for r in rows], color=TEXT, fontsize=9)
    ax.tick_params(axis="x", colors=TEXT_2, labelsize=8)
    ax.tick_params(axis="y", length=0)
    ax.set_xlabel(xlabel, color=TEXT_2, fontsize=9)
    ax.grid(axis="x", color=RULE, linewidth=0.5, alpha=0.6)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(RULE)
    ax.margins(x=0.12)

    legend = [
        Line2D(
            [],
            [],
            marker="o",
            linestyle="",
            markersize=7,
            markeredgewidth=2,
            markeredgecolor=SERIES,
            markerfacecolor=SERIES,
            label="95% CI excludes 0",
        ),
        Line2D(
            [],
            [],
            marker="o",
            linestyle="",
            markersize=7,
            markeredgewidth=2,
            markeredgecolor=SERIES,
            markerfacecolor=SURFACE,
            label="No detectable change",
        ),
    ]
    ax.legend(
        handles=legend, loc="lower right", frameon=False, fontsize=8, labelcolor=TEXT_2
    )
    head = 0.9 / fig.get_figheight()  # keep ~0.9in for the title block
    fig.tight_layout(rect=(0, 0, 1, 1 - head))
    fig.text(
        0.02,
        1 - 0.3 * head,
        title,
        ha="left",
        va="center",
        fontsize=11.5,
        fontweight="bold",
        color=TEXT,
    )
    fig.text(
        0.02,
        1 - 0.72 * head,
        subtitle,
        ha="left",
        va="center",
        fontsize=9,
        color=TEXT_2,
    )
    (HERE / "charts").mkdir(exist_ok=True)
    fig.savefig(HERE / "charts" / out, dpi=160, facecolor=SURFACE)
    plt.close(fig)
    print(f"analysis/charts/{out}")


def main() -> None:
    diff_chart(
        read("q1_category_black_friday"),
        "Black Friday week barely moved purchase rates",
        "Change vs the prior 4 weeks, by category · session × category · 95% CI",
        "Difference in purchase rate (percentage points)",
        "q1_purchase_rate_black_friday.png",
    )
    diff_chart(
        read("q2_band_contrast"),
        "Pricier items aren't consistently abandoned more",
        "Abandonment, top price quartile minus bottom, within each category · 95% CI",
        "Top-quartile minus bottom-quartile abandonment (percentage points)",
        "q2_abandonment_price_band.png",
    )


if __name__ == "__main__":
    main()
