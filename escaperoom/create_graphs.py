import os
import json
import glob
import requests
from io import BytesIO
from PIL import Image
import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.offsetbox import OffsetImage, AnnotationBbox


def fetch_and_resize_image(url, size=(100, 100)):
    """Fetches an image from a URL, resizes it to 'size', and returns a PIL Image."""
    response = requests.get(url)
    response.raise_for_status()
    img = Image.open(BytesIO(response.content)).convert("RGBA")
    # Use LANCZOS resampling for resizing (ANTIALIAS deprecated)
    return img.resize(size, resample=Image.LANCZOS)


def draw_graph(metadata, output_path, zoom=0.5, img_size=(100, 100)):
    """
    Draws and saves a graph based on metadata.

    - metadata: dict containing node_to_image and unnamed_edges
    - output_path: path to save the generated figure
    - zoom: scaling factor for node images
    - img_size: tuple for resizing node images
    """
    G = nx.Graph()
    positions = {}

    # Setup nodes
    for coord_str, url in metadata['node_to_image'].items():
        x, y = eval(coord_str)
        positions[coord_str] = (x, -y)
        G.add_node(coord_str)

    # Setup edges
    for src, dst in metadata.get('unnamed_edges', []):
        src_str = str(tuple(src))
        dst_str = str(tuple(dst))
        if src_str in G and dst_str in G:
            G.add_edge(src_str, dst_str)

    # Create output directory
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Plot
    fig, ax = plt.subplots()
    ax.set_axis_off()

    # Draw edges
    for u, v in G.edges():
        x1, y1 = positions[u]
        x2, y2 = positions[v]
        ax.plot([x1, x2], [y1, y2], linewidth=1, color='gray')

    # Draw nodes as resized image squares
    for node, (x, y) in positions.items():
        url = metadata['node_to_image'][node]
        try:
            img = fetch_and_resize_image(url, size=img_size)
            im = OffsetImage(img, zoom=zoom)
            ab = AnnotationBbox(im, (x, y), frameon=True, box_alignment=(0.5, 0.5))
            ax.add_artist(ab)
        except Exception as e:
            print(f"Failed to load or resize image for node {node}: {e}")

    # Save figure
    fig.savefig(output_path, bbox_inches='tight')
    plt.close(fig)


def main():
    # Load all instances
    instances_path = os.path.join('escaperoom', 'in', 'instances.json')
    with open(instances_path, 'r') as f:
        data = json.load(f)

    # Build lookup: exp_name -> {game_id: metadata}
    lookup = {}
    for exp in data.get('experiments', []):
        name = exp.get('name')
        lookup[name] = {inst['game_id']: inst for inst in exp.get('game_instances', [])}

    # Find all interactions.json files
    pattern = os.path.join('results', '*', 'escape_room', '*', 'episode_*', 'interactions.json')
    for interactions_path in glob.glob(pattern):
        # Derive experiment folder and episode
        parts = interactions_path.split(os.sep)
        exp_folder = parts[-3]
        episode_folder = parts[-2]
        # Extract experiment name and game_id
        _, exp_name = exp_folder.split('_', 1)
        game_id = int(episode_folder.split('_')[1])

        # Lookup metadata
        metadata = lookup.get(exp_name, {}).get(game_id)
        if not metadata:
            print(f"Metadata not found for {exp_folder}, game {game_id}")
            continue

        # Save graph.png alongside interactions.json
        output_png = os.path.join(os.path.dirname(interactions_path), 'graph.png')
        print(f"Drawing graph for {exp_folder}, episode {episode_folder} -> {output_png}")
        draw_graph(metadata, output_png)

if __name__ == '__main__':
    main()
