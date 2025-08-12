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

for interaction_file in interaction_files:
    int_data = load_json(interaction_file)
    model_name = int_data["meta"]["dialogue_pair"]

    exp_name = int_data['meta']["experiment_name"]
    game_id = int_data['meta']["game_id"]

    exps = [
        "small", "medium", "large"
            # "no_ambiguity", "medium_ambiguity", "high_ambiguity",
            # "low_dual_ambiguity", "medium_dual_ambiguity", "high_dual_ambiguity",
            # "path", "ladder", "tree",
            # "adjacent", "near", "far"
            ]

    if exp_name in exps:
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

        if exp_name not in abort_data[model]:
            abort_data[model][exp_name] = [val]
        else:
            abort_data[model][exp_name].append(val)

        if exp_name not in loop_data[model]:
            loop_data[model][exp_name] = [n_loops]
        else:
            loop_data[model][exp_name].append(n_loops)

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


# --- Define bin_func for loop data ---
def bin_func(n):
    if n == 0: return "0"
    if n == 1: return "1"
    if n == 2: return "2"
    if n == 3: return "3"
    if n > 3: return ">4"
    return None


def plot_grouped_metric(data_dict, metric_name, abort_types=None, bins=None, questions_moves=False):
    # data_dict: model -> exp_name -> list of metric values
    for group, models in groups.items():
        x = []
        group_data = {m: {e: [] for e in exp_names} for m in models}
        for m in models:
            for i, e in enumerate(exp_names):
                vals = []
                if m in data_dict and e in data_dict[m]:
                    for v in data_dict[m][e]:
                        vals.append(v)
                group_data[m][e] = vals
                x.append(f"{model_name_map.get(m, m)} {exp_disp[i]}")
        # Prepare traces
        traces = []
        if abort_types:  # For abort data
            for idx, atype in enumerate(abort_types):
                y = []
                for m in models:
                    for e in exp_names:
                        y.append(sum(1 for v in group_data[m][e] if v == atype))
                traces.append(go.Bar(
                    name=abort_types[atype],
                    x=x,
                    y=y,
                    marker_color=pio.templates['plotly'].layout.colorway[idx]
                ))
        elif bins:  # For loop data
            for idx, b in enumerate(bins):
                y = []
                for m in models:
                    for e in exp_names:
                        vals = group_data[m][e]
                        y.append(sum(1 for v in vals if bin_func(v)==b))
                traces.append(go.Bar(
                    name=f"{b} loops",
                    x=x,
                    y=y,
                    marker_color=pio.templates['plotly'].layout.colorway[idx]
                ))
        elif questions_moves:
            # y1: questions asked, y2: total moves, y3: efficient moves
            yq, ytm, yem = [], [], []
            for m in models:
                for e in exp_names:
                    qs = sum(data_dict["questions"][m][e]) if m in data_dict["questions"] and e in data_dict["questions"][m] else 0
                    tms = sum(data_dict["moves"][m][e]) if m in data_dict["moves"] and e in data_dict["moves"][m] else 0
                    ems = sum(data_dict["eff_moves"][m][e]) if m in data_dict["eff_moves"] and e in data_dict["eff_moves"][m] else 0
                    yq.append(qs)
                    ytm.append(tms)
                    yem.append(ems)
            traces.append(go.Bar(
                name="Questions Asked",
                x=x,
                y=yq,
                marker_color=pio.templates['plotly'].layout.colorway[4],
                offsetgroup=0
            ))
            traces.append(go.Bar(
                name="Efficient Moves",
                x=x,
                y=yem,
                marker_color=pio.templates['plotly'].layout.colorway[2],
                offsetgroup=1
            ))
            traces.append(go.Bar(
                name="Other Moves",
                x=x,
                y=[tm-em for tm,em in zip(ytm,yem)],
                marker_color=pio.templates['plotly'].layout.colorway[6],
                offsetgroup=1,
                base=yem,
                showlegend=True
            ))

        # Add vertical separators between each experiment set
        shapes = []
        for i in range(1, len(models)):
            x0 = i * len(exp_names) - 0.5
            shapes.append({
                "type": "line",
                "x0": x0, "x1": x0,
                "y0": 0, "y1": 1,
                "xref": "x", "yref": "paper",
                "line": {"color": "gray", "width": 2, "dash": "dot"},
            })
        fig = go.Figure(data=traces)
        fig.update_layout(
            barmode='group' if not questions_moves else 'relative',
            xaxis_title='',
            yaxis_title='Count',
            title=f"{metric_name} - {group}",
            legend_title_text='Metric',
            shapes=shapes,
        )
        fig.show()

# Model map and display order (as in your script)
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
    # Group 1 -High Performers
    'o3',
    'GPT-4.1',
    'Claude-Sonnet-4',

    # Group 2 -Mid Performers
    'o4-mini',
    'GPT-4.1-mini',
    'GLM-4.1V-9B-Th',
    'InternVL3-38B',
    'Mistral-Small-3.1-24B',

    # Group 3 - Low Performers
    'Llama-4-Maverick',
    'InternVL3-14B',
    'InternVL3-78B',
    'InternVL3-8B'
]

