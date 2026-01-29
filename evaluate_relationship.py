import json
import argparse
from pathlib import Path
from collections import defaultdict
from typing import Dict, List
import numpy as np


def load_relationship_validations(validation_dir: Path) -> Dict:
    """Load relationship validation results from validation files."""
    all_results = {
        'per_scene': {},
        'per_predicate': defaultdict(lambda: {'correct': 0, 'incorrect': 0}),
        'total_correct': 0,
        'total_incorrect': 0,
        'total_null_validation': 0,
        'total_relationships': 0
    }
    
    for validation_file in sorted(validation_dir.glob("annotations_*.json")):
        with open(validation_file, 'r') as f:
            data = json.load(f)
        
        scene_id = data.get('scene_id', validation_file.stem.replace('annotations_', ''))
        
        if 'relationships' not in data or 'predicted' not in data['relationships']:
            continue
        
        relationships = data['relationships']['predicted']['items']
        
        scene_stats = {
            'correct': 0,
            'incorrect': 0,
            'null_validation': 0,
            'total': len(relationships),
            'by_predicate': defaultdict(lambda: {'correct': 0, 'incorrect': 0})
        }
        
        for rel in relationships:
            predicate = rel['predicate']
            validation = rel.get('validation')
            
            if validation is None:
                scene_stats['null_validation'] += 1
                all_results['total_null_validation'] += 1
            elif validation == 'correct':
                scene_stats['correct'] += 1
                scene_stats['by_predicate'][predicate]['correct'] += 1
                all_results['per_predicate'][predicate]['correct'] += 1
                all_results['total_correct'] += 1
            elif validation == 'incorrect':
                scene_stats['incorrect'] += 1
                scene_stats['by_predicate'][predicate]['incorrect'] += 1
                all_results['per_predicate'][predicate]['incorrect'] += 1
                all_results['total_incorrect'] += 1
        
        scene_stats['accuracy'] = scene_stats['correct'] / scene_stats['total'] if scene_stats['total'] > 0 else 0
        all_results['per_scene'][scene_id] = scene_stats
        all_results['total_relationships'] += scene_stats['total']
    
    return all_results


def print_results(results: Dict, output_file: Path = None):
    """Print and save relationship evaluation results."""
    
    print("="*80)
    print("RELATIONSHIP PREDICTION EVALUATION")
    print("="*80)
    
    total = results['total_relationships']
    correct = results['total_correct']
    incorrect = results['total_incorrect']
    null_val = results['total_null_validation']
    
    evaluated_total = correct + incorrect
    
    # Compute per-scene average accuracy
    scene_accuracies = [scene['accuracy'] for scene in results['per_scene'].values()]
    avg_accuracy = np.mean(scene_accuracies) if scene_accuracies else 0
    
    print(f"\nOVERALL STATISTICS (averaged across {len(scene_accuracies)} scenes):")
    print(f"  Average Accuracy: {avg_accuracy:.3f} ({avg_accuracy*100:.1f}%)")
    print(f"\nTotal counts (all scenes combined):")
    print(f"  Total relationships: {total}")
    print(f"  Evaluated: {evaluated_total} ({evaluated_total/total*100:.1f}%)")
    print(f"  Not evaluated (null): {null_val} ({null_val/total*100:.1f}%)")
    print(f"  Correct: {correct}")
    print(f"  Incorrect: {incorrect}")
    
    # Per-scene results
    print(f"\n{'='*80}")
    print("PER-SCENE RESULTS:")
    print(f"{'='*80}")
    
    for scene_id in sorted(results['per_scene'].keys()):
        scene = results['per_scene'][scene_id]
        print(f"\n{scene_id}:")
        print(f"  Total: {scene['total']}")
        print(f"  Correct: {scene['correct']}")
        print(f"  Incorrect: {scene['incorrect']}")
        print(f"  Null: {scene['null_validation']}")
        print(f"  Accuracy: {scene['accuracy']:.3f} ({scene['accuracy']*100:.1f}%)")
    
    # Per-predicate results
    print(f"\n{'='*80}")
    print("PER-PREDICATE RESULTS:")
    print(f"{'='*80}")
    
    # Sort by total count
    predicate_stats = []
    for predicate, counts in results['per_predicate'].items():
        total = counts['correct'] + counts['incorrect']
        accuracy = counts['correct'] / total if total > 0 else 0
        predicate_stats.append({
            'predicate': predicate,
            'total': total,
            'correct': counts['correct'],
            'incorrect': counts['incorrect'],
            'accuracy': accuracy
        })
    
    predicate_stats.sort(key=lambda x: x['total'], reverse=True)
    
    print(f"\n{'Predicate':<30} {'Total':<8} {'Correct':<10} {'Incorrect':<10} {'Accuracy':<10}")
    print("-" * 80)
    for stat in predicate_stats:
        print(f"{stat['predicate']:<30} {stat['total']:<8} {stat['correct']:<10} "
              f"{stat['incorrect']:<10} {stat['accuracy']:<10.3f}")
    
    # Prepare output data
    output_data = {
        'overall': {
            'average_accuracy': float(avg_accuracy),
            'num_scenes': len(scene_accuracies)
        },
        'total_counts': {
            'total_relationships': total,
            'evaluated': evaluated_total,
            'not_evaluated': null_val,
            'correct': correct,
            'incorrect': incorrect
        },
        'per_scene': {},
        'per_predicate': {}
    }
    
    for scene_id, scene in results['per_scene'].items():
        output_data['per_scene'][scene_id] = {
            'total': scene['total'],
            'correct': scene['correct'],
            'incorrect': scene['incorrect'],
            'null_validation': scene['null_validation'],
            'accuracy': float(scene['accuracy'])
        }
    
    for stat in predicate_stats:
        output_data['per_predicate'][stat['predicate']] = {
            'total': stat['total'],
            'correct': stat['correct'],
            'incorrect': stat['incorrect'],
            'accuracy': float(stat['accuracy'])
        }
    
    # Save results
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        print(f"\n{'='*80}")
        print(f"Results saved to {output_file}")


