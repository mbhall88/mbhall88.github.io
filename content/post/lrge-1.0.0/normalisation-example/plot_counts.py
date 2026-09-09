"""Plot exported LRGE detector counts, without smoothing or simulated data."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter

ROOT = Path(__file__).resolve().parent
TEAL, AMBER, INK = "#00858a", "#efa72d", "#152132"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "text.color": INK, "axes.labelcolor": INK})

def plot(sample, ax):
    data = np.loadtxt(ROOT / f"{sample}.tsv", skiprows=1, dtype=int)
    values = np.repeat(data[:, 0], data[:, 1])
    median = np.sort(values)[(len(values)-1)//2]
    high = np.sort(values)[int(np.ceil(len(values)*.999))-1]
    # Integer edges at low counts, approximately equal logarithmic widths thereafter.
    edges = np.unique(np.rint(np.geomspace(1, 1024, 45))).astype(float) - .5
    heights, edges = np.histogram(values, bins=edges)
    colors = [TEAL if lo < 16*median else AMBER for lo in edges[:-1]]
    ax.bar(edges[:-1], heights, np.diff(edges), align="edge", color=colors,
           edgecolor="white", linewidth=.45)
    ax.set(xscale="log", yscale="log", xlim=(.7, 1024), ylim=(.8, 1e5),
           xlabel="Approximate minimizer count (log scale)",
           ylabel="Distinct minimizers per bin (log scale)", title=sample)
    ax.set_xticks([1, 10, 100, 1000])
    ax.xaxis.set_major_formatter(ScalarFormatter())
    ax.set_yticks([1, 10, 100, 1000, 10000])
    ax.yaxis.set_major_formatter(ScalarFormatter())
    ax.minorticks_off()
    ax.axvline(high, color=INK, ls="--", lw=1)
    ax.text(.34, .96, f"Median = {median}\n99.9th percentile = {high}\nSkew score = {high/median:.0f}×",
            va="top", transform=ax.transAxes, fontsize=10,
            bbox={"facecolor": "white", "alpha": .85, "edgecolor": "none"})
    print(sample, "distinct", len(values), "median", median, "q999", high,
          "above16", int((values >= 16*median).sum()))
    print("high-count bins:", [(round(a,1),round(b,1),int(n)) for a,b,n in
                                 zip(edges[:-1],edges[1:],heights) if a>20])

if __name__ == "__main__":
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), layout="constrained")
    for sample, ax in zip(["SRR26465526", "SRR10353548"], axes):
        plot(sample, ax)
    fig.savefig(ROOT / "detector-counts-comparison.png", dpi=180)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(6.3, 4.5), layout="constrained")
    plot("SRR26465526", ax)
    fig.savefig(ROOT / "SRR26465526-detector-counts.png", dpi=200)
    fig.savefig(ROOT / "SRR26465526-detector-counts.svg")
    plt.close(fig)
