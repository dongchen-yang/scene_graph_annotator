#!/usr/bin/env python3
"""
Generate detailed per-scene similarity evaluation report.
Shows ground truth vs predicted similarity pairs for each scene.
"""

import json
from pathlib import Path
from typing import Dict, Set, Tuple, List
import argparse


def load_validation_results(validation_dir: Path) -> Dict[str, Dict]:
    """Load validation results with similarity annotations."""
    validation_data = {}
    
    for json_file in validation_dir.glob("annotations_*.json"):
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        scene_id = data.get('scene_id')
        if not scene_id:
            continue
        
        # Extract similarity pairs
        similarity_pairs = set()
        if 'similarity' in data and 'annotations' in data['similarity']:
            for ann in data['similarity']['annotations']:
                obj1 = ann['id1']
                obj2 = ann['id2']
                similarity_pairs.add((min(obj1, obj2), max(obj1, obj2)))
        
        # Extract validated objects from attributes section
        validated_objects = set()
        if 'attributes' in data and 'predicted' in data['attributes']:
            for item in data['attributes']['predicted']['items']:
                validated_objects.add(item['object_id'])
        
        validation_data[scene_id] = {
            'similarity_pairs': similarity_pairs,
            'validated_objects': validated_objects
        }
    
    return validation_data


def load_model_predictions(scenegraph_dir: Path, scene_id: str, validated_objects: Set[int]) -> Set[Tuple[int, int]]:
    """Load model predictions for a specific scene."""
    scene_dir = scenegraph_dir / scene_id
    attributes_file = scene_dir / "attributes_from_images.json"
    
    if not attributes_file.exists():
        return set()
    
    with open(attributes_file, 'r') as f:
        data = json.load(f)
    
    predicted_pairs = set()
    for obj_id_str, obj_data in data.items():
        try:
            obj_id = int(obj_id_str)
        except ValueError:
            continue
        
        related = obj_data.get('related', [])
        if related is None:
            related = []
        
        for related_id in related:
            # Only include pairs where both objects are in validated set
            if obj_id in validated_objects and related_id in validated_objects:
                predicted_pairs.add((min(obj_id, related_id), max(obj_id, related_id)))
    
    return predicted_pairs


