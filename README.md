# EscapeRoom

This repository contains **MapWorld** — a graph-based environment generator — and **EscapeRoom**, test-bed designed to probe
spatial reasoning, graph reasoning, and collaborative dialogue under multi-
modal grounding constraints in Large Mulimodal (Reasoning) Models.

## WIP

This thesis builds over ```clemcore==2.1.0```. The migration to `v3.3` will be active in `dev` branch soon


---

## Overview

### Components
- **`engine/`** — MapWorld environment:
  - Generates path, cycle, tree, ladder, and star graphs.
  - Assigns ADE20K categories and images to rooms.
  - Exposes a Gymnasium environment with optional pygame rendering.
- **`escaperoom/`** — Two-agent game:
  - **Guide**: knows the full map and target room description.
  - **Explorer**: navigates the map via text communication.
  - Includes game master, scoring logic, prompts, configs, and analysis scripts.
- **`tests/` & `utils/`** — Sanity checks, data cleaning, and instance creation tools.

---

## Installation

```bash
# Clone
git clone https://github.com/kushal-10/mapworld-thesis.git
cd mapworld-thesis

# Virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Add repo to PYTHONPATH
source ./prepare_path.sh
``` 

## Quickstart 

Add a multimodal model like `GPT-4.1` in `model_registry.json` (already included here). Add the openai API key in key.json.
Run the following:

```python
clem run -g escaperoom -m gpt-4.1
```

More details on how this game/enviroment is created using clemcore - [https://github.com/clp-research/clemcore](https://github.com/clp-research/clemcore)

## Results

The results including various open source and commercial Large Multimodal (Reasoning) Models can be found in this repo - [https://github.com/kushal-10/escaperoom-results/tree/main](https://github.com/kushal-10/escaperoom-results/tree/main)