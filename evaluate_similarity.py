import json
import argparse
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple
import numpy as np


def load_validation_results(validation_dir: Path) -> Dict[str, Dict]:
    """Load validation results and extract similarity annotations."""
    validation_data = {}
    
    for validation_file in validation_dir.glob("annotations_*.json"):
        with open(validation_file, 'r') as f:
            data = json.load(f)
            scene_id = data['scene_id']
            
            # Extract validated object IDs from attributes
            validated_objects = set()
            if 'attributes' in data and 'predicted' in data['attributes']:
                for item in data['attributes']['predicted']['items']:
                    validated_objects.add(item['object_id'])
            
            # Extract similarity annotations
            similarity_annotations = data.get('similarity', {}).get('annotations', [])
            
            # Convert to set of tuples (min_id, max_id) to handle bidirectional pairs
            similarity_pairs = set()
            for annotation in similarity_annotations:
                id1, id2 = annotation['id1'], annotation['id2']
                # Store as (min, max) to ensure consistent representation
                similarity_pairs.add((min(id1, id2), max(id1, id2)))
            
            validation_data[scene_id] = {
                'similarity_pairs': similarity_pairs,
                'validated_objects': validated_objects,
                'total_annotations': len(similarity_annotations)
            }
    
    return validation_data


def load_model_predictions(scenegraph_dir: Path, scene_ids: List[str], 
                          validated_objects_per_scene: Dict[str, Set[int]]) -> Dict[str, Set[Tuple[int, int]]]:
    """Load model predictions from scenegraph attributes files for specific scenes.
    
    Only includes pairs where both objects were validated.
    """
    predictions = {}
    
    for scene_id in scene_ids:
        scene_dir = scenegraph_dir / scene_id
        
        if not scene_dir.exists():
            print(f"Warning: Scene directory not found for {scene_id}")
            continue
        
        attributes_file = scene_dir / "attributes_from_images.json"
        
        if not attributes_file.exists():
            print(f"Warning: Attributes file not found for {scene_id}")
            continue
        
        with open(attributes_file, 'r') as f:
            data = json.load(f)
        
        # Get validated objects for this scene
        validated_objects = validated_objects_per_scene.get(scene_id, set())
        
        # Extract similarity pairs from "related" field
        # Only include pairs where BOTH objects were validated
        predicted_pairs = set()
        filtered_count = 0
        for obj_id_str, obj_data in data.items():
            obj_id = int(obj_id_str)
            related = obj_data.get('related', [])
            
            # Handle None or empty related field
            if related is None:
                related = []
            
            for related_id in related:
                # Only include if both objects are in the validated set
                if obj_id in validated_objects and related_id in validated_objects:
                    # Store as (min, max) to ensure consistent representation
                    predicted_pairs.add((min(obj_id, related_id), max(obj_id, related_id)))
                else:
                    filtered_count += 1
        
        if filtered_count > 0:
            print(f"  Scene {scene_id}: Filtered out {filtered_count} predictions involving non-validated objects")
        
        predictions[scene_id] = predicted_pairs
    
    return predictions


def compute_metrics(ground_truth: Set[Tuple[int, int]], 
                   predicted: Set[Tuple[int, int]]) -> Dict[str, float]:
    """Compute precision, recall, and F1 score for similarity predictions."""
    
    if len(predicted) == 0:
        precision = 0.0
    else:
        true_positives = len(ground_truth & predicted)
        precision = true_positives / len(predicted)
    
    if len(ground_truth) == 0:
        recall = 0.0
    else:
        true_positives = len(ground_truth & predicted)
        recall = true_positives / len(ground_truth)
    
    if precision + recall == 0:
        f1 = 0.0
    else:
        f1 = 2 * (precision * recall) / (precision + recall)
    
    return {
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'true_positives': len(ground_truth & predicted),
        'false_positives': len(predicted - ground_truth),
        'false_negatives': len(ground_truth - predicted),
        'ground_truth_total': len(ground_truth),
        'predicted_total': len(predicted)
    }


