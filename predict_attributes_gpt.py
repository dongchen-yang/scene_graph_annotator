#!/usr/bin/env python3
"""
Predict object attributes with GPT-4 Vision.

For every scene found in data/validation_results/ this script:
  - Finds the per-object images in data/images/{dataset}/{scene_id}/
  - Sends them to GPT-4 Vision and asks for attributes across 9 categories
  - Saves predictions as data/gpt_predictions/{dataset}/{scene_id}/scene_graph.json
    (same schema as scenegraphs_sampled scene_graph.json files)

The saved files can be consumed directly by evaluate_gpt_on_attribute_prediction.py
or by the existing evaluate_attribute.py / evaluate_attribute_all.py.

Usage:
  export OPENAI_API_KEY=sk-...
  python predict_attributes_gpt.py
  python predict_attributes_gpt.py --gpt-model gpt-4o-mini --max-images 2
  python predict_attributes_gpt.py --overwrite          # regenerate cached scenes
"""

import argparse
import base64
import json
import os
import time
import uuid
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

from openai import OpenAI

from evaluate_attribute import find_object_images
from evaluate_attribute_all import extract_scene_id


# ---------------------------------------------------------------------------
# Attribute schema (aligned with scene graph annotation)
# ---------------------------------------------------------------------------

ATTRIBUTE_TYPES: List[str] = [
    "color", "shape", "material", "texture",
    "size", "function", "style", "text_label", "state",
]

_SYSTEM_PROMPT = """
### INSTRUCTIONS ###
You are an assistant tasked with extracting the attributes of an object from an image.
Given the object category name and image views of an object, please identify the attributes of the object which you can discern from any of the images based on the categories.
The object of interest should be marked with the ID label shown in the image and the red outline around the object.

Requirements:
- Attributes should not be conflicting across views.
- Only include those attributes which you are highly confident in.
- Provide only the JSON output based on the extracted information.

The JSON format is as follows, with the provided definitions and examples:
{
    "color": list of attributes describing the main colors of the object (e.g., "red", "blue", "green"),
    "size": list of attributes describing how small or large the object (e.g., "small", "large", "short", "tall"),
    "shape": list of attributes representing the shape of the object (e.g., "round", "square", "circular", "rectangular", "cylindrical"),
    "material": list of attributes describing the materials likely comprising the object (e.g., "wooden", "metal", "plastic"),
    "texture": list of attributes describing how the object would feel if touched (e.g., "smooth", "rough", "bumpy", "squishy", "comfortable"),
    "function": list of attributes describing what the object does (e.g., "for sitting on", "for eating food on"),
    "style": list of attributes describing the aesthetic style of the object (e.g., "modern", "vintage", "retro"),
    "text_label": list of attributes describing any text on the object, not including the ID mark of the object. For text labels, explicitly preface the attribute with the word "labeled" and the text in quotes (e.g., "labeled 'exit'"),
    "state": list of attributes describing a changeable state of the object (e.g., "open", "closed", "folded"). If the object does not have a changeable state, return an empty list.
}
All attribute types must be present in the JSON. Please use an empty list if no attributes are described for a particular attribute type. Any relationships to other objects should not be included.
You should return a JSON and only the JSON. Avoid including other text or explanations.
"""


# ---------------------------------------------------------------------------
# Core GPT Vision call
# ---------------------------------------------------------------------------

def _encode_image(path: str) -> str:
    """Return base64-encoded PNG/JPEG bytes as a UTF-8 string."""
    with open(path, "rb") as fh:
        return base64.b64encode(fh.read()).decode("utf-8")


