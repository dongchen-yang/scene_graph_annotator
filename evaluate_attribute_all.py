import json
import argparse
from pathlib import Path
from collections import defaultdict
import numpy as np
from evaluate_attribute import (
    CLIPSimilarityEvaluator, 
    load_ground_truth, 
    load_predictions, 
    calculate_similarity_scores,
    find_object_images,
    load_object_images
)


def extract_scene_id(validation_filename):
    """Extract scene ID from validation filename.
    
    Examples:
        annotations_02b33dfb-be2b-2d54-92d2-cd012b2b3c40_1769641580995.json -> 02b33dfb-be2b-2d54-92d2-cd012b2b3c40
        annotations_scene0001_00_1769639833162.json -> scene0001_00
    """
    stem = Path(validation_filename).stem
    # Remove 'annotations_' prefix and timestamp suffix
    parts = stem.split('_')
    if stem.startswith('annotations_scene'):
        # ScanNet: annotations_scene0001_00_timestamp
        return f"{parts[1]}_{parts[2]}"
    else:
        # 3RScan: annotations_uuid_timestamp
        return parts[1]


def find_validation_and_scene_graph_pairs(base_dir):
    """Find all validation/scene_graph pairs organized by dataset."""
    base_path = Path(base_dir)
    pairs = {'3rscan': [], 'scannet': []}
    
    for dataset in ['3rscan', 'scannet']:
        validation_dir = base_path / 'data' / 'validation_results' / dataset
        scene_graph_dir = base_path / 'data' / 'scenegraphs_sampled' / dataset
        
        if not validation_dir.exists():
            print(f"Warning: {validation_dir} does not exist")
            continue
        
        for validation_file in sorted(validation_dir.glob('annotations_*.json')):
            scene_id = extract_scene_id(validation_file.name)
            scene_graph_file = scene_graph_dir / scene_id / 'scene_graph.json'
            
            if scene_graph_file.exists():
                pairs[dataset].append({
                    'scene_id': scene_id,
                    'validation_file': str(validation_file),
                    'scene_graph_file': str(scene_graph_file),
                    'dataset': dataset
                })
            else:
                print(f"Warning: Scene graph not found for {scene_id}: {scene_graph_file}")
    
    return pairs


def evaluate_all_scenes(base_dir, evaluator, num_trials=10, include_images=False, max_images=3):
    """Evaluate all scenes and return aggregated results."""
    
    # Find all pairs
    pairs_by_dataset = find_validation_and_scene_graph_pairs(base_dir)
    
    all_results = []
    dataset_results = {'3rscan': [], 'scannet': []}
    
    print("\n" + "="*80)
    print("EVALUATING ALL SCENES")
    if include_images:
        print("Mode: Text-to-Text + Image-to-Text CLIP Similarity")
    else:
        print("Mode: Text-to-Text CLIP Similarity Only")
    print("="*80)
    
    total_scenes = sum(len(pairs) for pairs in pairs_by_dataset.values())
    current = 0
    
    for dataset, pairs in pairs_by_dataset.items():
        print(f"\n{dataset.upper()}: Found {len(pairs)} scenes")
        
        for pair in pairs:
            current += 1
            scene_id = pair['scene_id']
            print(f"\n[{current}/{total_scenes}] Evaluating {dataset}/{scene_id}...")
            
            try:
                # Load data
                ground_truth = load_ground_truth(pair['validation_file'])
                predictions = load_predictions(pair['scene_graph_file'])
                
                # Calculate similarity
                results = calculate_similarity_scores(
                    ground_truth, 
                    predictions, 
                    evaluator, 
                    num_random_trials=num_trials,
                    scene_id=scene_id,
                    dataset=dataset,
                    include_image_similarity=include_images,
                    max_images_per_object=max_images
                )
                
                # Add metadata
                scene_result = {
                    'scene_id': scene_id,
                    'dataset': dataset,
                    'validation_file': pair['validation_file'],
                    'scene_graph_file': pair['scene_graph_file'],
                    'average_similarity': results['overall']['average_similarity'],
                    'total_objects': results['overall']['total_objects'],
                    'per_object': results['per_object']
                }
                
                # Add image metrics if available
                if 'average_image_gt_similarity' in results['overall']:
                    scene_result['average_image_gt_similarity'] = results['overall']['average_image_gt_similarity']
                    scene_result['average_image_pred_similarity'] = results['overall']['average_image_pred_similarity']
                    scene_result['objects_with_images'] = results['overall']['objects_with_images']
                
                all_results.append(scene_result)
                dataset_results[dataset].append(scene_result)
                
                if include_images and 'average_image_gt_similarity' in scene_result:
                    print(f"  ✓ Text Sim: {scene_result['average_similarity']:.4f}, "
                          f"Img-GT: {scene_result['average_image_gt_similarity']:.4f}, "
                          f"Img-Pred: {scene_result['average_image_pred_similarity']:.4f}, "
                          f"Objects: {scene_result['total_objects']}")
                else:
                    print(f"  ✓ Similarity: {scene_result['average_similarity']:.4f}, Objects: {scene_result['total_objects']}")
                
            except Exception as e:
                print(f"  ✗ Error: {e}")
                import traceback
                traceback.print_exc()
                continue
    
    return all_results, dataset_results


