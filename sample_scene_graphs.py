#!/usr/bin/env python3
"""
Sample a subset of objects from each scene and keep only relationships involving those objects.
"""

import json
import argparse
from pathlib import Path
import random
import shutil
from collections import defaultdict


def sample_objects(objects, num_objects, seed=42):
    """
    Sample a subset of objects, prioritizing targetable objects.
    
    Args:
        objects: List of object dictionaries
        num_objects: Number of objects to sample
        seed: Random seed for reproducibility
    
    Returns:
        List of sampled object IDs
    """
    random.seed(seed)
    
    # Separate targetable and non-targetable objects
    targetable = [obj for obj in objects if obj.get('is_targetable', True)]
    non_targetable = [obj for obj in objects if not obj.get('is_targetable', True)]
    
    # Prioritize targetable objects
    if len(targetable) >= num_objects:
        sampled = random.sample(targetable, num_objects)
    else:
        # Take all targetable + sample from non-targetable
        remaining = num_objects - len(targetable)
        if remaining <= len(non_targetable):
            sampled = targetable + random.sample(non_targetable, remaining)
        else:
            sampled = objects[:num_objects]  # Take first N if not enough
    
    return sorted([obj['id'] for obj in sampled])


def filter_scene_graph(scene_graph_path, output_path, num_objects, seed=42):
    """
    Sample objects and filter relationships for a single scene.
    
    Returns:
        Dictionary with statistics
    """
    with open(scene_graph_path, 'r') as f:
        data = json.load(f)
    
    original_objects = len(data['objects'])
    original_relationships = len(data.get('relationships', []))
    original_attributes = len(data.get('attributes', []))
    
    # Sample objects
    sampled_object_ids = sample_objects(data['objects'], min(num_objects, len(data['objects'])), seed)
    sampled_object_ids_set = set(sampled_object_ids)
    
    # Filter objects
    filtered_objects = [obj for obj in data['objects'] if obj['id'] in sampled_object_ids_set]
    
    # Filter relationships - keep only if subject and ALL recipients are in sampled set
    filtered_relationships = []
    for rel in data.get('relationships', []):
        subject_in = rel['subject_id'] in sampled_object_ids_set
        recipients_in = all(rid in sampled_object_ids_set for rid in rel.get('recipient_id', []))
        if subject_in and recipients_in:
            filtered_relationships.append(rel)
    
    # Filter attributes
    filtered_attributes = []
    if 'attributes' in data:
        filtered_attributes = [attr for attr in data['attributes'] if attr['object_id'] in sampled_object_ids_set]
    
    # Create filtered scene graph
    filtered_data = {
        'id': data['id'],
        'source': data['source'],
        'objects': filtered_objects,
        'relationships': filtered_relationships,
        'attributes': filtered_attributes
    }
    
    # Save filtered scene graph
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(filtered_data, f, indent=2)
    
    # Copy other files if they exist (like attributes_from_images.json)
    for other_file in scene_graph_path.parent.glob('*.json'):
        if other_file.name != 'scene_graph.json':
            target = output_path.parent / other_file.name
            shutil.copy2(other_file, target)
    
    return {
        'scene_id': data['id'],
        'original_objects': original_objects,
        'sampled_objects': len(filtered_objects),
        'original_relationships': original_relationships,
        'sampled_relationships': len(filtered_relationships),
        'original_attributes': original_attributes,
        'sampled_attributes': len(filtered_attributes),
        'reduction_relationships': original_relationships - len(filtered_relationships),
        'reduction_percentage': ((original_relationships - len(filtered_relationships)) / original_relationships * 100) if original_relationships > 0 else 0
    }


def process_all_scenes(dataset, base_dir, output_dir, num_objects, seed=42):
    """
    Process all scenes for a given dataset.
    
    Args:
        dataset: 'scannet', 'multiscan', or '3rscan'
        base_dir: Base directory containing scene graphs
        output_dir: Output directory for sampled scene graphs
        num_objects: Number of objects to sample per scene
        seed: Random seed
    
    Returns:
        List of statistics dictionaries
    """
    dataset_dir = Path(base_dir) / dataset
    output_dataset_dir = Path(output_dir) / dataset
    
    if not dataset_dir.exists():
        print(f"Warning: {dataset_dir} does not exist, skipping...")
        return []
    
    stats = []
    scene_dirs = [d for d in dataset_dir.iterdir() if d.is_dir()]
    
    print(f"\nProcessing {len(scene_dirs)} scenes from {dataset}...")
    
    for i, scene_dir in enumerate(scene_dirs):
        scene_graph_file = scene_dir / 'scene_graph.json'
        if not scene_graph_file.exists():
            continue
        
        scene_id = scene_dir.name
        output_scene_dir = output_dataset_dir / scene_id
        output_file = output_scene_dir / 'scene_graph.json'
        
        try:
            scene_stats = filter_scene_graph(scene_graph_file, output_file, num_objects, seed)
            stats.append(scene_stats)
            
            if (i + 1) % 10 == 0:
                print(f"  Processed {i + 1}/{len(scene_dirs)} scenes...")
        except Exception as e:
            print(f"  Error processing {scene_id}: {e}")
    
    print(f"  Completed {dataset}: {len(stats)} scenes processed")
    return stats