def generate_markdown_report(validation_base: Path, scenegraph_base: Path, output_file: Path):
    """Generate a detailed markdown report."""
    
    # Determine datasets
    datasets = []
    if (validation_base / '3rscan').exists():
        datasets.append('3rscan')
    if (validation_base / 'scannet').exists():
        datasets.append('scannet')
    
    lines = []
    lines.append("# Detailed Similarity Evaluation Results")
    lines.append("")
    lines.append("Per-scene breakdown showing ground truth vs predicted similarity pairs.")
    lines.append("")
    
    total_scenes = 0
    total_gt_pairs = 0
    total_pred_pairs = 0
    total_tp = 0
    total_fp = 0
    total_fn = 0
    
    for dataset in datasets:
        validation_dir = validation_base / dataset
        scenegraph_dir = scenegraph_base / dataset
        
        lines.append(f"## {dataset.upper()}")
        lines.append("")
        
        validation_data = load_validation_results(validation_dir)
        
        for scene_id in sorted(validation_data.keys()):
            total_scenes += 1
            gt_pairs = validation_data[scene_id]['similarity_pairs']
            validated_objects = validation_data[scene_id]['validated_objects']
            pred_pairs = load_model_predictions(scenegraph_dir, scene_id, validated_objects)
            
            # Compute metrics
            tp_pairs = gt_pairs & pred_pairs
            fp_pairs = pred_pairs - gt_pairs
            fn_pairs = gt_pairs - pred_pairs
            
            tp = len(tp_pairs)
            fp = len(fp_pairs)
            fn = len(fn_pairs)
            
            total_gt_pairs += len(gt_pairs)
            total_pred_pairs += len(pred_pairs)
            total_tp += tp
            total_fp += fp
            total_fn += fn
            
            precision = tp / len(pred_pairs) if pred_pairs else 0
            recall = tp / len(gt_pairs) if gt_pairs else (1.0 if not pred_pairs else 0.0)
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
            
            lines.append(f"### {scene_id}")
            lines.append("")
            lines.append(f"**Validated Objects:** {len(validated_objects)}")
            lines.append("")
            lines.append(f"**Metrics:**")
            lines.append(f"- Ground Truth Pairs: {len(gt_pairs)}")
            lines.append(f"- Predicted Pairs: {len(pred_pairs)}")
            lines.append(f"- True Positives: {tp}")
            lines.append(f"- False Positives: {fp}")
            lines.append(f"- False Negatives: {fn}")
            lines.append(f"- Precision: {precision:.3f}")
            lines.append(f"- Recall: {recall:.3f}")
            lines.append(f"- F1 Score: {f1:.3f}")
            lines.append("")
            
            # Show actual pairs
            if gt_pairs:
                lines.append(f"**Ground Truth Pairs ({len(gt_pairs)}):**")
                for obj1, obj2 in sorted(gt_pairs):
                    status = "✓ PREDICTED" if (obj1, obj2) in tp_pairs else "✗ MISSED"
                    lines.append(f"- `({obj1}, {obj2})` {status}")
                lines.append("")
            else:
                lines.append("**Ground Truth Pairs:** None (no similar objects)")
                lines.append("")
            
            if pred_pairs:
                lines.append(f"**Predicted Pairs ({len(pred_pairs)}):**")
                for obj1, obj2 in sorted(pred_pairs):
                    status = "✓ CORRECT" if (obj1, obj2) in tp_pairs else "✗ FALSE POSITIVE"
                    lines.append(f"- `({obj1}, {obj2})` {status}")
                lines.append("")
            else:
                lines.append("**Predicted Pairs:** None")
                lines.append("")
            
            if fn_pairs:
                lines.append(f"**Missed Pairs (False Negatives) ({len(fn_pairs)}):**")
                for obj1, obj2 in sorted(fn_pairs):
                    lines.append(f"- `({obj1}, {obj2})`")
                lines.append("")
            
            lines.append("---")
            lines.append("")
    
    # Overall summary
    lines.append("## Overall Summary")
    lines.append("")
    lines.append(f"- **Total Scenes:** {total_scenes}")
    lines.append(f"- **Total Ground Truth Pairs:** {total_gt_pairs}")
    lines.append(f"- **Total Predicted Pairs:** {total_pred_pairs}")
    lines.append(f"- **Total True Positives:** {total_tp}")
    lines.append(f"- **Total False Positives:** {total_fp}")
    lines.append(f"- **Total False Negatives:** {total_fn}")
    lines.append("")
    
    avg_precision = total_tp / total_pred_pairs if total_pred_pairs > 0 else 0
    avg_recall = total_tp / total_gt_pairs if total_gt_pairs > 0 else 0
    avg_f1 = 2 * avg_precision * avg_recall / (avg_precision + avg_recall) if (avg_precision + avg_recall) > 0 else 0
    
    lines.append(f"**Aggregate Metrics (micro-averaged):**")
    lines.append(f"- Precision: {avg_precision:.3f} ({avg_precision*100:.1f}%)")
    lines.append(f"- Recall: {avg_recall:.3f} ({avg_recall*100:.1f}%)")
    lines.append(f"- F1 Score: {avg_f1:.3f}")
    lines.append("")
    
    # Write to file
    with open(output_file, 'w') as f:
        f.write('\n'.join(lines))
    
    print(f"✓ Detailed report saved to {output_file}")


def main():
    parser = argparse.ArgumentParser(description='Generate detailed similarity evaluation report')
    parser.add_argument('--validation_dir', type=str,
                       default='data/validation_results',
                       help='Base directory containing validation results')
    parser.add_argument('--scenegraph_dir', type=str,
                       default='data/scenegraphs',
                       help='Base directory containing scenegraph predictions')
    parser.add_argument('--output', type=str,
                       default='similarity_detailed_report.md',
                       help='Output markdown file')
    
    args = parser.parse_args()
    
    validation_base = Path(args.validation_dir)
    scenegraph_base = Path(args.scenegraph_dir)
    output_file = Path(args.output)
    
    generate_markdown_report(validation_base, scenegraph_base, output_file)


if __name__ == '__main__':
    main()
