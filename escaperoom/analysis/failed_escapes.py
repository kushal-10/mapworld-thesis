import os
import plotly.graph_objs as go
import plotly.io as pio

import pandas as pd
import json

def load_json(path):
    with open(path) as json_file:
        return json.load(json_file)

def get_escape_val(int_data):
    turns = int_data['turns']
    final_turn = turns[-1][-1]
    val = final_turn['action']['type']
    cont = final_turn['action']['content']


    if val == "escape":
        if cont == "success":
            return 1
        else:
            last_turn_data = turns[-1]
            for i in range(len(last_turn_data)):
                ind = len(last_turn_data) - 1 - i
                current_val = last_turn_data[ind]
                if current_val["action"]["type"] == "image":
                    image_data_exp = current_val["action"]["content"]["image"][0]

                    exp_room_type = image_data_exp.split("/")[-2]

            firstturndata = turns[0][0]
            room_type = firstturndata["action"]["content"]["image"][0].split("/")[-2]
            if room_type == exp_room_type:
                return 0
            else:
                return 2

    return 3

base_dir = "results"

interaction_files = []
for dirname, _, filenames in os.walk(base_dir):
    for filename in filenames:
        if filename.endswith("interactions.json"):
            interaction_files.append(os.path.join(dirname, filename))


possible_values = []
possible_contents = []
possible_dicts = []
abort_data = {}
for interaction_file in interaction_files:
    int_data = load_json(interaction_file)
    model_name = int_data["meta"]["dialogue_pair"]
    model = model_name.split("-t0.0")[0]
    if model == "mock":
        continue
    if model not in abort_data:
        abort_data[model] = {}

    val = get_escape_val(int_data)
    if val != 3:
        exp_name = int_data["meta"]["experiment_name"]
        if exp_name not in abort_data[model]:
            abort_data[model][exp_name] = [val]
        else:
            abort_data[model][exp_name].append(val)

model_name_map = {
    'o3': 'o3',
    'gpt-4.1': 'GPT-4.1',
    'claude-sonnet-4': 'Claude-Sonnet-4',
    'o4-mini': 'o4-mini',
    'gpt-4.1-mini': 'GPT-4.1-mini',
    'GLM-4.1V-9B-Thinking': 'GLM-4.1V-9B-Th',
    'InternVL3-38B': 'InternVL3-38B',
    'mistral-small-3.1-24b-instruct': 'Mistral-Small-3.1-24B',
    'llama-4-maverick': 'Llama-4-Maverick',
    'InternVL3-14B': 'InternVL3-14B',
    'InternVL3-78B': 'InternVL3-78B',
    'InternVL3-8B': 'InternVL3-8B',
}

# Desired order for plotting (mapped display names)
ordered_names = [
    'o3',
    'GPT-4.1',
    'Claude-Sonnet-4',
    'o4-mini',
    'GPT-4.1-mini',
    'GLM-4.1V-9B-Th',
    'InternVL3-38B',
    'Mistral-Small-3.1-24B',
    'Llama-4-Maverick',
    'InternVL3-14B',
    'InternVL3-78B',
    'InternVL3-8B'
]

