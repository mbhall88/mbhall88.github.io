"""Schematic of how a repeat turns a true SNP into a het call (Figure 2 of the post).

Not drawn from data: the read counts are illustrative, matching what we saw on the E. coli
sample (ATCC_25922, hac 50x), where 60-85% of reads at Clair3's missed SNPs carried the ALT.

    python het-call-diagram.py   # writes het-call-repeat.png next to this script
"""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

COPY1, COPY2 = "#56B4E9", "#CC79A7"  # repeat copies, and the reads that come from them
ALT, REF = "#009E73", "#D55E00"  # bases at the SNP
GREY, DARK = "#9a9a9a", "#333333"
MONO = "DejaVu Sans Mono"

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "svg.fonttype": "none"})
fig, ax = plt.subplots(figsize=(10, 5.4))
ax.set_xlim(0, 100)
ax.set_ylim(0, 54)
ax.axis("off")


def panel_label(x, y, text):
    ax.text(x, y, text, fontsize=13, fontweight="bold", va="top")


# a: the genome, with two copies of a repeat; the SNP is in copy 1 only.
panel_label(0.5, 53.5, "a")
ax.plot([4, 96], [46, 46], color=GREY, lw=3, solid_capstyle="round", zorder=1)
for x0, colour, name, base, base_colour in [
    (20, COPY1, "repeat copy 1", "T", ALT),
    (64, COPY2, "repeat copy 2", "C", REF),
]:
    ax.add_patch(Rectangle((x0, 44.6), 16, 2.8, fc=colour, ec=colour, alpha=0.45, zorder=2))
    ax.text(x0 + 8, 49.4, name, ha="center", va="bottom")
    ax.plot([x0 + 8, x0 + 8], [44.6, 47.4], color=base_colour, lw=2, zorder=3)
    ax.text(x0 + 8, 43.6, base, ha="center", va="top", color=base_colour, fontweight="bold",
            fontfamily=MONO, fontsize=11)  # fmt: skip
ax.text(4, 47.6, "sequenced genome", ha="left", va="bottom", color=DARK, fontsize=9)
ax.text(50, 47.6, "7.5 kb copies, 96.5% identical", ha="center", va="bottom", color=DARK, fontsize=9)
ax.add_patch(FancyArrowPatch(
    (70.5, 41.2), (29.5, 41.2), connectionstyle="arc3,rad=-0.18", arrowstyle="-|>",
    mutation_scale=14, color=COPY2, lw=1.6, ls=(0, (4, 2)),
))  # fmt: skip
ax.text(50, 35.6, "some reads from copy 2 align to copy 1", ha="center", va="top", color=DARK,
        fontsize=9)  # fmt: skip

# b: the pileup at the SNP in copy 1. Reads from copy 2 carry the reference base.
panel_label(0.5, 32.5, "b")
ref_seq = "AGTCCAGCTAGGA"
snp = 6
xs = [9 + 2.9 * i for i in range(len(ref_seq))]
ax.add_patch(Rectangle((xs[snp] - 1.3, 3.4), 2.6, 27.4, fc="#fff3c4", ec="none", zorder=0))
ax.text(xs[0] - 2.2, 29.4, "reference", ha="right", va="center", color=DARK, fontsize=9)
for i, (x, b) in enumerate(zip(xs, ref_seq)):
    ax.text(x, 29.4, "C" if i == snp else b, ha="center", va="center", fontfamily=MONO,
            color=REF if i == snp else GREY, fontweight="bold" if i == snp else "normal")  # fmt: skip
reads = [  # (start, end) in reference positions, and which copy the read came from
    (0, 12, 1), (2, 12, 1), (0, 9, 2), (3, 12, 1), (1, 10, 1),
    (4, 12, 2), (0, 8, 1), (2, 11, 1), (1, 12, 2), (3, 10, 1),
]  # fmt: skip
for k, (start, end, copy) in enumerate(reads):
    y = 26.2 - k * 2.35
    colour = COPY1 if copy == 1 else COPY2
    ax.add_patch(FancyBboxPatch(
        (xs[start] - 1.1, y - 0.75), xs[end] - xs[start] + 2.2, 1.5,
        boxstyle="round,pad=0,rounding_size=0.6", fc=colour, ec="none", alpha=0.45,
    ))  # fmt: skip
    base, base_colour = ("T", ALT) if copy == 1 else ("C", REF)
    ax.text(xs[snp], y, base, ha="center", va="center", fontfamily=MONO, fontweight="bold",
            color=base_colour)  # fmt: skip
ax.text(xs[snp], 1.4, "ALT T on 7 reads, REF C on 3:  AF = 0.70", ha="center", va="center",
        color=DARK, fontsize=9)  # fmt: skip
handles = [
    Rectangle((0, 0), 1, 1, fc=COPY1, alpha=0.45, label="read from copy 1"),
    Rectangle((0, 0), 1, 1, fc=COPY2, alpha=0.45, label="read from copy 2"),
]
ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.03, 0.78), frameon=False,
          fontsize=9, handlelength=1.6)  # fmt: skip

# c: what Clair3's haploid modes, and the AF filter, make of the call.
panel_label(51, 32.5, "c")
ax.add_patch(FancyBboxPatch((55, 25.2), 40, 5.6, boxstyle="round,pad=0,rounding_size=0.8",
                            fc="#f2f2f2", ec=GREY))  # fmt: skip
ax.text(75, 28, "Clair3's diploid call: 0/1, ALT AF 0.70", ha="center", va="center")
ax.plot([57.5, 57.5], [25.2, 7.6], color=GREY, lw=1.2)
rows = [
    ("--haploid_precise", "✗", REF, "het dropped: SNP missed"),
    ("--haploid_sensitive", "✓", ALT, "het kept: ALT called"),
    ("AF filter (AF ≥ 0.65)", "✓", ALT, "0.70 ≥ 0.65: ALT called"),
]
for k, (mode, mark, colour, outcome) in enumerate(rows):
    y = 22 - k * 7.2
    ax.add_patch(FancyArrowPatch((57.5, y), (60, y), arrowstyle="-|>", mutation_scale=10,
                                 color=GREY, lw=1.2))  # fmt: skip
    ax.text(60.6, y, mode, va="center", fontfamily=MONO, fontsize=9.5)
    ax.text(60.6, y - 2.7, mark, va="center", color=colour, fontweight="bold", fontsize=12)
    ax.text(63, y - 2.7, outcome, va="center", color=DARK, fontsize=9.5)

out = Path(__file__).with_name("het-call-repeat")
fig.savefig(out.with_suffix(".png"), dpi=300, bbox_inches="tight", facecolor="white")
