#!/usr/bin/env python3
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

base_dir = Path("/scratch/user/uqmhal11/minimap_preset_testing/variants")
plot_dir = base_dir / "plots"
plot_dir.mkdir(exist_ok=True)

csv_path = base_dir / "aggregated_precision_recall_summaries.csv"

if not csv_path.exists():
    print(f"Error: {csv_path} not found.")
    exit(1)

data = pd.read_csv(csv_path)

named_colors = {
    "black": "#000000",
    "orange": "#e69f00",
    "skyblue": "#56b4e9",
    "bluish green": "#009e73",
    "yellow": "#f0e442",
    "blue": "#0072b2",
    "vermilion": "#d55e00",
    "reddish purple": "#cc79a7",
}
cud_palette = list(named_colors.values())

def cud(n: int = len(cud_palette), start: int = 0) -> list[str]:
    remainder = cud_palette[:start]
    palette = cud_palette[start:] + remainder
    return palette[:n]

sns.set_theme(style="whitegrid")

metrics = ["F1_SCORE", "PREC", "RECALL"]
x = "read_model"
hue = "preset"
var_types = ["SNP", "INDEL"]

order = sorted(data[x].unique())
hue_order = sorted(data[hue].unique())
pal = {c: cud()[i] for i, c in enumerate(hue_order)}

for y in metrics:
    fig, axes = plt.subplots(
        nrows=1,
        ncols=len(var_types),
        figsize=(12, 6),
        dpi=300,
        sharey=True,
    )
    
    for i, vartype in enumerate(var_types):
        ax = axes[i]
        legend = (i == 0)
        
        df = data.query("VAR_TYPE == @vartype").copy()
        if df.empty:
            continue

        cap = 0.99999
        df.loc[:, y] = df[y].apply(lambda v: cap if v > cap else v)
        
        yticks = [0.5, 0.8, 0.9, 0.95, 0.99, 0.999, 0.9999, cap]
        yticklabels = [f"{yval:.2%}" for yval in yticks]

        box_kws = {
            "data": df, "x": x, "y": y, "order": order, "hue": hue,
            "ax": ax, "palette": pal, "fliersize": 0, "legend": legend,
        }
        
        if int(sns.__version__.split('.')[1]) >= 13:
            box_kws["fill"] = False
            box_kws["gap"] = 0.2
        
        sns.boxplot(**box_kws)

        sns.stripplot(
            data=df, x=x, y=y, order=order, hue=hue, ax=ax,
            palette=pal, alpha=0.5, dodge=True, legend=False,
            linewidth=0.5, edgecolor="black",
        )

        ax.set_yscale("logit", nonpositive="clip")
        ax.set_yticks(yticks)
        ax.set_yticklabels(yticklabels)
        
        ylabel = {"F1_SCORE": "F1 score", "PREC": "Precision", "RECALL": "Recall"}[y]
        ax.set_ylabel(f"{vartype} {ylabel}")
        ax.set_xlabel("")
        ax.tick_params(axis="x", labelsize=12)
        ax.set_title(f"{vartype} {ylabel}")

        if legend:
            handles, labels = ax.get_legend_handles_labels()
            for h in handles:
                h.set_linewidth(3)
            ax.legend(
                handles=handles, labels=labels, framealpha=1.0,
                fancybox=True, shadow=True, title="Preset",
            )

    fig.tight_layout()
    out_file = plot_dir / f"boxplot_strip_{y}.pdf"
    fig.savefig(out_file)