def plot_escape_outcomes_by_model_experiment(
    escape_data,              # Dict: model -> experiment -> [0/1/2, ...] (output of get_escape_val)
    model_name_map,
    ordered_names,
    experiment_names,
    experiment_display_map=None,
    models_to_plot=None,
    show=True,
    save_path=None,
    as_percentage=False
):
    import plotly.graph_objs as go
    import plotly.io as pio
    import numpy as np

    if experiment_display_map is None:
        experiment_display_map = {k: k.capitalize() for k in experiment_names}
    if models_to_plot is not None:
        filtered_names = [m for m in ordered_names if m in models_to_plot]
    else:
        filtered_names = ordered_names.copy()

    # Prepare y values for each outcome type, by experiment
    status_labels = ['Success', 'Escaped attempted from distractor room', 'Escaped attempted from non-distractor room']
    status_vals = [1, 0, 2]
    status_colors = [ '#FF6565', '#8FAADC']  # green, red, blue

    n_exp = len(experiment_names)
    n_models = len(filtered_names)

    # For each experiment, keep a separate list for each outcome (success/fail/aborted)
    data = {status: [] for status in status_labels}
    for expt in experiment_names:
        for model in filtered_names:
            orig_key = None
            for k, v in model_name_map.items():
                if v == model:
                    orig_key = k
                    break
            vals = []
            if orig_key and orig_key in escape_data and expt in escape_data[orig_key]:
                vals = escape_data[orig_key][expt]
            n = len(vals)
            counts = [0, 0, 0]
            for v in vals:
                if v == 1:
                    counts[0] += 1
                elif v == 0:
                    counts[1] += 1
                else:
                    counts[2] += 1
            if as_percentage and n > 0:
                counts = [100 * c / n for c in counts]
            data['Success'].append(counts[0])
            data['Escaped attempted from distractor room'].append(counts[1])
            data['Escaped attempted from non-distractor room'].append(counts[2])

    # Plot: for each outcome, bars (each bar at x=[model, exp]) - stacked bar grouped by experiment
    x_vals = []
    for model in filtered_names:
        for expt in experiment_names:
            x_vals.append(f"{model}<br>{experiment_display_map[expt]}")

    # Each outcome type is a trace (so stacking works)
    traces = []
    bar_indices = list(range(len(x_vals)))
    offset = 0
    for i, status in enumerate(status_labels):
        traces.append(
            go.Bar(
                name=status,
                x=x_vals,
                y=data[status],
                marker_color=status_colors[i],
            )
        )

    fig = go.Figure(traces)
    fig.update_layout(
        barmode='stack',
        xaxis_title='Model and Experiment',
        yaxis_title='Percentage of Tasks' if as_percentage else 'Number of Tasks',
        title='Escape Outcomes per Model and Experiment',
        legend_title_text='Outcome',
        bargap=0.25
    )
    fig.show() if show else None
    if save_path:
        fname = 'escape_outcomes_by_model_experiment'
        if as_percentage:
            fname += '_pct'
        fig.write_html(f"{save_path}/{fname}.html")



if __name__ == '__main__':

    results_dict = abort_data
    default_colors = pio.templates['plotly'].layout.colorway  # default Plotly palette
    # -- Only 3 abort types, using same color logic as before
    # outcome_plot_order = [1, 2, 0]
    # outcome_map = {
    #     1: "Moves Exceeded",
    #     2: "Conversation Exceeded",
    #     0: "Invalid"
    # }
    # abort_colors = [
    #     default_colors[0],     # Blueish for Moves Exceeded
    #     default_colors[6],     # Yellowish for Conversation Exceeded
    #     default_colors[2]      # Purple-ish for Invalid
    # ]

    experiment_display_map = {"small": "Small", "medium": "Medium", "large": "Large"}
    models_to_plot = ['o3','GPT-4.1','Claude-Sonnet-4']
    midlow = [
        'o4-mini',
        'GPT-4.1-mini',
        'GLM-4.1V-9B-Th',
        'InternVL3-38B',
        'Mistral-Small-3.1-24B',

    ]
    low = [
        'Llama-4-Maverick',
        'InternVL3-14B',
        'InternVL3-78B',
        'InternVL3-8B'
    ]
    experiment_names = ["low_dual_ambiguity", "medium_dual_ambiguity", "high_dual_ambiguity"]
    experiment_display_map = {"low_dual_ambiguity": "LD", "medium_dual_ambiguity": "MD", "high_dual_ambiguity": "HD"}
    plot_escape_outcomes_by_model_experiment(
        results_dict,
        model_name_map,
        ordered_names,
        experiment_names,
        experiment_display_map=experiment_display_map,
        models_to_plot=models_to_plot,
        show=True,
        save_path=None
    )
