import os
import ast
import json
import requests
from io import BytesIO
from collections import defaultdict, Counter

from tqdm import tqdm
from PIL import Image
import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.patches import FancyBboxPatch
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
        x, y = ast.literal_eval(coord_str)
        positions[coord_str] = (x, -y)
        G.add_node(coord_str)

    # Setup edges
    for src, dst in metadata.get('unnamed_edges', []):
        src_str = str(ast.literal_eval(src))
        dst_str = str(ast.literal_eval(dst))
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

    all_categories = [metadata['node_to_category'].get(node, "Unknown") for node in positions]
    total_counts = Counter(all_categories)
    category_instance_counter = defaultdict(int)

    start_node = metadata.get('start_node')
    target_node = metadata.get('target_node')

    # Draw nodes as resized image squares
    for node, (x, y) in positions.items():
        url = metadata['node_to_image'][node]
        try:
            img = fetch_and_resize_image(url, size=img_size)
            im = OffsetImage(img, zoom=zoom)
            if node == start_node:
                ab = AnnotationBbox(im, (x, y), frameon=True, box_alignment=(0.5, 0.5),
                                    bboxprops=dict(edgecolor='blue', linewidth=2, facecolor='none'))
            elif node == target_node:
                ab = AnnotationBbox(im, (x, y), frameon=True, box_alignment=(0.5, 0.5),
                                    bboxprops=dict(edgecolor='orange', linewidth=2, facecolor='none'))
            else:
                ab = AnnotationBbox(im, (x, y), frameon=True, box_alignment=(0.5, 0.5))

            ax.add_artist(ab)

            # Get the category
            category = metadata['node_to_category'].get(node, "Unknown")
            category_instance_counter[category] += 1
            count = category_instance_counter[category]

            # Format label
            if total_counts[category] == 1:
                label = category  # Only one instance, no number
            else:
                label = f"{category}{count}"  # Multiple instances, use numbering

            # Decide label position (above or below)
            label_y_offset = 0.4
            max_y = max(pos[1] for pos in positions.values())
            y_offset = -label_y_offset if y > 0.8 * max_y else label_y_offset

            # Add text label
            ax.text(x, y + y_offset, label, ha='center', va='center', fontsize=8)

        except Exception as e:
            print(f"Failed to load or resize image for node {node}: {e}")

    # Save figure
    fig.savefig(output_path, bbox_inches='tight')
    plt.close(fig)


def main():
    instance_path = os.path.join("escaperoom", "in", "instances.json")
    out_dir = os.path.join("escaperoom", "in", "instance_images_higher_label")
    os.makedirs(out_dir, exist_ok=True)
    with open(instance_path) as f:
        instances = json.load(f)
    for exp in tqdm(instances["experiments"]):
        exp_name = exp["name"]
        game_instances = exp["game_instances"]
        for metadata in game_instances:
            id = metadata["game_id"]
            out_sub_dir = os.path.join(out_dir, exp_name)
            os.makedirs(out_sub_dir, exist_ok=True)
            output_png = os.path.join(out_sub_dir, f"{id}.png")
            draw_graph(metadata, output_png)


if __name__ == '__main__':
    main()
