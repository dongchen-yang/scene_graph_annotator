#!/usr/bin/env python3
"""
Evaluate GPT attribute predictions against ground truth using CLIP similarity.

Reads predictions from data/gpt_predictions/{dataset}/{scene_id}/scene_graph.json
(produced by predict_attributes_gpt.py) and ground truth from
data/validation_results/{dataset}/annotations_*.json.

Predictions cover 9 attribute categories: color, shape, material, texture,
size, function, style, text_label, and state.

Evaluation metrics and output format are identical to evaluate_attribute_all.py
so results can be compared directly.

Usage:
  python evaluate_gpt_on_attribute_prediction.py
  python evaluate_gpt_on_attribute_prediction.py --include-images
  python evaluate_gpt_on_attribute_prediction.py --predictions-dir data/gpt_predictions
  python evaluate_gpt_on_attribute_prediction.py --output my_results.json
"""

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

from evaluate_attribute import (
    CLIPSimilarityEvaluator,
    load_ground_truth,
    calculate_similarity_scores,
)
from evaluate_attribute_all import (
    aggregate_results,
    print_summary,
    save_detailed_results,
)


def evaluate_gpt_predictions(
    base_dir: str,
    evaluator: CLIPSimilarityEvaluator,
    gpt_predictions_dir: str = "data/gpt_predictions",
    num_trials: int = 10,
    include_images: bool = False,
    max_images: int = 3,
) -> Tuple[List[Dict], Dict[str, List[Dict]]]:
    """
    Evaluate GPT predictions against annotated ground truth.

    Loads:
      - Predictions : {gpt_predictions_dir}/{dataset}/{scene_id}/scene_graph.json
      - Ground truth: data/validation_results/{dataset}/annotations_{scene_id}_*.json

    Args:
        base_dir:            Root directory of the project.
        evaluator:           Initialised CLIPSimilarityEvaluator.
        gpt_predictions_dir: Directory containing GPT prediction files.
        num_trials:          Random-ordering trials for order-invariant CLIP score.
        include_images:      Also compute image-to-text CLIP similarity.
        max_images:          Max images per object for image-CLIP evaluation.

    Returns:
        (all_results, dataset_results) with the same structure used by
        evaluate_attribute_all.py, suitable for print_summary / save_detailed_results.
    """
    base_path = Path(base_dir)
    pred_base = base_path / gpt_predictions_dir

    all_results: List[Dict] = []
    dataset_results: Dict[str, List[Dict]] = {"3rscan": [], "scannet": []}

    print("\n" + "=" * 80)
    print("EVALUATING GPT PREDICTIONS")
    if include_images:
        print("Mode: Text-to-Text + Image-to-Text CLIP Similarity")
    else:
        print("Mode: Text-to-Text CLIP Similarity Only")
    print("=" * 80)

    for dataset in ("3rscan", "scannet"):
        val_dir = base_path / "data" / "validation_results" / dataset
        pred_dir = pred_base / dataset

        if not val_dir.exists():
            print(f"\n{dataset.upper()}: validation dir not found – skipping")
            continue
        if not pred_dir.exists():
            print(f"\n{dataset.upper()}: no GPT predictions in {pred_dir} – skipping")
            continue

        pred_files = sorted(pred_dir.glob("*/scene_graph.json"))
        print(f"\n{dataset.upper()}: {len(pred_files)} scene(s) with GPT predictions")

        for pred_file in pred_files:
            scene_id = pred_file.parent.name

            matches = sorted(val_dir.glob(f"annotations_{scene_id}_*.json"))
            if not matches:
                print(f"  Warning: no validation file for {scene_id} – skipping")
                continue
            val_file = matches[0]

            print(f"  Evaluating {scene_id} ...", end=" ", flush=True)

            try:
                ground_truth = load_ground_truth(str(val_file))

                with open(pred_file) as fh:
                    pred_data = json.load(fh)

                gpt_predictions: Dict[int, List[str]] = defaultdict(list)
                for attr in pred_data.get("attributes", []):
                    gpt_predictions[int(attr["object_id"])].append(attr["name"])

                results = calculate_similarity_scores(
                    ground_truth,
                    gpt_predictions,
                    evaluator,
                    num_random_trials=num_trials,
                    scene_id=scene_id,
                    dataset=dataset,
                    include_image_similarity=include_images,
                    max_images_per_object=max_images,
                )

                scene_result: Dict = {
                    "scene_id": scene_id,
                    "dataset": dataset,
                    "validation_file": str(val_file),
                    "scene_graph_file": str(pred_file),
                    "average_similarity": results["overall"]["average_similarity"],
                    "total_objects": results["overall"]["total_objects"],
                    "per_object": results["per_object"],
                }

                overall = results["overall"]
                if "average_image_gt_similarity" in overall:
                    scene_result["average_image_gt_similarity"] = overall["average_image_gt_similarity"]
                    scene_result["average_image_pred_similarity"] = overall["average_image_pred_similarity"]
                    scene_result["objects_with_images"] = overall["objects_with_images"]

                all_results.append(scene_result)
                dataset_results[dataset].append(scene_result)

                if include_images and "average_image_gt_similarity" in scene_result:
                    print(
                        f"Text={scene_result['average_similarity']:.4f}  "
                        f"Img-GT={scene_result['average_image_gt_similarity']:.4f}  "
                        f"Img-Pred={scene_result['average_image_pred_similarity']:.4f}  "
                        f"objs={scene_result['total_objects']}"
                    )
                else:
                    print(
                        f"similarity={scene_result['average_similarity']:.4f}  "
                        f"objs={scene_result['total_objects']}"
                    )

            except Exception as exc:
                print(f"ERROR: {exc}")
                import traceback
                traceback.print_exc()

    return all_results, dataset_results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate GPT attribute predictions against ground truth "
                    "using CLIP similarity (mirrors evaluate_attribute_all.py).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--base-dir", default=".",
        help="Root of the scene_graph_annotation project (contains data/)",
    )
    parser.add_argument(
        "--predictions-dir", default="data/gpt_predictions",
        help="Directory containing GPT prediction files "
             "(produced by predict_attributes_gpt.py)",
    )
    parser.add_argument(
        "--output", default="gpt_attribute_evaluation.json",
        help="Path for the output evaluation JSON",
    )
    parser.add_argument(
        "--clip-model", default="openai/clip-vit-base-patch32",
        help="CLIP model used for similarity scoring",
    )
    parser.add_argument(
        "--device", default=None,
        help="Torch device (cuda/cpu; default: auto-detect)",
    )
    parser.add_argument(
        "--num-trials", type=int, default=10,
        help="Random orderings averaged for order-invariant CLIP score",
    )
    parser.add_argument(
        "--include-images", action="store_true",
        help="Also compute image-to-text CLIP similarity",
    )
    parser.add_argument(
        "--max-images", type=int, default=3,
        help="Maximum images per object for image-CLIP evaluation",
    )

    args = parser.parse_args()

    print("Loading CLIP model ...")
    evaluator = CLIPSimilarityEvaluator(
        model_name=args.clip_model,
        device=args.device,
    )

    all_results, dataset_results = evaluate_gpt_predictions(
        args.base_dir,
        evaluator,
        gpt_predictions_dir=args.predictions_dir,
        num_trials=args.num_trials,
        include_images=args.include_images,
        max_images=args.max_images,
    )

    if all_results:
        print_summary(all_results, dataset_results)
        save_detailed_results(all_results, dataset_results, args.output)
    else:
        print(
            "\nNo results to evaluate. "
            "Run predict_attributes_gpt.py first."
        )


if __name__ == "__main__":
    main()
