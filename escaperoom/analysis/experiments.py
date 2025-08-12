import os
import json
import plotly.graph_objs as go
import plotly.io as pio

from escaperoom.analysis.aborts import get_reason, load_json
from escaperoom.analysis.loops import get_moves, count_loops
from escaperoom.scorer import get_efficient_moves
from escaperoom.analysis.questions import analyse

instance_file = os.path.join("escaperoom", "in", "instances.json")
with open(instance_file, "r") as f:
    instances = json.load(f)

base_dir = "results"

interaction_files = []
for dirname, _, filenames in os.walk(base_dir):
    for filename in filenames:
        if filename.endswith("interactions.json"):
            interaction_files.append(os.path.join(dirname, filename))


abort_data = {}
loop_data = {}

move_data = {}
eff_move_data = {}
question_data = {}

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

def plot_questions_by_model_experiment(
    question_data,
    model_name_map,
    ordered_names,
    experiment_names,
    experiment_display_map=None,
    models_to_plot=None,
    show=True,
    save_path=None,
    tasks_per_experiment=10,  # NEW: set default to 10
):
    import plotly.graph_objs as go
    import plotly.io as pio

    if experiment_display_map is None:
        experiment_display_map = {k: k.capitalize() for k in experiment_names}
    if models_to_plot is not None:
        filtered_names = [m for m in ordered_names if m in models_to_plot]
    else:
        filtered_names = ordered_names.copy()

    # Gather per-experiment averages for each model
    avgs_per_exp = {expt: [] for expt in experiment_names}
    for model in filtered_names:
        orig_key = None
        for k, v in model_name_map.items():
            if v == model:
                orig_key = k
                break
        for expt in experiment_names:
            avg = 0
            if orig_key and orig_key in question_data and expt in question_data[orig_key]:
                vals = question_data[orig_key][expt]
                if len(vals) > 0:
                    avg = sum(vals) / len(vals)
                else:
                    avg = 0
            avgs_per_exp[expt].append(avg)

    # Plot: 3 bars per model, colored by experiment
    default_colors = pio.templates['plotly'].layout.colorway
    traces = []
    for i, expt in enumerate(experiment_names):
        traces.append(
            go.Bar(
                name=experiment_display_map.get(expt, expt),
                x=filtered_names,
                y=avgs_per_exp[expt],
                marker_color=default_colors[i % len(default_colors)]
            )
        )

    fig = go.Figure(traces)
    fig.update_layout(
        barmode='group',
        xaxis_title='Model',
        yaxis_title='Average Number of Questions',
        title='Average Number of Questions per Model per Experiment',
        legend_title_text='Experiment'
    )
    if show:
        fig.show()
    if save_path:
        fig.write_html(f"{save_path}/questions_by_model_experiment_avg.html")

def plot_moves_by_model_experiment(
    move_data,
    eff_move_data,
    model_name_map,
    ordered_names,
    experiment_names,
    experiment_display_map=None,
    models_to_plot=None,
    show=True,
    save_path=None
):
    import plotly.graph_objs as go
    import plotly.io as pio

    # Color pairs for (efficient, inefficient) moves for each experiment
    exp_colors = {
        'path': ['#4587A4', '#55BCEA'],  # blues dark, light
        'ladder': ['#e8432c', "#e79489"],  # reds
        'tree': ['#85ec34', '#b2f3b0'],  # greens
    }

    if experiment_display_map is None:
        experiment_display_map = {k: k.capitalize() for k in experiment_names}
    if models_to_plot is not None:
        filtered_names = [m for m in ordered_names if m in models_to_plot]
    else:
        filtered_names = ordered_names.copy()

    n_models = len(filtered_names)

    traces = []
    for eidx, expt in enumerate(experiment_names):
        eff_moves = []
        ineff_moves = []
        for model in filtered_names:
            orig_key = None
            for k, v in model_name_map.items():
                if v == model:
                    orig_key = k
                    break
            # Efficient and total moves
            eff = sum(eff_move_data.get(orig_key, {}).get(expt, []))
            tot = sum(move_data.get(orig_key, {}).get(expt, []))
            ineff = tot - eff
            eff_moves.append(eff)
            ineff_moves.append(max(0, ineff))  # No negative bars

        # Efficient moves (bottom stack)
        traces.append(
            go.Bar(
                name=f"{experiment_display_map[expt]}, Efficient",
                x=filtered_names,
                y=eff_moves,
                marker_color=exp_colors[expt][0],
                offsetgroup=str(eidx),
                width=0.2,
                legendgroup=f"{expt}-eff",
                showlegend=True
            )
        )
        # Inefficient moves (top stack)
        traces.append(
            go.Bar(
                name=f"{experiment_display_map[expt]}, Inefficient",
                x=filtered_names,
                y=ineff_moves,
                marker_color=exp_colors[expt][1],
                offsetgroup=str(eidx),
                base=eff_moves,
                width=0.2,
                legendgroup=f"{expt}-ineff",
                showlegend=True
            )
        )

    fig = go.Figure(traces)
    fig.update_layout(
        barmode='stack',
        xaxis_title='Model',
        yaxis_title='Number of Moves',
        title='Efficient and Inefficient Moves per Model per Experiment',
        legend_title_text='Moves and Experiment',
        bargap=0.25
    )
    if show:
        fig.show()
    if save_path:
        fig.write_html(f"{save_path}/moves_by_model_experiment.html")


for interaction_file in interaction_files:
    int_data = load_json(interaction_file)
    model_name = int_data["meta"]["dialogue_pair"]

    exp_name = int_data['meta']["experiment_name"]
    game_id = int_data['meta']["game_id"]


    model = model_name.split("-t0.0")[0]
    if model == "mock":
        continue
    if model not in abort_data:
        abort_data[model] = {}
    if model not in loop_data:
        loop_data[model] = {}
    if model not in move_data:
        move_data[model] = {}
    if model not in eff_move_data:
        eff_move_data[model] = {}
    if model not in question_data:
        question_data[model] = {}

    val = get_reason(int_data)
    moves = get_moves(int_data)
    n_loops = count_loops(moves)
    total_moves, eff_moves, aborted = get_efficient_moves(instances, exp_name, game_id, moves)
    qa, mm, em, fe, se = analyse(int_data)

    if exp_name not in move_data[model]:
        move_data[model][exp_name] = [total_moves]
    else:
        move_data[model][exp_name].append(total_moves)

    if exp_name not in eff_move_data[model]:
        eff_move_data[model][exp_name] = [eff_moves]
    else:
        eff_move_data[model][exp_name].append(eff_moves)

    if exp_name not in question_data[model]:
        question_data[model][exp_name] = [qa]
    else:
        question_data[model][exp_name].append(qa)



if __name__ == "__main__":
    experiment_display_map = {"path": "Path", "ladder": "Ladder", "tree": "Tree"}
    models_to_plot = ['o3', 'GPT-4.1', 'Claude-Sonnet-4']
    experiment_names = ["path", "ladder", "tree"]

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
    plot_questions_by_model_experiment(
        question_data,
        model_name_map,
        ordered_names,
        experiment_names,
        experiment_display_map=experiment_display_map,
        models_to_plot=None,
        show=True,
        save_path=None
    )

    plot_moves_by_model_experiment(
        move_data,
        eff_move_data,
        model_name_map,
        ordered_names,
        experiment_names,
        experiment_display_map=experiment_display_map,
        models_to_plot=None,
        show=True,
        save_path=None
    )