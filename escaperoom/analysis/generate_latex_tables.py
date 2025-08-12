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
for col in table.columns:
    if col != "experiment":
        table[col] = table[col].apply(lambda x: round(x, 1))
exps = ['0_small', '1_medium', '2_large', # set1
        '3_no_ambiguity', '4_medium_ambiguity', '5_high_ambiguity',
        '6_low_dual_ambiguity', '7_medium_dual_ambiguity', '8_high_dual_ambiguity', #set2 3-8
        '9_path', '10_ladder', '12_tree', #set 3
        '13_adjacent', '14_near', '15_far' #set 4
        ]

# colours = ["rowblue1", "rowblue2", "rowblue3",
#            "rowred1", "rowred2", "rowred3",
#            "rowred4", "rowred5", "rowred6",
#            "rowgreen1", "rowgreen2", "rowgreen3",
#            "rowyellow1", "rowyellow2", "rowyellow3"]
#
# all_scores = [
#     'o4-mini-t0.0--o4-mini-t0.0_clemscore', 'o4-mini-t0.0--o4-mini-t0.0_PP', 'o4-mini-t0.0--o4-mini-t0.0_QS',
#     'InternVL3-78B-t0.0--InternVL3-78B-t0.0_clemscore', 'InternVL3-78B-t0.0--InternVL3-78B-t0.0_PP', 'InternVL3-78B-t0.0--InternVL3-78B-t0.0_QS',
#     'InternVL3-38B-t0.0--InternVL3-38B-t0.0_clemscore', 'InternVL3-38B-t0.0--InternVL3-38B-t0.0_PP', 'InternVL3-38B-t0.0--InternVL3-38B-t0.0_QS',
#     'InternVL3-14B-t0.0--InternVL3-14B-t0.0_clemscore', 'InternVL3-14B-t0.0--InternVL3-14B-t0.0_PP', 'InternVL3-14B-t0.0--InternVL3-14B-t0.0_QS',
#     'InternVL3-8B-t0.0--InternVL3-8B-t0.0_clemscore', 'InternVL3-8B-t0.0--InternVL3-8B-t0.0_PP', 'InternVL3-8B-t0.0--InternVL3-8B-t0.0_QS',
#     'InternVL3-2B-t0.0--InternVL3-2B-t0.0_clemscore', 'InternVL3-2B-t0.0--InternVL3-2B-t0.0_PP', 'InternVL3-2B-t0.0--InternVL3-2B-t0.0_QS',
#     'InternVL3-1B-t0.0--InternVL3-1B-t0.0_clemscore', 'InternVL3-1B-t0.0--InternVL3-1B-t0.0_PP', 'InternVL3-1B-t0.0--InternVL3-1B-t0.0_QS',]
#
# pq_scores = [
#     'o4-mini-t0.0--o4-mini-t0.0_PP', 'o4-mini-t0.0--o4-mini-t0.0_QS',
#     'InternVL3-78B-t0.0--InternVL3-78B-t0.0_PP', 'InternVL3-78B-t0.0--InternVL3-78B-t0.0_QS',
#     'InternVL3-38B-t0.0--InternVL3-38B-t0.0_PP', 'InternVL3-38B-t0.0--InternVL3-38B-t0.0_QS',
#     'InternVL3-14B-t0.0--InternVL3-14B-t0.0_PP', 'InternVL3-14B-t0.0--InternVL3-14B-t0.0_QS',
#     'InternVL3-8B-t0.0--InternVL3-8B-t0.0_PP', 'InternVL3-8B-t0.0--InternVL3-8B-t0.0_QS',
#     # 'InternVL3-2B-t0.0--InternVL3-2B-t0.0_PP', 'InternVL3-2B-t0.0--InternVL3-2B-t0.0_QS',
#     # 'InternVL3-1B-t0.0--InternVL3-1B-t0.0_PP', 'InternVL3-1B-t0.0--InternVL3-1B-t0.0_QS'
# ]
# """
# & \cellcolor{rowblue}hard & \cellcolor{rowblue}81.2 & \cellcolor{rowblue}93.7 & \cellcolor{rowblue}87.5 & \cellcolor{rowblue}93.7 & \cellcolor{rowblue}43.7 & \cellcolor{rowblue}87.5 & \cellcolor{rowblue}31.2 & \cellcolor{rowblue}87.5 & \cellcolor{rowblue}18.7 & \cellcolor{rowblue}93.7 & \cellcolor{rowblue}56.2 & \cellcolor{rowblue}87.5 & \cellcolor{rowblue}62.5 & \cellcolor{rowblue}100\\
# """
#
# col_items = {
#      0: "\multicolumn{1}{|l|}{\multirow{2}{*}{\\textbf{G}}}",
#      3: "\multicolumn{1}{|l|}{\multirow{2}{*}{\\textbf{Amb}}}",
#      9: "\multicolumn{1}{|l|}{\multirow{2}{*}{\\textbf{Top}}}",
#      12: "\multicolumn{1}{|l|}{\multirow{2}{*}{\\textbf{Dist}}}"
# }
#
# strings = []
# for i in range(len(exps)):
#     if i in col_items:
#         strings.append("\\hline")
#         strings.append(col_items[i])
#
#     else:
#         strings.append("\multicolumn{1}{|l|}{}")
#     colour = colours[i]
#     exp_name = exps[i].split("_")[1]
#     str_builder = f"& \cellcolor{{{colour}}} {exp_name}"
#     for pq in pq_scores:
#         score = table.loc[table['experiment'] == exps[i], pq].values[0]
#         str_builder += f" & \cellcolor{{{colour}}} {score}"
#
#     str_builder += " \\\\"
#
#     strings.append(str_builder)
#
# strings.append("\\hline")
#
# for s in strings:
#     print(f"{s}\n")