def print_statistics(all_stats):
    """Print summary statistics."""
    if not all_stats:
        print("\nNo scenes processed.")
        return
    
    total_original_objects = sum(s['original_objects'] for s in all_stats)
    total_sampled_objects = sum(s['sampled_objects'] for s in all_stats)
    total_original_rels = sum(s['original_relationships'] for s in all_stats)
    total_sampled_rels = sum(s['sampled_relationships'] for s in all_stats)
    total_original_attrs = sum(s['original_attributes'] for s in all_stats)
    total_sampled_attrs = sum(s['sampled_attributes'] for s in all_stats)
    
    print("\n" + "="*70)
    print("SAMPLING STATISTICS")
    print("="*70)
    print(f"\nTotal scenes processed: {len(all_stats)}")
    print(f"\nObjects:")
    print(f"  Original: {total_original_objects:,} ({total_original_objects/len(all_stats):.1f} avg per scene)")
    print(f"  Sampled:  {total_sampled_objects:,} ({total_sampled_objects/len(all_stats):.1f} avg per scene)")
    print(f"  Reduction: {total_original_objects - total_sampled_objects:,} ({(total_original_objects - total_sampled_objects)/total_original_objects*100:.1f}%)")
    
    print(f"\nRelationships:")
    print(f"  Original: {total_original_rels:,} ({total_original_rels/len(all_stats):.1f} avg per scene)")
    print(f"  Sampled:  {total_sampled_rels:,} ({total_sampled_rels/len(all_stats):.1f} avg per scene)")
    print(f"  Reduction: {total_original_rels - total_sampled_rels:,} ({(total_original_rels - total_sampled_rels)/total_original_rels*100:.1f}%)")
    
    print(f"\nAttributes:")
    print(f"  Original: {total_original_attrs:,} ({total_original_attrs/len(all_stats):.1f} avg per scene)")
    print(f"  Sampled:  {total_sampled_attrs:,} ({total_sampled_attrs/len(all_stats):.1f} avg per scene)")
    print(f"  Reduction: {total_original_attrs - total_sampled_attrs:,} ({(total_original_attrs - total_sampled_attrs)/total_original_attrs*100:.1f}%)")
    
    # Show distribution of relationship reduction
    print(f"\nRelationship reduction by scene:")
    print(f"  Min: {min(s['reduction_relationships'] for s in all_stats):,}")
    print(f"  Max: {max(s['reduction_relationships'] for s in all_stats):,}")
    print(f"  Avg: {sum(s['reduction_relationships'] for s in all_stats)/len(all_stats):.1f}")
    
    # Show scenes with most relationships remaining
    print(f"\nTop 10 scenes with most relationships (after sampling):")
    top_scenes = sorted(all_stats, key=lambda s: s['sampled_relationships'], reverse=True)[:10]
    for i, s in enumerate(top_scenes, 1):
        print(f"  {i}. {s['scene_id']}: {s['sampled_relationships']:,} relationships ({s['sampled_objects']} objects)")
    
    print("="*70)


def main():
    parser = argparse.ArgumentParser(description="Sample objects from scene graphs and filter relationships")
    parser.add_argument(
        '--num-objects',
        type=int,
        default=15,
        help='Number of objects to sample per scene (default: 15)'
    )
    parser.add_argument(
        '--input-dir',
        type=str,
        default='data/scenegraphs',
        help='Input directory containing scene graphs (default: data/scenegraphs)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/scenegraphs_sampled',
        help='Output directory for sampled scene graphs (default: data/scenegraphs_sampled)'
    )
    parser.add_argument(
        '--datasets',
        nargs='+',
        choices=['scannet', 'multiscan', '3rscan'],
        default=['scannet', 'multiscan', '3rscan'],
        help='Datasets to process (default: all)'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility (default: 42)'
    )
    parser.add_argument(
        '--stats-file',
        type=str,
        help='Optional: Save statistics to JSON file'
    )
    
    args = parser.parse_args()
    
    print(f"Sampling Configuration:")
    print(f"  Objects per scene: {args.num_objects}")
    print(f"  Input directory: {args.input_dir}")
    print(f"  Output directory: {args.output_dir}")
    print(f"  Datasets: {', '.join(args.datasets)}")
    print(f"  Random seed: {args.seed}")
    
    # Process each dataset
    all_stats = []
    for dataset in args.datasets:
        stats = process_all_scenes(
            dataset=dataset,
            base_dir=args.input_dir,
            output_dir=args.output_dir,
            num_objects=args.num_objects,
            seed=args.seed
        )
        all_stats.extend(stats)
    
    # Print statistics
    print_statistics(all_stats)
    
    # Save statistics to file if requested
    if args.stats_file:
        stats_path = Path(args.stats_file)
        with open(stats_path, 'w') as f:
            json.dump(all_stats, f, indent=2)
        print(f"\nStatistics saved to: {stats_path}")


if __name__ == '__main__':
    main()