def aggregate_results(results_list):
    """Aggregate multiple scene results into overall statistics."""
    if not results_list:
        return {
            'average_similarity': 0.0,
            'std_similarity': 0.0,
            'total_scenes': 0,
            'total_objects': 0,
            'min_similarity': 0.0,
            'max_similarity': 0.0
        }
    
    similarities = [r['average_similarity'] for r in results_list]
    total_objects = sum(r['total_objects'] for r in results_list)
    
    agg = {
        'average_similarity': np.mean(similarities),
        'std_similarity': np.std(similarities),
        'total_scenes': len(results_list),
        'total_objects': total_objects,
        'min_similarity': np.min(similarities),
        'max_similarity': np.max(similarities)
    }
    
    # Add image metrics if available
    img_gt_sims = [r['average_image_gt_similarity'] for r in results_list if 'average_image_gt_similarity' in r]
    img_pred_sims = [r['average_image_pred_similarity'] for r in results_list if 'average_image_pred_similarity' in r]
    objects_with_images = sum(r.get('objects_with_images', 0) for r in results_list)
    objects_without_images = sum(r.get('objects_without_images', 0) for r in results_list)
    
    if img_gt_sims:
        agg['average_image_gt_similarity'] = np.mean(img_gt_sims)
        agg['std_image_gt_similarity'] = np.std(img_gt_sims)
        agg['average_image_pred_similarity'] = np.mean(img_pred_sims)
        agg['std_image_pred_similarity'] = np.std(img_pred_sims)
        agg['scenes_with_images'] = len(img_gt_sims)
        agg['total_objects_with_images'] = objects_with_images
        agg['total_objects_without_images'] = objects_without_images
    
    return agg


