#!/usr/bin/env python3
import pandas as pd
from pathlib import Path

base_dir = Path("/scratch/user/uqmhal11/minimap_preset_testing/variants")
csv_path = base_dir / "aggregated_precision_recall_summaries.csv"
out_table_path = base_dir / "preset_comparison_summary.md"

if not csv_path.exists():
    print(f"Error: {csv_path} not found. Please run the aggregation script first.")
    exit(1)

df = pd.read_csv(csv_path)
summary_df = df.groupby(['VAR_TYPE', 'read_model', 'preset'])[['PREC', 'RECALL', 'F1_SCORE', 'F1_QSCORE']].mean().reset_index()
summary_df = summary_df.sort_values(['VAR_TYPE', 'read_model', 'preset'], ascending=[False, True, True])

summary_df['PREC'] = summary_df['PREC'].apply(lambda x: f"{x:.6f}")
summary_df['RECALL'] = summary_df['RECALL'].apply(lambda x: f"{x:.6f}")
summary_df['F1_SCORE'] = summary_df['F1_SCORE'].apply(lambda x: f"{x:.6f}")
summary_df['F1_QSCORE'] = summary_df['F1_QSCORE'].apply(lambda x: f"{x:.2f}")

summary_df.columns = ['Variant Type', 'Read Model', 'Preset', 'Mean Precision', 'Mean Recall', 'Mean F1 Score', 'Mean F1 Q-Score']

try:
    markdown_table = summary_df.to_markdown(index=False)
    with open(out_table_path, "w") as f:
        f.write("# minimap2 Preset Performance Summary\n\n")
        f.write("*Values represent the mean across all tested samples at the 'BEST' threshold.*\n\n")
        f.write(markdown_table)
        f.write("\n")
    print(f"Markdown table saved to: {out_table_path}")
except ImportError:
    fallback_path = base_dir / "preset_comparison_summary.tsv"
    summary_df.to_csv(fallback_path, sep='\t', index=False)
    print(f"TSV table saved to: {fallback_path}")
