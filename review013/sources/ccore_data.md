---
license: mit
pretty_name: CCORE Three.js 3D GLB Assets
language:
- en
task_categories:
- text-generation
size_categories:
- 1K<n<10K
tags:
- 3d
- threejs
- glb
- game-assets
- code
- reasoning
- conversational
- html
- javascript
configs:
- config_name: conversations
  data_files:
  - split: train
    path:
    - data/train-00000.parquet
    - data/train-00001.parquet
    - data/train-00002.parquet
    - data/train-00003.parquet
    - data/train-00004.parquet
    - data/train-00005.parquet
    - data/train-00006.parquet
  - split: validation
    path:
    - data/validation-00000.parquet
- config_name: previews
  data_files:
  - split: train
    path:
    - previews/train-00000.parquet
    - previews/train-00001.parquet
    - previews/train-00002.parquet
    - previews/train-00003.parquet
    - previews/train-00004.parquet
    - previews/train-00005.parquet
    - previews/train-00006.parquet
    - previews/train-00007.parquet
    - previews/train-00008.parquet
    - previews/train-00009.parquet
    - previews/train-00010.parquet
    - previews/train-00011.parquet
    - previews/train-00012.parquet
    - previews/train-00013.parquet
  - split: validation
    path:
    - previews/validation-00000.parquet
    - previews/validation-00001.parquet
- config_name: meshes
  data_files:
  - split: train
    path:
    - meshes/train-00000.parquet
    - meshes/train-00001.parquet
    - meshes/train-00002.parquet
    - meshes/train-00003.parquet
    - meshes/train-00004.parquet
    - meshes/train-00005.parquet
    - meshes/train-00006.parquet
    - meshes/train-00007.parquet
    - meshes/train-00008.parquet
    - meshes/train-00009.parquet
  - split: validation
    path:
    - meshes/validation-00000.parquet
  default: true
dataset_info:
- config_name: conversations
  features:
  - name: id
    dtype: string
  - name: title
    dtype: string
  - name: domain
    dtype: string
  - name: messages
    list:
    - name: role
      dtype: string
    - name: content
      dtype: string
    - name: reasoning_content
      dtype: string
  splits:
  - name: train
    num_examples: 3501
    num_bytes: 226166218
  - name: validation
    num_examples: 417
    num_bytes: 26385907
  download_size: 82536659
  dataset_size: 252552125
- config_name: previews
  features:
  - name: id
    dtype: string
  - name: title
    dtype: string
  - name: domain
    dtype: string
  - name: image
    dtype: image
  splits:
  - name: train
    num_examples: 3501
    num_bytes: 246995824
  - name: validation
    num_examples: 417
    num_bytes: 28751585
  download_size: 269754648
  dataset_size: 275747409
---

<a href="#next-releases"><img src="assets/important-note.svg" alt="Important note — Next releases" width="380" /></a>

[![256 rendered examples across 40 domains](assets/dataset-grid-16x16.jpg)](assets/dataset-grid-16x16.jpg)

# CCORE Three.js 3D GLB Assets

**3,918 examples across 40 domains, with complete conversations, thinking traces, HTML/JavaScript responses, and a rendered reference for every asset.**

**All 3,918 examples were tested and rendered, and their exported GLB files were validated before inclusion in the dataset.**

From stylized characters and musical instruments to vehicles, laboratory equipment, industrial machinery, modular structures, and everyday props, this dataset focuses on creating reusable 3D assets through Three.js code. It includes static assets and examples with animation and interaction, with GLB export built into the scene code.

