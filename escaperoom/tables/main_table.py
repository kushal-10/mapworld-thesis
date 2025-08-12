#!/usr/bin/env python3
import os
import sys
import pandas as pd

def main():
    raw_path = os.path.join("results", "raw.csv")
    out_path = os.path.join("results", "scores.csv")
    out_path_html = os.path.join("results", "scores.html")

    if not os.path.exists(raw_path):
        print(f"Error: Could not find {raw_path}", file=sys.stderr)
        sys.exit(1)

    expected = {'idx','game','model','experiment','episode','metric','value'}
    try:
        df = pd.read_csv(raw_path)
        if not expected.issubset(df.columns):
            raise ValueError("Header missing expected columns")
    except Exception:
        df = pd.read_csv(
            raw_path,
            header=None,
            names=['idx','game','model','experiment','episode','metric','value']
        )

    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    df = df.dropna(subset=['value'])

    pivot = df.pivot_table(
        index=['experiment','model','episode'],
        columns='metric',
        values='value',
        aggfunc='mean'
    )

    agg = (
        pivot
        .groupby(level=['experiment','model'])
        .agg({'Main Score':'mean','Aborted':'mean'})
        .reset_index()
    )

    agg['% Played']      = (1.0 - agg['Aborted']) * 100.0
    agg['Quality score'] = agg['Main Score']

    wide = (
        agg
        .pivot(index="model", columns="experiment")[["% Played", "Quality score"]]
    )

    experiment_order = ['0_small', '1_medium', '2_large',
        '3_no_ambiguity', '4_medium_ambiguity', '5_high_ambiguity',
        '6_low_dual_ambiguity', '7_medium_dual_ambiguity', '8_high_dual_ambiguity',
        '9_path', '10_ladder', '12_tree',
        '13_adjacent', '14_near', '15_far'
    ]
    score_types = ["% Played", "Quality score"]

    # Rearrange columns in experiment/score_types order
    new_columns = []
    for exp in experiment_order:
        for score in score_types:
            new_columns.append((score, exp))
    wide = wide.reindex(columns=pd.MultiIndex.from_tuples(new_columns), fill_value=None)
    # wide.rename(columns={'model': 'model'}, inplace=True)

    # Define experiment sets
    set_defs = {
        "Set1": ['0_small', '1_medium', '2_large'],
        "Set2": ['3_no_ambiguity', '4_medium_ambiguity', '5_high_ambiguity',
                 '6_low_dual_ambiguity', '7_medium_dual_ambiguity', '8_high_dual_ambiguity'],
        "Set3": ['9_path', '10_ladder', '12_tree'],
        "Set4": ['13_adjacent', '14_near', '15_far']
    }

    # For each model, compute mean across set columns for both metrics
    for set_name, set_exps in set_defs.items():
        for metric in score_types:
            cols = [(metric, exp) for exp in set_exps if (metric, exp) in wide.columns]
            wide[(metric, set_name)] = wide[cols].mean(axis=1)

    # Put set averages after experiments
    new_exp_order = experiment_order + list(set_defs.keys())
    new_columns = []
    for exp in new_exp_order:
        for score in score_types:
            new_columns.append((score, exp))
    wide = wide.reindex(columns=pd.MultiIndex.from_tuples(new_columns), fill_value=None)
    wide = wide.reset_index()

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    wide.to_csv(out_path, index=False)
    wide.to_html(out_path_html, index=False)

    print(f"✅ Generated {out_path} with experiment set averages")



if __name__ == "__main__":
    main()
