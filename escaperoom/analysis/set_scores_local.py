#!/usr/bin/env python3
import os
import sys
import pandas as pd

def main():
    raw_path = os.path.join("results_local", "raw.csv")
    out_path = os.path.join("results_local", "scores.html")

    if not os.path.exists(raw_path):
        print(f"Error: Could not find {raw_path}", file=sys.stderr)
        sys.exit(1)

    # 1) Read CSV, either with header or fallback to no‐header
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

    # 2) Coerce 'value' to numeric and drop parse‐failures
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    df = df.dropna(subset=['value'])

    # 3) Pivot so metrics become columns per (experiment, model, episode)
    pivot = df.pivot_table(
        index=['experiment','model','episode'],
        columns='metric',
        values='value',
        aggfunc='mean'
    )

    # 4) Aggregate per experiment & model
    agg = (
        pivot
        .groupby(level=['experiment','model'])
        .agg({'Main Score':'mean','Aborted':'mean'})
        .reset_index()
    )

    # 5) Compute % Played and Quality score
    agg['% Played']      = (1.0 - agg['Aborted']) * 100.0
    agg['Quality score'] = agg['Main Score']

    # 6) Build the multi‐column DataFrame
    table = agg.set_index(['experiment','model'])[['% Played','Quality score']]
    table.columns = pd.MultiIndex.from_product([['Model'], table.columns])
    table = table.reset_index()

    # 7) Sort by numeric prefix of experiment (0,1,2,...)
    #    Assumes experiment names always start with "<number>_"
    table['exp_order'] = table['experiment'].str.split('_').str[0].astype(int)
    table = table.sort_values(by=['exp_order','model']).drop(columns='exp_order')

    # 8) Ensure output folder exists and write HTML
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    table.to_html(out_path, index=False)
    print(f"✅ Generated {out_path}")

if __name__ == "__main__":
    main()