def evaluate_similarity(validation_dir: Path, scenegraph_dir: Path, output_file: Path = None):
    """Evaluate similarity predictions against ground truth annotations."""
    
    print("Loading validation results...")
    validation_data = load_validation_results(validation_dir)
    print(f"Loaded validation data for {len(validation_data)} scenes")
    
    # Only load predictions for scenes that have validation data
    annotated_scene_ids = list(validation_data.keys())
    validated_objects_per_scene = {
        scene_id: data['validated_objects'] 
        for scene_id, data in validation_data.items()
    }
    
    print(f"\nLoading model predictions for {len(annotated_scene_ids)} annotated scenes...")
    print("(Only evaluating predictions where both objects were validated)")
    predictions = load_model_predictions(scenegraph_dir, annotated_scene_ids, validated_objects_per_scene)
    print(f"Loaded predictions for {len(predictions)} scenes")
    
    # Find scenes with both validation and predictions
    common_scenes = set(validation_data.keys()) & set(predictions.keys())
    print(f"\nEvaluating {len(common_scenes)} scenes with both validation and predictions")
    
    if not common_scenes:
        print("No common scenes found! Check scene IDs.")
        print(f"Validation scenes: {list(validation_data.keys())[:5]}")
        print(f"Prediction scenes: {list(predictions.keys())[:5]}")
        return
    
    # Evaluate each scene
    results = {}
    all_metrics = []
    
    for scene_id in sorted(common_scenes):
        ground_truth = validation_data[scene_id]['similarity_pairs']
        predicted = predictions[scene_id]
        validated_objects = validation_data[scene_id]['validated_objects']
        
        metrics = compute_metrics(ground_truth, predicted)
        results[scene_id] = metrics
        all_metrics.append(metrics)
        
        print(f"\n{scene_id}:")
        print(f"  Validated objects: {len(validated_objects)}")
        print(f"  Ground truth pairs: {metrics['ground_truth_total']}")
        print(f"  Predicted pairs (filtered): {metrics['predicted_total']}")
        print(f"  True positives: {metrics['true_positives']}")
        print(f"  False positives: {metrics['false_positives']}")
        print(f"  False negatives: {metrics['false_negatives']}")
        print(f"  Precision: {metrics['precision']:.3f}")
        print(f"  Recall: {metrics['recall']:.3f}")
        print(f"  F1: {metrics['f1']:.3f}")
    
    # Compute aggregate metrics (per-scene average)
    if all_metrics:
        print("\n" + "="*80)
        print("OVERALL METRICS (averaged across scenes):")
        print("="*80)
        
        avg_precision = np.mean([m['precision'] for m in all_metrics])
        avg_recall = np.mean([m['recall'] for m in all_metrics])
        avg_f1 = np.mean([m['f1'] for m in all_metrics])
        
        total_tp = sum([m['true_positives'] for m in all_metrics])
        total_fp = sum([m['false_positives'] for m in all_metrics])
        total_fn = sum([m['false_negatives'] for m in all_metrics])
        total_gt = sum([m['ground_truth_total'] for m in all_metrics])
        total_pred = sum([m['predicted_total'] for m in all_metrics])
        
        print(f"\nAverage across {len(all_metrics)} scenes:")
        print(f"  Precision: {avg_precision:.3f} ({avg_precision*100:.1f}%)")
        print(f"  Recall: {avg_recall:.3f} ({avg_recall*100:.1f}%)")
        print(f"  F1: {avg_f1:.3f}")
        
        print(f"\nTotal counts (all scenes combined):")
        print(f"  Ground truth pairs: {total_gt}")
        print(f"  Predicted pairs: {total_pred}")
        print(f"  True positives: {total_tp}")
        print(f"  False positives: {total_fp}")
        print(f"  False negatives: {total_fn}")
        
        # Prepare output data
        output_data = {
            'per_scene_results': results,
            'overall_metrics': {
                'precision': float(avg_precision),
                'recall': float(avg_recall),
                'f1': float(avg_f1),
                'num_scenes': len(all_metrics)
            },
            'total_counts': {
                'ground_truth_pairs': total_gt,
                'predicted_pairs': total_pred,
                'true_positives': total_tp,
                'false_positives': total_fp,
                'false_negatives': total_fn
            }
        }
        
        # Save results if output file specified
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(output_data, f, indent=2)
            print(f"\nResults saved to {output_file}")