def print_summary(all_results, dataset_results):
    """Print comprehensive evaluation summary."""
    
    print("\n" + "="*80)
    print("EVALUATION SUMMARY")
    print("="*80)
    
    # Overall results (per-scene average)
    overall_agg = aggregate_results(all_results)
    print(f"\n{'='*80}")
    print(f"OVERALL (averaged across {len(all_results)} scenes)")
    print(f"{'='*80}")
    print(f"  Average Text-Text Similarity: {overall_agg['average_similarity']:.4f} (±{overall_agg['std_similarity']:.4f})")
    
    if 'average_image_gt_similarity' in overall_agg:
        print(f"\n  Image Statistics:")
        print(f"    Objects with Images:    {overall_agg['total_objects_with_images']}/{overall_agg['total_objects']} "
              f"({100*overall_agg['total_objects_with_images']/overall_agg['total_objects']:.1f}%)")
        print(f"    Objects without Images: {overall_agg['total_objects_without_images']}/{overall_agg['total_objects']} "
              f"({100*overall_agg['total_objects_without_images']/overall_agg['total_objects']:.1f}%)")
        print(f"    Scenes with Images:     {overall_agg['scenes_with_images']}/{overall_agg['total_scenes']}")
        
        print(f"\n  Image-to-Text Similarity:")
        print(f"    Image-GT Similarity:    {overall_agg['average_image_gt_similarity']:.4f} (±{overall_agg['std_image_gt_similarity']:.4f})")
        print(f"    Image-Pred Similarity:  {overall_agg['average_image_pred_similarity']:.4f} (±{overall_agg['std_image_pred_similarity']:.4f})")
        
        diff = overall_agg['average_image_pred_similarity'] - overall_agg['average_image_gt_similarity']
        if diff > 0.01:
            print(f"    → Predictions better aligned with images (+{diff:.4f})")
        elif diff < -0.01:
            print(f"    → GT better aligned with images ({diff:.4f})")
        else:
            print(f"    → Similar alignment (diff: {diff:+.4f})")
    
    print(f"\n  Scene Statistics:")
    print(f"    Total Scenes:         {overall_agg['total_scenes']}")
    print(f"    Total Objects:        {overall_agg['total_objects']}")
    print(f"    Min Similarity:       {overall_agg['min_similarity']:.4f}")
    print(f"    Max Similarity:       {overall_agg['max_similarity']:.4f}")
    
    # Per-dataset results
    for dataset in ['3rscan', 'scannet']:
        if dataset_results[dataset]:
            agg = aggregate_results(dataset_results[dataset])
            print(f"\n{'-'*80}")
            print(f"{dataset.upper()} (averaged across {len(dataset_results[dataset])} scenes)")
            print(f"{'-'*80}")
            print(f"  Average Text-Text Similarity: {agg['average_similarity']:.4f} (±{agg['std_similarity']:.4f})")
            
            if 'total_objects_with_images' in agg:
                print(f"  Objects with Images:  {agg['total_objects_with_images']}/{agg['total_objects']} "
                      f"({100*agg['total_objects_with_images']/agg['total_objects']:.1f}%)")
            
            if 'average_image_gt_similarity' in agg:
                print(f"  Image-GT Similarity:  {agg['average_image_gt_similarity']:.4f} (±{agg['std_image_gt_similarity']:.4f})")
                print(f"  Image-Pred Similarity:{agg['average_image_pred_similarity']:.4f} (±{agg['std_image_pred_similarity']:.4f})")
            
            print(f"  Total Scenes:         {agg['total_scenes']}")
            print(f"  Total Objects:        {agg['total_objects']}")
            print(f"  Min Similarity:       {agg['min_similarity']:.4f}")
            print(f"  Max Similarity:       {agg['max_similarity']:.4f}")
    
    # Per-scene results
    print(f"\n{'='*80}")
    print("PER-SCENE RESULTS")
    print(f"{'='*80}")
    
    has_images = any('average_image_gt_similarity' in r for r in all_results)
    
    if has_images:
        print(f"{'Dataset':<10} {'Scene ID':<40} {'Text-Text':<12} {'Img-GT':<10} {'Img-Pred':<10} {'Objs':<8}")
    else:
        print(f"{'Dataset':<10} {'Scene ID':<40} {'Similarity':<12} {'Objects':<8}")
    print(f"{'-'*80}")
    
    # Sort by similarity (worst first for debugging)
    sorted_results = sorted(all_results, key=lambda x: x['average_similarity'])
    
    for result in sorted_results:
        dataset = result['dataset'].upper()
        scene_id = result['scene_id']
        sim = result['average_similarity']
        obj_count = result['total_objects']
        
        if has_images and 'average_image_gt_similarity' in result:
            img_gt = result['average_image_gt_similarity']
            img_pred = result['average_image_pred_similarity']
            print(f"{dataset:<10} {scene_id:<40} {sim:.4f}       {img_gt:.4f}    {img_pred:.4f}    {obj_count:<8}")
        elif has_images:
            print(f"{dataset:<10} {scene_id:<40} {sim:.4f}       {'N/A':<10} {'N/A':<10} {obj_count:<8}")
        else:
            print(f"{dataset:<10} {scene_id:<40} {sim:.4f}       {obj_count:<8}")


def save_detailed_results(all_results, dataset_results, output_file):
    """Save detailed results to JSON file."""
    
    output = {
        'overall': aggregate_results(all_results),
        'by_dataset': {
            '3rscan': aggregate_results(dataset_results['3rscan']),
            'scannet': aggregate_results(dataset_results['scannet'])
        },
        'per_scene': all_results
    }
    
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n{'='*80}")
    print(f"Detailed results saved to: {output_file}")
    print(f"{'='*80}")


def main():
    parser = argparse.ArgumentParser(
        description='Evaluate attribute prediction for all scenes'
    )
    parser.add_argument(
        '--base-dir',
        type=str,
        default='.',
        help='Base directory containing data/ folder (default: current directory)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='attribute_evaluation_all_scenes.json',
        help='Output JSON file for detailed results'
    )
    parser.add_argument(
        '--num-trials',
        type=int,
        default=10,
        help='Number of random orderings to average (default: 10)'
    )
    parser.add_argument(
        '--model',
        type=str,
        default='openai/clip-vit-base-patch32',
        help='CLIP model to use'
    )
    parser.add_argument(
        '--device',
        type=str,
        default=None,
        help='Device to use (cuda/cpu, default: auto-detect)'
    )
    parser.add_argument(
        '--include-images',
        action='store_true',
        help='Include image-based CLIP similarity evaluation'
    )
    parser.add_argument(
        '--max-images',
        type=int,
        default=3,
        help='Maximum images to load per object (default: 3)'
    )
    
    args = parser.parse_args()
    
    # Initialize CLIP evaluator
    print("Loading CLIP model...")
    evaluator = CLIPSimilarityEvaluator(model_name=args.model, device=args.device)
    
    # Evaluate all scenes
    all_results, dataset_results = evaluate_all_scenes(
        args.base_dir, 
        evaluator, 
        num_trials=args.num_trials,
        include_images=args.include_images,
        max_images=args.max_images
    )
    
    # Print summary
    print_summary(all_results, dataset_results)
    
    # Save detailed results
    save_detailed_results(all_results, dataset_results, args.output)


if __name__ == '__main__':
    main()
