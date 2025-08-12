import os
import plotly.graph_objs as go
import plotly.io as pio

import pandas as pd
import json

def load_json(path):
    with open(path) as json_file:
        return json.load(json_file)

def get_reason(int_data):
    turns = int_data['turns']
    final_turn = turns[-1][-1]
    val = final_turn['action']['type']
    cont = final_turn['action']['content']

    if val == "escape":
        return 3

    if val == "invalid value":
        return 0

    if val == "move":
        return 1 # moves exceeded

    if val == "image":
        return 2 # questions exceeded, change of turn

    if val == "turns exceeded":
        final_turns = turns[-1]
        last_val = None
        for i in range(len(final_turns)):
            last_index = len(final_turns) - 1 - i
            turn_data = final_turns[last_index]
            if turn_data['from'] != "GM":
                last_val = turn_data
                break
        if not last_val:
            print("something broke")
        else:
            content = last_val['action']['content'].lower()
            if content.startswith("question") or content.startswith("answer"):
                return 2
            elif content.startswith("move"):
                return 1
            else:
                print("something broke again")

    return val

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

    val = get_reason(int_data)

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

def plot_aborts_by_model_experiment(
    results_dict,
    model_name_map,
    ordered_names,
    experiment_names,  # these are the KEYS, e.g., ["small", "medium", "large"]
    experiment_display_map=None,  # {"small": "Small", ...}
    models_to_plot=None,
    show=True,
    save_path=None
):
    import plotly.graph_objs as go
    import plotly.io as pio

    # Setup models
    if models_to_plot is not None:
        filtered_names = [m for m in ordered_names if m in models_to_plot]
    else:
        filtered_names = ordered_names.copy()

    # Set up display map
    if experiment_display_map is None:
        experiment_display_map = {k: k.capitalize() for k in experiment_names}

    # Collect aborts for each experiment/model
    aborts_per_experiment = {expt: [] for expt in experiment_names}
    for orig_name in filtered_names:
        orig_key = None
        for k, v in model_name_map.items():
            if v == orig_name:
                orig_key = k
                break
        for expt in experiment_names:
            count = 0
            if orig_key is not None and orig_key in results_dict:
                vals = results_dict[orig_key].get(expt, [])
                count = sum(1 for v in vals if v != 3)  # Exclude success
            aborts_per_experiment[expt].append(count)

    # Plot: 1 bar per experiment (grouped by model)
    traces = []
    default_colors = pio.templates['plotly'].layout.colorway
    for i, expt in enumerate(experiment_names):
        traces.append(
            go.Bar(
                name=experiment_display_map.get(expt, expt),
                x=filtered_names,
                y=aborts_per_experiment[expt],
                marker_color=default_colors[i % len(default_colors)]
            )
        )

    fig = go.Figure(data=traces)
    fig.update_layout(
        barmode='group',
        xaxis_title='Model',
        yaxis_title='Number of Aborted Tasks',
        title='Total Aborts per Model Across Experiments',
        legend_title_text='Experiment'
    )
    if show:
        fig.show()
    if save_path:
        fig.write_html(f"{save_path}/aborts_by_model_experiment.html")

# Example usage:
# plot_aborts_by_experiment(abort_data, model_name_map, ordered_names,
#     experiment_names=['0_small', '2_large'],
#     models_to_plot=['o3', 'GPT-4.1', 'Claude-Sonnet-4'],
#     save_path='./plots')


if __name__ == '__main__':

    results_dict = abort_data
    default_colors = pio.templates['plotly'].layout.colorway  # default Plotly palette
    # -- Only 3 abort types, using same color logic as before
    outcome_plot_order = [1, 2, 0]
    outcome_map = {
        1: "Moves Exceeded",
        2: "Conversation Exceeded",
        0: "Invalid"
    }
    abort_colors = [
        default_colors[0],     # Blueish for Moves Exceeded
        default_colors[6],     # Yellowish for Conversation Exceeded
        default_colors[2]      # Purple-ish for Invalid
    ]

    experiment_display_map = {"small": "Small", "medium": "Medium", "large": "Large"}
    models_to_plot = ['o3','GPT-4.1','Claude-Sonnet-4']
    midlow = [
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
    experiment_names = ["small", "medium", "large"]
    plot_aborts_by_model_experiment(
        results_dict,
        model_name_map,
        ordered_names,
        experiment_names,
        experiment_display_map=experiment_display_map,
        models_to_plot=midlow,
        show=True,
        save_path=None
    )
