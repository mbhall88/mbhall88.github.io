#!/usr/bin/env python3
import pandas as pd
from pathlib import Path
import seaborn as sns
import matplotlib.pyplot as plt
import math

base_dir = Path("/scratch/user/uqmhal11/minimap_preset_testing/variants")

print("Gathering summary files...")
summary_data = []

for filepath in base_dir.rglob("*.precision-recall-summary.tsv"):
    rel_path = filepath.relative_to(base_dir)
    read_model = rel_path.parts[0]
    preset = rel_path.parts[1]
    sample = rel_path.parts[2]
    
    df = pd.read_csv(filepath, sep='\t')
    df['read_model'] = read_model
    df['preset'] = preset
    df['sample'] = sample
    
    summary_data.append(df)

if not summary_data:
    print("Error: No summary data found. Check your paths.")
    exit(1)

merged_df = pd.concat(summary_data, ignore_index=True)
best_df = merged_df[merged_df['THRESHOLD'] == 'BEST'].copy()

out_csv = base_dir / "aggregated_precision_recall_summaries.csv"
best_df.to_csv(out_csv, index=False)
print(f"Aggregated data saved to {out_csv}")

print("Generating comparative plots...")
sns.set_theme(style="whitegrid")

for var_type in ['SNP', 'INDEL']:
    plot_df = best_df[best_df['VAR_TYPE'] == var_type].copy()
    
    if plot_df.empty:
        continue

    fig, ax1 = plt.subplots(figsize=(10, 8))
    fig.suptitle(f"{var_type} Performance: minimap2 Presets", fontsize=16)

    sns.boxplot(
        data=plot_df, x='preset', y='F1_QSCORE', hue='read_model', 
        ax=ax1, palette="Set2"
    )
    sns.stripplot(
        data=plot_df, x='preset', y='F1_QSCORE', hue='read_model', 
        ax=ax1, dodge=True, color='black', alpha=0.5, size=4, legend=False
    )
    
    ax1.set_xlabel("minimap2 Preset", fontsize=12)
    ax1.set_ylabel("Phred-scaled F1 Q-Score", fontsize=12)

    ax2 = ax1.twinx()
    
    f1_targets = [0.5, 0.8, 0.9, 0.95, 0.98, 0.99, 0.995, 0.998, 0.999, 0.9995, 0.9999, 0.99995, 0.99999, 0.999999]
    f1_labels = ["0.50", "0.80", "0.90", "0.95", "0.98", "0.99", "0.995", "0.998", "0.999", "0.9995", "0.9999", "0.99995", "0.99999", "0.999999"]
    q_targets = [-10 * math.log10(1 - f1) for f1 in f1_targets]
    
    ax2.set_yticks(q_targets)
    ax2.set_yticklabels(f1_labels)
    ax2.set_ylim(ax1.get_ylim())
    ax2.set_ylabel("Raw F1 Score", rotation=270, labelpad=20, fontsize=12)
    ax2.grid(False)

    handles, labels = ax1.get_legend_handles_labels()
    ax1.legend(handles, labels, title="Read Model", loc="lower right")

    plt.tight_layout()
    plot_path = base_dir / f"preset_comparison_{var_type}.png"
    plt.savefig(plot_path, dpi=300)
    plt.close()
    print(f"Saved plot: {plot_path}")
