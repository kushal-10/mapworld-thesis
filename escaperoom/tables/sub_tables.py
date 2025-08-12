import pandas as pd
import os

# --- Configuration ---
INPUT = "results/scores.html"
RESULTS_DIR = "results"
set_names = ["Set1", "Set2", "Set3", "Set4"]
score_types = ["% Played", "Quality score"]

# --- Read CSV with 2-line header ---
df = pd.read_csv(INPUT, header=[0, 1])

# The first column is usually ("model", "model") or just ('model','') or ('model', nan) — handle generically
first_col = df.columns[0]
if isinstance(first_col, tuple):
    first_col_name = first_col[0]
else:
    first_col_name = first_col

# --- Save master table: only sets ---
set_cols = [first_col]
for set_name in set_names:
    for score in score_types:
        set_cols.append((score, set_name))

df_master = df.loc[:, set_cols]
df_master.to_csv(os.path.join(RESULTS_DIR, "scores_only_sets.csv"), index=False)
print("✅ Master table (only sets) written to scores_only_sets.csv")

# --- Save per-set tables ---
for set_name in set_names:
    per_set_cols = [first_col]
    for score in score_types:
        per_set_cols.append((score, set_name))
    df_set = df.loc[:, per_set_cols]
    out_path = os.path.join(RESULTS_DIR, f"scores_{set_name.lower()}.csv")
    df_set.to_csv(out_path, index=False)
    print(f"✅ Per-set table written to {out_path}")

print("Done.")
