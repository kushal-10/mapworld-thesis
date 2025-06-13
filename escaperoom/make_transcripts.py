import os
import json
import glob
from io import BytesIO
import requests
from PIL import Image, ImageDraw, ImageFont
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import textwrap

# Init Config
DATA_ROOT = 'escaperoom/in/instances.json'
INTERACTIONS_PATTERN = os.path.join('results', '*', 'escape_room', '*', 'episode_*', 'interactions.json')
ROBOT_PATH = 'engine/resources/robot.png'
ORACLE_PATH = 'engine/resources/oracle.png'
NODE_IMG_SIZE = (128, 128)
ROBOT_IMG_SIZE = (64, 64)
ORACLE_IMG_SIZE = (64, 64)
GRAPH_ZOOM = 0.5
FONT = ImageFont.load_default()
PADDING = 10
TEXT_WIDTH = 40

# Direction mapping according to GymEnv
dir_map = {'north': (0, 1), 'south': (0, -1), 'east': (1, 0), 'west': (-1, 0)}


def fetch_and_resize_image(url, size):
    """
    Args:
        url: URL of the image from clembench serve
        size: New size of the room image to display in graph in px

    Returns:

    """
    resp = requests.get(url)
    resp.raise_for_status()
    img = Image.open(BytesIO(resp.content)).convert('RGBA')
    return img.resize(size, resample=Image.LANCZOS)


def render_graph_image(positions, edges, node_imgs, robot_img, current_node):
    """
    Render the graph to a PIL image via saving to buffer to preserve aspect ratio.

    Args
        positions: Positions of the nodes in the graph
        edges: Edges of the nodes in the graph
        node_imgs: Node images to render
        robot_img: Robot/Explorer image to render
        current_node: Current node o the agent
    """
    fig, ax = plt.subplots()
    ax.set_axis_off()
    for u, v in edges:
        x1, y1 = positions[u]
        x2, y2 = positions[v]
        ax.plot([x1, x2], [y1, y2], linewidth=1, color='gray')
    for node, (x, y) in positions.items():
        img = node_imgs[node]
        im = OffsetImage(img, zoom=GRAPH_ZOOM)
        ab = AnnotationBbox(im, (x, y), frameon=True, box_alignment=(0.5, 0.5))
        ax.add_artist(ab)
    # robot
    x, y = positions[current_node]
    rb = OffsetImage(robot_img, zoom=GRAPH_ZOOM)
    ab_r = AnnotationBbox(rb, (x, y + 0.2), frameon=False)
    ax.add_artist(ab_r)
    # save to buffer
    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0)
    plt.close(fig)
    buf.seek(0)
    img = Image.open(buf).convert('RGB')
    return img


def create_combined(graph_img, oracle_img, robot_img, last_guide_msg, last_explorer_msg):
    """
    Combine graph image  transcript messages at turn
    Args:
        graph_img: Image to render of the graph - left half
        oracle_img:  Image to render of the oracle
        robot_img:  Image to render of the robot
        last_guide_msg: Message sent from the last turn from Guide
        last_explorer_msg: Message sent from the last turn from Exp

    Returns:

    """
    gw, gh = graph_img.size
    combined = Image.new('RGB', (2 * gw, gh), (255, 255, 255))
    # paste graph
    combined.paste(graph_img, (0, 0))
    draw = ImageDraw.Draw(combined)
    # vertical divider center of right half
    mid_x = gw + gw // 2
    draw.line([(mid_x, 0), (mid_x, gh)], fill='black')
    # guide area (right-half left column)
    if last_guide_msg:
        lines = textwrap.wrap(last_guide_msg, width=TEXT_WIDTH)
        y = PADDING
        combined.paste(oracle_img, (gw + PADDING, y), oracle_img)
        x_text = gw + PADDING + ORACLE_IMG_SIZE[0] + PADDING
        for line in lines:
            bbox = draw.textbbox((x_text, y), line, font=FONT)
            line_h = bbox[3] - bbox[1]
            draw.text((x_text, y), line, font=FONT, fill='black')
            y += line_h + PADDING
    # explorer area (right-half right column)
    if last_explorer_msg:
        lines = textwrap.wrap(last_explorer_msg, width=TEXT_WIDTH)
        y = PADDING
        explorer_x0 = gw + gw // 2
        combined.paste(robot_img, (explorer_x0 + PADDING, y), robot_img)
        x_text = explorer_x0 + PADDING + ROBOT_IMG_SIZE[0] + PADDING
        for line in lines:
            bbox = draw.textbbox((x_text, y), line, font=FONT)
            line_h = bbox[3] - bbox[1]
            draw.text((x_text, y), line, font=FONT, fill='black')
            y += line_h + PADDING
    return combined


def process_interactions():
    with open(DATA_ROOT) as f:
        data = json.load(f)
    lookup = {exp['name']:{inst['game_id']:inst for inst in exp['game_instances']} for exp in data['experiments']}
    for path in glob.glob(INTERACTIONS_PATTERN):
        with open(path) as f:
            inter = json.load(f)
        meta = inter['meta']
        md = lookup[meta['experiment_name']][meta['game_id']]
        # build graph data
        positions, node_imgs, edges = {}, {}, []
        for coord_str, url in md['node_to_image'].items():
            coord = tuple(eval(coord_str))
            positions[coord_str] = (coord[0], -coord[1])
            node_imgs[coord_str] = fetch_and_resize_image(url, NODE_IMG_SIZE)
        for src, dst in md.get('unnamed_edges', []):
            edges.append((str(tuple(src)), str(tuple(dst))))
        current = md['start_node']
        robot_img = Image.open(ROBOT_PATH).convert('RGBA').resize(ROBOT_IMG_SIZE, resample=Image.LANCZOS)
        oracle_img = Image.open(ORACLE_PATH).convert('RGBA').resize(ORACLE_IMG_SIZE, resample=Image.LANCZOS)
        last_guide, last_explorer = None, None
        out_dir = os.path.join(os.path.dirname(path), 'combined_graphs')
        os.makedirs(out_dir, exist_ok=True)
        for idx, turn in enumerate(inter['turns']):
            updated = False
            for i, act in enumerate(turn):
                frm, to = act['from'], act['to']
                typ = act['action']['type']
                cnt = act['action']['content']
                # move logic
                if frm.startswith('Player 2') and typ == 'get message' and cnt.startswith('MOVE:'):
                    if i + 1 < len(turn) and turn[i+1]['action']['type'] == 'move':
                        res = turn[i+1]['action']['content']
                        if res in ('valid', 'efficient', 'inefficient'):
                            direction = cnt.split('MOVE:')[1].strip()
                            dx, dy = dir_map.get(direction, (0, 0))
                            x0, y0 = eval(current)
                            new = (x0 + dx, y0 + dy)
                            if str(new) in positions:
                                current = str(new)
                            updated = True
                # Guide -> GM
                if frm.startswith('Player 1') and to == 'GM' and typ == 'get message':
                    last_guide = cnt
                    updated = True
                # Explorer -> GM
                if frm.startswith('Player 2') and to == 'GM' and typ == 'get message':
                    last_explorer = cnt
                    updated = True
            if updated:
                graph_img = render_graph_image(positions, edges, node_imgs, robot_img, current)
                combined = create_combined(graph_img, oracle_img, robot_img, last_guide, last_explorer)
                combined.save(os.path.join(out_dir, f'combined_{idx}.png'))
                print(f"Saved {path} -> combined_{idx}.png")

if __name__ == '__main__':
    process_interactions()