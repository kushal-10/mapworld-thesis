import pandas as pd

df = pd.read_csv("results/raw.csv")

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
scores["clemscore"] = scores["PP"] * scores["QS"] / 100

# --- Pivot the table so columns are Model_(PP/QS/clemscore), rows are experiments ---
table = scores.pivot(index="experiment", columns="model")[["PP", "QS", "clemscore"]]

# Flatten the multiindex columns
table.columns = [f"{model}_{stat}" for stat, model in table.columns]

# Reset index to make 'experiment' a column
table = table.reset_index()

print(table)