# --- Data collection (from your loop, keep as is) ---
# (Assume the data structures abort_data, loop_data, move_data, eff_move_data, question_data are filled as above.)

# ---- Abort Data Plot ----
abort_types = {0: "Invalid value", 1: "Moves exceeded", 2: "Turns exceeded"}  # Update if your abort reasons differ
abort_colors = pio.templates['plotly'].layout.colorway[:3]

abort_counts = {atype: [] for atype in abort_types}
for orig_name in ordered_names:
    orig_key = None
    for k, v in model_name_map.items():
        if v == orig_name:
            orig_key = k
            break
    if orig_key not in abort_data:
        for atype in abort_types:
            abort_counts[atype].append(0)
        continue
    vals = []
    for exp_vals in abort_data[orig_key].values():
        vals += exp_vals
    for atype in abort_types:
        abort_counts[atype].append(sum(1 for v in vals if v == atype))

traces = [
    go.Bar(
        name=abort_types[atype],
        x=ordered_names,
        y=abort_counts[atype],
        marker_color=abort_colors[i]
    ) for i, atype in enumerate(abort_types)
]
fig = go.Figure(data=traces)
fig.update_layout(
    barmode='group',
    xaxis_title='Model',
    yaxis_title='Num Aborts',
    title='Distribution of Abort Types per Model',
    legend_title_text='Abort Reason'
)
fig.show()

# ---- Loop Data Plot ----
bins = ["0", "1", "2", "3", ">4"]
def bin_func(n):
    if n == 0: return "0"
    if n == 1: return "1"
    if n == 2: return "2"
    if n == 3: return "3"
    if n > 3: return ">4"
    return None

loop_counts = {b: [] for b in bins}
for orig_name in ordered_names:
    orig_key = None
    for k, v in model_name_map.items():
        if v == orig_name:
            orig_key = k
            break
    if orig_key not in loop_data:
        for b in bins:
            loop_counts[b].append(0)
        continue
    vals = []
    for exp_vals in loop_data[orig_key].values():
        vals += exp_vals
    bin_count = {b: 0 for b in bins}
    for n in vals:
        b = bin_func(n)
        if b:
            bin_count[b] += 1
    for b in bins:
        loop_counts[b].append(bin_count[b])

traces = [
    go.Bar(
        name=f"{b} loops",
        x=ordered_names,
        y=loop_counts[b],
        marker_color=pio.templates['plotly'].layout.colorway[i]
    ) for i, b in enumerate(bins)
]
fig = go.Figure(data=traces)
fig.update_layout(
    barmode='group',
    xaxis_title='Model',
    yaxis_title='Number of Tasks',
    title='Tasks by Number of Loops per Model',
    legend_title_text='Number of Loops'
)
fig.show()

# ---- Combined Plot: Questions and Moves (with Efficient Moves stacked) ----

# Aggregate per model (mean or sum—use sum for counts)
q_list, tm_list, em_list = [], [], []
for orig_name in ordered_names:
    orig_key = None
    for k, v in model_name_map.items():
        if v == orig_name:
            orig_key = k
            break
    # All experiment values together for this model:
    qs, tms, ems = [], [], []
    if orig_key in question_data:
        for exp_vals in question_data[orig_key].values():
            qs += exp_vals
    if orig_key in move_data:
        for exp_vals in move_data[orig_key].values():
            tms += exp_vals
    if orig_key in eff_move_data:
        for exp_vals in eff_move_data[orig_key].values():
            ems += exp_vals
    q_list.append(sum(qs) if qs else 0)
    tm_list.append(sum(tms) if tms else 0)
    em_list.append(sum(ems) if ems else 0)

# Bar for questions
trace_q = go.Bar(
    name="Questions Asked",
    x=ordered_names,
    y=q_list,
    marker_color=pio.templates['plotly'].layout.colorway[4],
    offsetgroup=0
)
# Stacked bars for moves
trace_tm = go.Bar(
    name="Total Moves",
    x=ordered_names,
    y=[tm - em for tm, em in zip(tm_list, em_list)],
    marker_color=pio.templates['plotly'].layout.colorway[6],
    offsetgroup=1,
    base=em_list,
    showlegend=True
)
trace_em = go.Bar(
    name="Efficient Moves",
    x=ordered_names,
    y=em_list,
    marker_color=pio.templates['plotly'].layout.colorway[2],
    offsetgroup=1
)
fig = go.Figure(data=[trace_q, trace_em, trace_tm])
fig.update_layout(
    barmode='relative',
    xaxis_title='Model',
    yaxis_title='Count',
    title='Questions vs Total Moves (Efficient Moves Highlighted)',
    legend_title_text='Metric'
)
fig.show()