def main():
    parser = argparse.ArgumentParser(description='Evaluate similarity predictions against ground truth')
    parser.add_argument('--validation_dir', type=str, 
                       default='data/validation_results',
                       help='Base directory containing validation results')
    parser.add_argument('--scenegraph_dir', type=str,
                       default='data/scenegraphs',
                       help='Base directory containing scenegraph predictions')
    parser.add_argument('--dataset', type=str,
                       choices=['3rscan', 'scannet', 'both'],
                       default='both',
                       help='Which dataset to evaluate')
    parser.add_argument('--output', type=str,
                       default='similarity_eval_results.json',
                       help='Output file for evaluation results')
    
    args = parser.parse_args()
    
    validation_base = Path(args.validation_dir)
    scenegraph_base = Path(args.scenegraph_dir)
    output_file = Path(args.output)
    
    # Determine which datasets to evaluate
    datasets = []
    if args.dataset in ['3rscan', 'both']:
        datasets.append('3rscan')
    if args.dataset in ['scannet', 'both']:
        datasets.append('scannet')
    
    # Collect all results
    all_results = {}
    all_metrics = []
    
    # Evaluate each dataset
    for dataset in datasets:
        validation_dir = validation_base / dataset
        scenegraph_dir = scenegraph_base / dataset
        
        if not validation_dir.exists():
            print(f"Warning: Validation directory not found: {validation_dir}")
            continue
        
        if not scenegraph_dir.exists():
            print(f"Warning: Scenegraph directory not found: {scenegraph_dir}")
            continue
        
        print(f"\n{'='*80}")
        print(f"EVALUATING {dataset.upper()}")
        print(f"{'='*80}")
        
        # Load and evaluate this dataset
        validation_data = load_validation_results(validation_dir)
        print(f"Loaded validation data for {len(validation_data)} scenes")
        
        annotated_scene_ids = list(validation_data.keys())
        validated_objects_per_scene = {
            scene_id: data['validated_objects'] 
            for scene_id, data in validation_data.items()
        }
        
        print(f"\nLoading model predictions for {len(annotated_scene_ids)} annotated scenes...")
        print("(Only evaluating predictions where both objects were validated)")
        predictions = load_model_predictions(scenegraph_dir, annotated_scene_ids, validated_objects_per_scene)
        print(f"Loaded predictions for {len(predictions)} scenes")
        
        common_scenes = set(validation_data.keys()) & set(predictions.keys())
        print(f"\nEvaluating {len(common_scenes)} scenes with both validation and predictions")
        
        if not common_scenes:
            print("No common scenes found! Skipping dataset.")
            continue
        
        # Evaluate each scene
        for scene_id in sorted(common_scenes):
            ground_truth = validation_data[scene_id]['similarity_pairs']
            predicted = predictions[scene_id]
            validated_objects = validation_data[scene_id]['validated_objects']
            
            metrics = compute_metrics(ground_truth, predicted)
            all_results[f"{dataset}/{scene_id}"] = metrics
            all_metrics.append(metrics)
            
            print(f"\n{scene_id}:")
            print(f"  Validated objects: {len(validated_objects)}")
            print(f"  Ground truth pairs: {metrics['ground_truth_total']}")
            print(f"  Predicted pairs (filtered): {metrics['predicted_total']}")
            print(f"  True positives: {metrics['true_positives']}")
            print(f"  False positives: {metrics['false_positives']}")
            print(f"  False negatives: {metrics['false_negatives']}")
            print(f"  Precision: {metrics['precision']:.3f}")
            print(f"  Recall: {metrics['recall']:.3f}")
            print(f"  F1: {metrics['f1']:.3f}")
    
    # Compute overall metrics
    if all_metrics:
        print("\n" + "="*80)
        print("OVERALL METRICS (averaged across all scenes):")
        print("="*80)
        
        avg_precision = np.mean([m['precision'] for m in all_metrics])
        avg_recall = np.mean([m['recall'] for m in all_metrics])
        avg_f1 = np.mean([m['f1'] for m in all_metrics])
        
        total_tp = sum([m['true_positives'] for m in all_metrics])
        total_fp = sum([m['false_positives'] for m in all_metrics])
        total_fn = sum([m['false_negatives'] for m in all_metrics])
        total_gt = sum([m['ground_truth_total'] for m in all_metrics])
        total_pred = sum([m['predicted_total'] for m in all_metrics])
        
        print(f"\nAverage across {len(all_metrics)} scenes:")
        print(f"  Precision: {avg_precision:.3f} ({avg_precision*100:.1f}%)")
        print(f"  Recall: {avg_recall:.3f} ({avg_recall*100:.1f}%)")
        print(f"  F1: {avg_f1:.3f}")
        
        print(f"\nTotal counts (all scenes combined):")
        print(f"  Ground truth pairs: {total_gt}")
        print(f"  Predicted pairs: {total_pred}")
        print(f"  True positives: {total_tp}")
        print(f"  False positives: {total_fp}")
        print(f"  False negatives: {total_fn}")
        
        # Prepare output data
        output_data = {
            'per_scene_results': all_results,
            'overall_metrics': {
                'precision': float(avg_precision),
                'recall': float(avg_recall),
                'f1': float(avg_f1),
                'num_scenes': len(all_metrics)
            },
            'total_counts': {
                'ground_truth_pairs': total_gt,
                'predicted_pairs': total_pred,
                'true_positives': total_tp,
                'false_positives': total_fp,
                'false_negatives': total_fn
            }
        }
        
        # Save results
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(output_data, f, indent=2)
            print(f"\nResults saved to {output_file}")


if __name__ == '__main__':
    main()
