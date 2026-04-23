#!/usr/bin/env python3
import math
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

base_dir = Path("/scratch/user/uqmhal11/minimap_preset_testing/variants")
plot_dir = base_dir / "plots"
plot_dir.mkdir(exist_ok=True)

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

frames = []
pr_files = list(base_dir.rglob("*.precision-recall.tsv"))

for p in pr_files:
    rel_path = p.relative_to(base_dir)
    read_model = rel_path.parts[0]
    preset = rel_path.parts[1]
    sample = rel_path.parts[2]      
    
    df = pd.read_csv(p, sep="\t")
    df["sample"] = sample
    df["read_model"] = read_model
    df["preset"] = preset
    frames.append(df)

if not frames:
    print("Error: No precision-recall data found.")
    exit(1)

pr_df = pd.concat(frames, ignore_index=True)
samples = set(pr_df["sample"])

metrics = []
for vartype in ["SNP", "INDEL"]:
    for model in ["hac", "sup"]:
        for preset in pr_df["preset"].unique():
            data = pr_df.query("VAR_TYPE == @vartype and read_model == @model and preset == @preset")
            if data.empty: continue
                
            for q in sorted(set(data["MIN_QUAL"])):
                subdf = data.query("MIN_QUAL == @q")
                if set(subdf["sample"]) == samples:
                    tps = subdf["TRUTH_TP"].sum()
                    fps = subdf["QUERY_FP"].sum()
                    fns = subdf["TRUTH_FN"].sum()
                    
                    if (tps + fps) == 0 or (tps + fns) == 0: continue
                        
                    precision = tps / (tps + fps)
                    recall = tps / (tps + fns)
                    f1 = 2 * (precision * recall) / (precision + recall)
                    
                    metrics.append((preset, q, precision, recall, f1, vartype, model))

aggdf = pd.DataFrame(
    metrics,
    columns=["preset", "QUAL", "precision", "recall", "f1", "vartype", "read_model"],
)

aggdf.to_csv(plot_dir / "aggregated_pr_metrics.tsv", sep="\t", index=False)

vartypes = ["SNP", "INDEL"]
read_models = ["hac", "sup"]

fig, axes = plt.subplots(
    nrows=len(vartypes),
    ncols=len(read_models),
    figsize=(12, 10),
    dpi=300,
    sharex=True,
    sharey=True,
)

x = "recall"
y = "precision"
hue = "preset"

hue_order = sorted(set(aggdf[hue]))
pal = {c: cud()[i] for i, c in enumerate(hue_order)}

i = 0
legend = True
for vartype in vartypes:
    for model in read_models:
        ax = axes.flatten()[i]
        data = aggdf.query("vartype == @vartype and read_model == @model").copy()
        
        cap = 0.99999
        data.loc[:, y] = data[y].apply(lambda v: cap if v > cap else v)

        sns.lineplot(
            data=data, x=x, y=y, hue=hue, hue_order=hue_order,
            ax=ax, palette=pal, alpha=0.9, linewidth=2, legend=legend,
        )

        if legend:
            handles, labels = ax.get_legend_handles_labels()
            ax.legend().remove()
            legend = False

        ax.set_yscale("logit", nonpositive="clip")
        yticks = [0.8, 0.9, 0.95, 0.99, 0.999, 0.9999, cap]
        yticklabels = [f"{yval:.2%}" for yval in yticks]
        ax.set_yticks(yticks)
        ax.set_yticklabels(yticklabels)

        xticks = [0, 0.25, 0.5, 0.75, 1.0]
        xticklabels = [f"{xval:.2%}" for xval in xticks]
        ax.set_xticks(xticks)
        ax.set_xticklabels(xticklabels)
        ax.set_title(f"{vartype} ({model})")
        i += 1

for h in handles:
    h.set_linewidth(3)

plt.tight_layout()
leg_cols = math.ceil(len(hue_order))
fig.legend(
    handles=handles, labels=labels, loc="upper center",
    bbox_to_anchor=(0.5, 1.05), ncol=leg_cols, title="minimap2 preset",
    framealpha=1.0, fancybox=True, shadow=True,
)

out_png = plot_dir / "aggregated_precision_recall.png"
fig.savefig(out_png, bbox_inches="tight", dpi=300)
print(f"Saved plot: {out_png}")
