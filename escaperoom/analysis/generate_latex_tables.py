import pandas as pd

df = pd.read_csv("results_paper/raw.csv")

# --- Calculate PP and QS for each (experiment, model) ---
# PP: 1 - mean(aborted) for each (experiment, model)
pp = (
    df[df["metric"] == "Aborted"]
    .groupby(["experiment", "model"])["value"]
    .mean()
    .apply(lambda x: 1 - x)
    .rename("PP")
    .reset_index()
)

# QS: mean(Main Score) for each (experiment, model)
qs = (
    df[df["metric"] == "Main Score"]
    .groupby(["experiment", "model"])["value"]
    .mean()
    .rename("QS")
    .reset_index()
)

# Merge PP and QS on experiment, model
scores = pd.merge(pp, qs, on=["experiment", "model"])

# clemscore = PP * QS / 100
scores["PP"] = scores["PP"]*100
scores["clemscore"] = scores["PP"] * scores["QS"]/100

# --- Pivot the table so columns are Model_(PP/QS/clemscore), rows are experiments ---
table = scores.pivot(index="experiment", columns="model")[["PP", "QS", "clemscore"]]

# Flatten the multiindex columns
table.columns = [f"{model}_{stat}" for stat, model in table.columns]

# Reset index to make 'experiment' a column
table = table.reset_index()

exps = ['0_small', '1_medium', '2_large',
        '3_no_ambiguity', '4_medium_ambiguity', '5_high_ambiguity',
        '6_low_dual_ambiguity', '7_medium_dual_ambiguity', '8_high_dual_ambiguity',
        '9_path', '10_ladder', '12_tree',
        '13_adjacent', '14_near', '15_far']

colours = []

scores = [
    'o4-mini-t0.0--o4-mini-t0.0_clemscore', 'o4-mini-t0.0--o4-mini-t0.0_PP', 'o4-mini-t0.0--o4-mini-t0.0_QS',
    'InternVL3-78B-t0.0--InternVL3-78B-t0.0_clemscore', 'InternVL3-78B-t0.0--InternVL3-78B-t0.0_PP', 'InternVL3-78B-t0.0--InternVL3-78B-t0.0_QS',
    'InternVL3-38B-t0.0--InternVL3-38B-t0.0_clemscore', 'InternVL3-38B-t0.0--InternVL3-38B-t0.0_PP', 'InternVL3-38B-t0.0--InternVL3-38B-t0.0_QS',
    'InternVL3-14B-t0.0--InternVL3-14B-t0.0_clemscore', 'InternVL3-14B-t0.0--InternVL3-14B-t0.0_PP', 'InternVL3-14B-t0.0--InternVL3-14B-t0.0_QS',
    'InternVL3-8B-t0.0--InternVL3-8B-t0.0_clemscore', 'InternVL3-8B-t0.0--InternVL3-8B-t0.0_PP', 'InternVL3-8B-t0.0--InternVL3-8B-t0.0_QS',
    'InternVL3-2B-t0.0--InternVL3-2B-t0.0_clemscore', 'InternVL3-2B-t0.0--InternVL3-2B-t0.0_PP', 'InternVL3-2B-t0.0--InternVL3-2B-t0.0_QS',
    'InternVL3-1B-t0.0--InternVL3-1B-t0.0_clemscore', 'InternVL3-1B-t0.0--InternVL3-1B-t0.0_PP', 'InternVL3-1B-t0.0--InternVL3-1B-t0.0_QS',]

for exp in exps:
    str_builder = ""