This is the dataset used to train [**CCORE GLB-3D-Coder — Qwen3.5-4B-GLB-3D-Coder**](https://huggingface.co/ccore/Qwen3.5-4B-GLB-3D-Coder).

## Dataset at a glance

| Split | Examples | Rendered references |
|:---|---:|---:|
| Train | 3,501 | 3,501 |
| Validation | 417 | 417 |
| **Total** | **3,918** | **3,918** |

The original training and validation split is preserved. The release contains the complete prompts, thinking traces, and response targets used for the final model, without truncation. The text and image configurations share the same identifiers, splits, and row order.

The conversations are in English. Requests range from short asset descriptions to detailed specifications covering shape, components, colors, materials, and motion.

## Domains and asset coverage

The dataset contains **40 annotated domains** and **2,903 distinct domain/subject labels**. A subject can have multiple examples with different instructions or configurations. Counts below describe dataset examples and subject labels.

| Domain | Samples | Distinct subjects | Example assets |
|:---|---:|---:|:---|
| Air and space transport | 119 | 83 | cargo airship, cargo glider, cargo shuttle |
| Battlefield scenery | 125 | 86 | frontier command post, frontier supply barricade, frontier signal tower |
| Bosses | 80 | 80 | dragon boss, wyvern boss, hydra boss |
| Camping and travel | 42 | 10 | camping tent, camp lantern, portable camping stove |
| Characters and NPCs | 216 | 216 | merchant, blacksmith, baker |
| Civilian characters | 41 | 10 | village merchant character, village blacksmith character, village farmer character |
| Companions and creatures | 139 | 139 | fox companion, wolf cub companion, dog companion |
| Creatures and companions | 43 | 10 | fox companion character, dog companion character, cat companion character |
| Cuisine and markets | 117 | 84 | bakery display counter, bakery serving cart, bakery ingredient rack |
| Electronics and optics | 47 | 10 | portable computer, desktop computer station, handheld radio |
| Enemies | 220 | 220 | goblin, orc, skeleton |
| Enemies and bosses | 38 | 10 | skeletal guard character, goblin scavenger character, orc gatekeeper character |
| Fantasy adventurers | 45 | 10 | human ranger character, dwarf warrior character, elf spellcaster character |
| Farming and homestead | 123 | 85 | orchard feeding station, orchard harvest cart, orchard storage shed |
| Festivals and ceremonies | 118 | 85 | harvest parade float, harvest ceremony arch, harvest festival booth |
| Fitness and rehabilitation | 47 | 10 | electric treadmill, stationary exercise bicycle, rowing exercise machine |
| Furniture and interiors | 45 | 10 | wooden dining chair, storage cupboard, single bed |
| Ground transport | 115 | 84 | courier motorcycle, courier buggy, courier hover bike |
| Household appliances | 42 | 10 | domestic washing machine, refrigerator, kitchen stove |
| Industrial machinery | 119 | 84 | mining drill rig, mining conveyor unit, mining hydraulic press |
| Interactive objects | 99 | 99 | door that can open and close, double door that can open and close, gate that can open and close |
| Items tools and pickups | 159 | 159 | health potion, mana potion, stamina potion |
| Laboratory and medical | 118 | 83 | botanical analysis station, botanical sample cabinet, botanical scanner bed |
| Modern specialists | 39 | 10 | firefighter character, paramedic character, construction worker character |
| Modular architecture | 100 | 100 | wall module, wall corner module, wall end module |
| Museum and field research | 114 | 84 | ancient exhibit case, ancient restoration table, ancient artifact pedestal |
| Musical instruments | 42 | 10 | acoustic guitar, electric bass guitar, upright piano |
| Nature and environment | 119 | 119 | oak tree, pine tree, palm tree |
| Nature and garden | 40 | 10 | oak tree, pine tree, palm tree |
| Props and furniture | 180 | 180 | wooden chair, wooden table, stool |
| Puzzle and gameplay markers | 120 | 84 | rune puzzle column, rune sequence console, rune path marker |
| Robots and constructs | 47 | 10 | warehouse helper robot character, medical assistant robot character, agricultural robot character |
| Sports and playgrounds | 120 | 85 | training goal frame, training climbing wall, training score board |
| Traps and hazards | 118 | 83 | spiked floor trap, spiked wall launcher, spiked pressure tunnel |
| Underwater structures | 120 | 85 | coral observation dome, coral sonar beacon, coral docking ring |
| Urban services | 122 | 85 | city bus stop, city parking meter, city utility box |
| Watercraft | 119 | 82 | fishing skiff, fishing canoe, fishing speedboat |
| Weapons and armor | 179 | 179 | short sword, long sword, great sword |
| Weapons armor and equipment | 41 | 10 | longsword, battle axe, war hammer |
| Workshop and repair | 41 | 10 | bench vise, drill press, angle grinder |
| **Total** | **3,918** | **2,903** | **40 domains** |

Machine-readable totals and split counts are provided in [domain-counts.csv](stats/domain-counts.csv) and [dataset-stats.json](stats/dataset-stats.json).

## Format

The **conversations** configuration contains conversational data in Parquet format. Rendered images are loaded separately through **previews**, so downloading images is optional.

| Field | Description |
|:---|:---|
| `id` | Stable asset identifier shared by both configurations. |
| `title` | Human-readable asset subject. |
| `domain` | Asset category from the domain table above. |
| `messages` | System instruction, user request, and full assistant response. |

Each message has `role`, `content`, and `reasoning_content`. The assistant's `reasoning_content` contains the thinking trace, and its `content` contains the complete response, including the HTML/JavaScript. System and user messages have a null `reasoning_content`.

The **previews** configuration contains `id`, `title`, `domain`, and an `image` feature for every example. These are rendered references for the included assets; they are separate from the text conversations. Animation and interaction cannot be fully represented by a single still image.

The **meshes** configuration, the default, contains `id`, `title`, `domain`, and a `mesh` feature with the GLB exported by each example's scene code, in the same splits and row order.

This release includes the data, images, and GLB files. The GLBs in **meshes** were exported with each example's own scene code.

## Usage

```python
from datasets import load_dataset

dataset = load_dataset("ccore/ThreeJS-3D-GLB-Assets", "conversations")
sample = dataset["train"][0]

messages = sample["messages"]
thinking = messages[-1]["reasoning_content"]
response = messages[-1]["content"]

# Optional rendered references, aligned by split, row order, and id.
previews = load_dataset("ccore/ThreeJS-3D-GLB-Assets", "previews")
assert previews["train"][0]["id"] == sample["id"]
image = previews["train"][0]["image"]
```

## Related releases

- [CCORE GLB-3D-Coder model](https://huggingface.co/ccore/Qwen3.5-4B-GLB-3D-Coder) — the model trained with this dataset, with GGUF and full model weights.
- [CCORE Three.js 3D Scenes](https://huggingface.co/datasets/ccore/ThreeJS-3D-Scenes) — a separate dataset covering a broad range of Three.js scenes.

## License

Released under the [MIT License](LICENSE), to the extent of the rights held by the dataset publisher.

## Next releases

Beyond this release, I want to build **larger, carefully reviewed datasets** and **more capable small models**, including specialized models in other areas.

I've developed and funded this work myself, and I'm releasing the **models, weights, and datasets free of charge to the community**.

Next, I'm planning **100,000 high-quality examples for 3D and general-purpose coding harnesses** to **train new small models** that can use tools, test their outputs, and refine their work through iteration.

I expect **creating these datasets and training the new models to require around 20 times the effort of the current project**. **I need the community's support to make this next stage possible.**

## Support the project

I cover the cost of data preparation, validation, experiments, and GPU training myself. If this dataset or the CCORE models are useful to you and you want to help fund larger datasets and future open releases, you can support the work directly:

### Ko-fi

[**Support CCORE on Ko-fi**](https://ko-fi.com/ccorecaio)

### Crypto donations

**Bitcoin (BTC) — Bitcoin Network (SegWit)**

`bc1qr2gnr9g0uzk8rmsq0k6xpjgg4l7r0rfyrq69e6`

**Ethereum (ETH) — Ethereum Mainnet (ERC20)**

`0xa17608FCdeAd9e717Cd42e04127175527b4E75CB`

**Solana (SOL / USDC / USDT) — Solana Network**

`GhNmYmezKi1uWGKZeVxgddjiRW2rYNHZrf84ZaMcnha`

Your support helps pay for compute, better datasets, and future public releases. Thank you for supporting independent open-source work.
