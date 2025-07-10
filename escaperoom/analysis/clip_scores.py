import requests
from itertools import combinations
from io import BytesIO
import os
import json

from PIL import Image
import clip
import torch
from sklearn.metrics.pairwise import cosine_similarity

device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"

model, preprocess = clip.load("ViT-B/32", device=device)

def get_clip_scores(node_to_image, node_to_category):
    # Load and preprocess images
    embeddings = {}
    for node, url in node_to_image.items():
        response = requests.get(url)
        image = Image.open(BytesIO(response.content)).convert("RGB")
        image_input = preprocess(image).unsqueeze(0).to(device)
        with torch.no_grad():
            embeddings[node] = model.encode_image(image_input).cpu().numpy()[0]

    similar_clip_scores = []
    different_clip_scores = []
    node_list = list(node_to_image.keys())
    for i, j in combinations(node_list, 2):
        emb1 = embeddings[i].reshape(1, -1)
        emb2 = embeddings[j].reshape(1, -1)
        score = cosine_similarity(emb1, emb2)[0][0]
        if node_to_category[i] == node_to_category[j]:
            similar_clip_scores.append(score)
        else:
            different_clip_scores.append(score)
    if similar_clip_scores:
        print(f"SIMILAR DATA - MAX: {max(similar_clip_scores)}, MIN: {min(similar_clip_scores)}, AVG: {sum(similar_clip_scores) / len(similar_clip_scores)}")
    if different_clip_scores:
        print(f"DIFFERENT DATA - MAX: {max(different_clip_scores)}, MIN: {min(different_clip_scores)}, AVG: {sum(different_clip_scores) / len(different_clip_scores)}")

if __name__ == "__main__":
    instances_path = os.path.join("escaperoom", "in", "instances.json")

    with open(instances_path) as f:
        instances = json.load(f)

    for exps in instances["experiments"]:
        game_instances = exps["game_instances"]
        print(f"Calculating clip scores for {exps['name']}")
        print("*"*50)
        for game_instance in game_instances:
            node_to_image = game_instance["node_to_image"]
            node_to_category = game_instance["node_to_category"]
            get_clip_scores(node_to_image, node_to_category)
            print("#"*10)