def predict_attributes_with_gpt(
    client: OpenAI,
    object_label: str,
    image_paths: List[str],
    max_images: int = 3,
    model: str = "gpt-4.1",
    max_retries: int = 3,
) -> Dict[str, List[str]]:
    """
    Call GPT-4 Vision to predict visual attributes for one object.

    Args:
        client:        Initialised OpenAI client.
        object_label:  Object class name (e.g. "chair", "wall").
        image_paths:   Paths to per-object RGB crop images.
        max_images:    Maximum images included in the API request.
        model:         GPT model identifier.
        max_retries:   Retry budget for API / JSON-parse failures.

    Returns:
        Dict mapping attribute type -> list of attribute name strings.
        Returns an empty dict if every attempt fails.
    """
    if not image_paths:
        return {}

    image_content: List[dict] = []
    for img_path in image_paths[:max_images]:
        try:
            b64 = _encode_image(img_path)
            image_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{b64}",
                    "detail": "low",
                },
            })
        except Exception as exc:
            print(f"    Warning: could not encode {img_path}: {exc}")

    if not image_content:
        return {}

    user_content: List[dict] = [
        {"type": "text", "text": f"Object category: {object_label}"},
        *image_content,
    ]

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user",   "content": user_content},
                ],
                max_tokens=512,
                temperature=0.1,
            )
            raw = response.choices[0].message.content.strip()

            # Strip optional markdown code fences
            if raw.startswith("```"):
                parts = raw.split("```")
                raw = parts[1]
                if raw.lower().startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()

            parsed = json.loads(raw)

            # Normalise: keep only known types, lower-case all values
            result: Dict[str, List[str]] = {}
            for atype in ATTRIBUTE_TYPES:
                vals = parsed.get(atype, [])
                if isinstance(vals, list):
                    result[atype] = [
                        str(v).strip().lower()
                        for v in vals
                        if v and isinstance(v, (str, int, float))
                    ]
            return result

        except json.JSONDecodeError as exc:
            print(f"    Warning: JSON parse error (attempt {attempt + 1}/{max_retries}): {exc}")
            if attempt < max_retries - 1:
                time.sleep(1)
        except Exception as exc:
            print(f"    Warning: API error (attempt {attempt + 1}/{max_retries}): {exc}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)

    return {}


def attrs_to_scene_graph_entries(
    attrs_by_type: Dict[str, List[str]],
    object_id: int,
) -> List[Dict]:
    """Convert {type: [names]} to a list of scene-graph attribute dicts."""
    entries = []
    for attr_type, names in attrs_by_type.items():
        for name in names:
            if name:
                entries.append({
                    "id": uuid.uuid4().hex[:8],
                    "object_id": object_id,
                    "name": name,
                    "type": attr_type,
                })
    return entries


# ---------------------------------------------------------------------------
# Scene-level prediction pipeline
# ---------------------------------------------------------------------------

def generate_gpt_predictions(
    base_dir: str,
    client: OpenAI,
    gpt_model: str = "gpt-4.1",
    max_images: int = 3,
    output_dir: str = "data/gpt_predictions",
    overwrite: bool = False,
    limit_scenes: int = 0,
) -> Dict[str, int]:
    """
    Iterate over every scene that has a ground-truth file in
    data/validation_results/ and generate GPT attribute predictions for each
    GT object that has at least one image.

    Output files:
        {output_dir}/{dataset}/{scene_id}/scene_graph.json

    The format mirrors scenegraphs_sampled scene_graph.json so that
    load_predictions() in evaluate_attribute.py works without modification.

    Args:
        limit_scenes: Stop after processing this many scenes (0 = no limit).

    Returns:
        stats dict with processing counters.
    """
    base_path = Path(base_dir)
    output_base = base_path / output_dir
    images_base = base_path / "data" / "images"

    stats: Dict[str, int] = {
        "total_scenes": 0,
        "skipped_scenes": 0,
        "total_objects": 0,
        "objects_with_images": 0,
        "objects_no_images": 0,
        "api_errors": 0,
    }

    for dataset in ("3rscan", "scannet"):
        validation_dir = base_path / "data" / "validation_results" / dataset
        scene_graph_dir = base_path / "data" / "scenegraphs_sampled" / dataset

        if not validation_dir.exists():
            print(f"Skipping {dataset}: validation dir not found ({validation_dir})")
            continue

        val_files = sorted(validation_dir.glob("annotations_*.json"))
        print(f"\n{dataset.upper()}: found {len(val_files)} scene(s) with ground truth")

        for val_file in val_files:
            scene_id = extract_scene_id(val_file.name)
            scene_graph_file = scene_graph_dir / scene_id / "scene_graph.json"

            if not scene_graph_file.exists():
                print(f"  Warning: scene graph missing for {scene_id} – skipping")
                continue

            out_dir = output_base / dataset / scene_id
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file = out_dir / "scene_graph.json"

            stats["total_scenes"] += 1

            if limit_scenes and stats["total_scenes"] > limit_scenes:
                print(f"  Reached --limit-scenes {limit_scenes}, stopping.")
                return stats

            if out_file.exists() and not overwrite:
                print(f"  {scene_id}: cached – skipping (use --overwrite to regenerate)")
                stats["skipped_scenes"] += 1
                continue

            print(f"\n  [{dataset}] {scene_id}")

            # Build object_id -> label mapping from the sampled scene graph
            with open(scene_graph_file) as fh:
                scene_graph = json.load(fh)

            obj_id_to_label: Dict[int, str] = {}
            for obj in scene_graph.get("objects", []):
                labels = obj.get("labels", ["object"])
                obj_id_to_label[int(obj["id"])] = labels[0] if labels else "object"

            # Collect GT object IDs from the validation file
            with open(val_file) as fh:
                val_data = json.load(fh)

            gt_object_ids: set = set()
            if "attributes" in val_data:
                for attr in val_data["attributes"].get("predicted", {}).get("items", []):
                    if attr.get("validation") == "correct":
                        gt_object_ids.add(int(attr["object_id"]))
                for attr in val_data["attributes"].get("added", []):
                    gt_object_ids.add(int(attr["object_id"]))

            all_attributes: List[Dict] = []

            for obj_id in sorted(gt_object_ids):
                stats["total_objects"] += 1
                label = obj_id_to_label.get(obj_id, "object")

                img_paths = find_object_images(
                    scene_id, obj_id, dataset, str(images_base),
                )

                if not img_paths:
                    print(f"    Object {obj_id:3d} ({label}): no images – skipping")
                    stats["objects_no_images"] += 1
                    continue

                stats["objects_with_images"] += 1
                print(
                    f"    Object {obj_id:3d} ({label}): {len(img_paths)} image(s)",
                    end=" ... ", flush=True,
                )

                attrs_by_type = predict_attributes_with_gpt(
                    client, label, img_paths,
                    max_images=max_images,
                    model=gpt_model,
                )

                if attrs_by_type:
                    entries = attrs_to_scene_graph_entries(attrs_by_type, obj_id)
                    all_attributes.extend(entries)
                    print(", ".join(e["name"] for e in entries))
                else:
                    print("no attributes returned")
                    stats["api_errors"] += 1

            out_data = {
                "scene_id": scene_id,
                "dataset": dataset,
                "prediction_model": gpt_model,
                "attributes": all_attributes,
            }
            with open(out_file, "w") as fh:
                json.dump(out_data, fh, indent=2)
            print(f"  Saved {len(all_attributes)} attributes → {out_file}")

    return stats


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Predict object attributes with GPT-4 Vision and save results "
                    "as scene-graph JSON files.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--base-dir", default=".",
        help="Root of the scene_graph_annotation project (contains data/)",
    )
    parser.add_argument(
        "--predictions-dir", default="data/gpt_predictions",
        help="Output directory for predicted scene_graph.json files",
    )
    parser.add_argument(
        "--api-key", default=None,
        help="OpenAI API key (default: OPENAI_API_KEY env var)",
    )
    parser.add_argument(
        "--gpt-model", default="gpt-4.1",
        help="GPT model to use",
    )
    parser.add_argument(
        "--max-images", type=int, default=3,
        help="Maximum images per object sent to GPT",
    )
    parser.add_argument(
        "--overwrite", action="store_true",
        help="Regenerate predictions even when cached output already exists",
    )
    parser.add_argument(
        "--limit-scenes", type=int, default=0,
        help="Stop after processing this many scenes, useful for testing (0 = no limit)",
    )

    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        parser.error(
            "OpenAI API key required. "
            "Set OPENAI_API_KEY or pass --api-key."
        )

    client = OpenAI(api_key=api_key)

    print("=" * 80)
    print("GENERATING GPT ATTRIBUTE PREDICTIONS")
    print(f"  GPT model      : {args.gpt_model}")
    print(f"  Max images/obj : {args.max_images}")
    print(f"  Output dir     : {args.predictions_dir}")
    print("=" * 80)

    stats = generate_gpt_predictions(
        args.base_dir,
        client,
        gpt_model=args.gpt_model,
        max_images=args.max_images,
        output_dir=args.predictions_dir,
        overwrite=args.overwrite,
        limit_scenes=args.limit_scenes,
    )

    print("\n" + "=" * 80)
    print("PREDICTION SUMMARY")
    print(f"  Total scenes processed : {stats['total_scenes']}")
    print(f"  Scenes skipped (cached): {stats['skipped_scenes']}")
    print(f"  Total GT objects       : {stats['total_objects']}")
    print(f"  Objects with images    : {stats['objects_with_images']}")
    print(f"  Objects without images : {stats['objects_no_images']}")
    print(f"  API / parse errors     : {stats['api_errors']}")
    print("=" * 80)


if __name__ == "__main__":
    main()