def main():
    parser = argparse.ArgumentParser(description='Evaluate relationship predictions from validation results')
    parser.add_argument('--validation_dir', type=str,
                       default='data/validation_results',
                       help='Directory containing validation results')
    parser.add_argument('--dataset', type=str,
                       choices=['3rscan', 'scannet', 'both'],
                       default='both',
                       help='Which dataset to evaluate')
    parser.add_argument('--output', type=str,
                       default='relationship_eval_results.json',
                       help='Output file for evaluation results')
    
    args = parser.parse_args()
    
    validation_base = Path(args.validation_dir)
    
    if not validation_base.exists():
        print(f"Error: Validation directory not found: {validation_base}")
        return
    
    # Collect validation directories based on dataset selection
    validation_dirs = []
    if args.dataset in ['3rscan', 'both']:
        rscan_dir = validation_base / '3rscan'
        if rscan_dir.exists():
            validation_dirs.append(('3rscan', rscan_dir))
    
    if args.dataset in ['scannet', 'both']:
        scannet_dir = validation_base / 'scannet'
        if scannet_dir.exists():
            validation_dirs.append(('scannet', scannet_dir))
    
    if not validation_dirs:
        print(f"Error: No validation directories found for dataset: {args.dataset}")
        return
    
    # Process each dataset
    all_results = {}
    for dataset_name, val_dir in validation_dirs:
        print(f"\nProcessing {dataset_name}...")
        results = load_relationship_validations(val_dir)
        all_results[dataset_name] = results
    
    # Print results for each dataset
    for dataset_name, results in all_results.items():
        print(f"\n{'#'*80}")
        print(f"{'#'*80}")
        print(f"  DATASET: {dataset_name.upper()}")
        print(f"{'#'*80}")
        print(f"{'#'*80}")
        print_results(results, None)
    
    # If processing both datasets, also show combined results
    if len(all_results) > 1:
        print(f"\n{'#'*80}")
        print(f"{'#'*80}")
        print(f"  COMBINED RESULTS (ALL DATASETS)")
        print(f"{'#'*80}")
        print(f"{'#'*80}")
        
        combined = {
            'per_scene': {},
            'per_predicate': defaultdict(lambda: {'correct': 0, 'incorrect': 0}),
            'total_correct': 0,
            'total_incorrect': 0,
            'total_null_validation': 0,
            'total_relationships': 0
        }
        
        for dataset_name, results in all_results.items():
            combined['total_correct'] += results['total_correct']
            combined['total_incorrect'] += results['total_incorrect']
            combined['total_null_validation'] += results['total_null_validation']
            combined['total_relationships'] += results['total_relationships']
            
            for scene_id, scene_data in results['per_scene'].items():
                combined['per_scene'][f"{dataset_name}/{scene_id}"] = scene_data
            
            for predicate, counts in results['per_predicate'].items():
                combined['per_predicate'][predicate]['correct'] += counts['correct']
                combined['per_predicate'][predicate]['incorrect'] += counts['incorrect']
        
        print_results(combined, Path(args.output))
    else:
        # Save single dataset results
        dataset_name = list(all_results.keys())[0]
        print_results(all_results[dataset_name], Path(args.output))


if __name__ == '__main__':
    main()
