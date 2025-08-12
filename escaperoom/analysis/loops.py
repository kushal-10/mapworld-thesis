import os
import json
import plotly.graph_objs as go
import plotly.io as pio

# --- Move utilities ---
MOVE_MAP = {
    "north": (0, 1),
    "south": (0, -1),
    "east": (1, 0),
    "west": (-1, 0)
}

def load_json(path):
    with open(path) as f:
        return json.load(f)

def get_moves(int_data):
    moves = []
    for turn in int_data['turns']:
        for t in turn:
            action = t["action"]
            if action["type"] == "get message":
                act_content = action["content"].lower()
                if act_content.startswith("move"):
                    move = act_content[5:].strip()
                    if move in MOVE_MAP:
                        moves.append(move)
    return moves

def count_loops(moves, min_len=2, max_len=4):
    n = len(moves)
    found = 0
    for window in range(min_len, max_len + 1):
        for i in range(n - window + 1):
            dx, dy = 0, 0
            for move in moves[i:i+window]:
                mx, my = MOVE_MAP.get(move, (0, 0))
                dx += mx
                dy += my
            if dx == 0 and dy == 0:
                found += 1
    return found

# ---- Model display mapping ----
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

def plot_stacked_loops_by_model_experiment_v2(
    loop_data,
    model_name_map,
    ordered_names,
    experiment_names,             # ['small', 'medium', 'large']
    experiment_display_map=None,  # {'small': 'Small', ...}
    models_to_plot=None,
    show=True,
    save_path=None
):
    import plotly.graph_objs as go
    import plotly.io as pio
    import numpy as np

    # Custom color pairs (experiment: [≤3 color, ≥4 color])
    exp_colors = {
        'small':   ['#4587A4', '#55BCEA'],   # blues dark, light
        'medium':  ['#e8432c', "#e79489"],   # reds
        'large':   ['#85ec34', '#b2f3b0'],   # greens
    }

    if experiment_display_map is None:
        experiment_display_map = {k: k.capitalize() for k in experiment_names}

    if models_to_plot is not None:
        filtered_names = [m for m in ordered_names if m in models_to_plot]
    else:
        filtered_names = ordered_names.copy()

    n_models = len(filtered_names)
    n_expts = len(experiment_names)

    # Prepare y values and trace structure:
    # For each experiment, make two traces: ≤3 and ≥4, with "offsets" to group by model
    x_vals = filtered_names
    bar_width = 0.2  # control space between bars in a group

    traces = []
    for eidx, expt in enumerate(experiment_names):
        y_le3 = []
        y_ge4 = []
        for model in filtered_names:
            orig_key = None
            for k, v in model_name_map.items():
                if v == model:
                    orig_key = k
                    break
            vals = []
            if orig_key is not None and orig_key in loop_data and expt in loop_data[orig_key]:
                vals = loop_data[orig_key][expt]
            le3 = sum(1 for n in vals if 1 <= n <= 3)
            ge4 = sum(1 for n in vals if n >= 4)
            y_le3.append(le3)
            y_ge4.append(ge4)

        # Offset for grouping bars by model
        offset = -bar_width + eidx * bar_width  # centers the three bars per model
        traces.append(
            go.Bar(
                name=f"{experiment_display_map[expt]}, ≤3 Loops",
                x=x_vals,
                y=y_le3,
                marker_color=exp_colors[expt][0],
                offsetgroup=str(eidx),
                width=bar_width,
                legendgroup=f"{expt}-le3",
                showlegend=True
            )
        )
        traces.append(
            go.Bar(
                name=f"{experiment_display_map[expt]}, ≥4 Loops",
                x=x_vals,
                y=y_ge4,
                marker_color=exp_colors[expt][1],
                offsetgroup=str(eidx),
                base=y_le3,  # stack on top of ≤3
                width=bar_width,
                legendgroup=f"{expt}-ge4",
                showlegend=True
            )
        )

    fig = go.Figure(traces)
    fig.update_layout(
        barmode='stack',
        xaxis_title='Model',
        yaxis_title='Number of Tasks',
        title='Stacked Loop Counts by Model and Experiment',
        legend_title_text='Experiment and Loop Group',
        bargap=0.25
    )
    fig.show() if show else None
    if save_path:
        fig.write_html(f"{save_path}/grouped_stacked_loops_by_model_experiment.html")

if __name__ == '__main__':
    # ---- Collect loop counts per task ----
    base_dir = "results"
    interaction_files = []
    for dirname, _, filenames in os.walk(base_dir):
        for filename in filenames:
            if filename.endswith("interactions.json"):
                interaction_files.append(os.path.join(dirname, filename))

    # Dict: model_name -> exp_name -> [num_loops, ...]
    loop_data = {}
    for interaction_file in interaction_files:
        int_data = load_json(interaction_file)
        model_name = int_data["meta"]["dialogue_pair"]
        model = model_name.split("-t0.0")[0]
        if model == "mock":
            continue
        if model not in loop_data:
            loop_data[model] = {}
        exp_name = int_data["meta"]["experiment_name"]
        moves = get_moves(int_data)
        num_loops = count_loops(moves)
        if exp_name not in loop_data[model]:
            loop_data[model][exp_name] = []
        loop_data[model][exp_name].append(num_loops)

    # ---- Aggregate for Plotting ----
    # Bins: 1 loop, 2 loops, 3 loops, >=4 loops
    bins = ["1 loop", "2 loops", "3 loops", ">=4 loops"]
    bin_func = lambda n: (
        "1 loop" if n == 1 else
        "2 loops" if n == 2 else
        "3 loops" if n == 3 else
        ">=4 loops" if n > 3 else
        None
    )

    # For each model: [num tasks with 1 loop, with 2 loops, with 3 loops, with >=4 loops]
    counts_per_bin = {b: [] for b in bins}
    model_names_display = []

    experiment_display_map = {"small": "Small", "medium": "Medium", "large": "Large"}
    models_to_plot = ['o3', 'GPT-4.1', 'Claude-Sonnet-4']
    experiment_names = ["small", "medium", "large"]
    plot_stacked_loops_by_model_experiment_v2(
        loop_data,
        model_name_map,
        ordered_names,
        experiment_names,  # e.g., ['small', 'medium', 'large']
        experiment_display_map=experiment_display_map,  # {'small': 'Small', ...}
        models_to_plot=models_to_plot,
        show=True,
        save_path=None
    )