import json
import argparse
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple
import numpy as np
import torch
from transformers import CLIPProcessor, CLIPModel
import random
from PIL import Image
import glob


class CLIPSimilarityEvaluator:
    def __init__(self, model_name: str = "openai/clip-vit-base-patch32", device: str = None):
        """Initialize CLIP model for computing attribute similarity."""
        self.device = device if device else ("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Loading CLIP model: {model_name} on {self.device}")
        
        self.model = CLIPModel.from_pretrained(model_name).to(self.device)
        self.processor = CLIPProcessor.from_pretrained(model_name)
        self.model.eval()
    
    def get_text_embeddings(self, texts: List[str]) -> np.ndarray:
        """Get CLIP embeddings for a list of texts."""
        if not texts:
            return np.array([])
        
        with torch.no_grad():
            inputs = self.processor(text=texts, return_tensors="pt", padding=True, truncation=True)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            text_features = self.model.get_text_features(**inputs)
            
            # Extract tensor if it's wrapped in a model output object
            if hasattr(text_features, 'pooler_output'):
                embeddings = text_features.pooler_output
            elif hasattr(text_features, 'last_hidden_state'):
                embeddings = text_features.last_hidden_state[:, 0]  # Use CLS token
            else:
                embeddings = text_features  # Already a tensor
            
            # Normalize embeddings
            embeddings = embeddings / torch.norm(embeddings, dim=-1, keepdim=True)
        
        return embeddings.cpu().numpy()
    
    def get_image_embeddings(self, images: List[Image.Image]) -> np.ndarray:
        """Get CLIP embeddings for a list of images."""
        if not images:
            return np.array([])
        
        with torch.no_grad():
            inputs = self.processor(images=images, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            image_features = self.model.get_image_features(**inputs)
            
            # Extract tensor if it's wrapped in a model output object
            if hasattr(image_features, 'pooler_output'):
                embeddings = image_features.pooler_output
            elif hasattr(image_features, 'last_hidden_state'):
                embeddings = image_features.last_hidden_state[:, 0]  # Use CLS token
            else:
                embeddings = image_features  # Already a tensor
            
            # Normalize embeddings
            embeddings = embeddings / torch.norm(embeddings, dim=-1, keepdim=True)
        
        return embeddings.cpu().numpy()
    
    def compute_similarity_matrix(self, texts1: List[str], texts2: List[str]) -> np.ndarray:
        """Compute pairwise cosine similarity between two sets of texts."""
        if not texts1 or not texts2:
            return np.array([])
        
        emb1 = self.get_text_embeddings(texts1)
        emb2 = self.get_text_embeddings(texts2)
        
        # Compute cosine similarity
        similarity = np.matmul(emb1, emb2.T)
        return similarity
    
    def compute_image_text_similarity(self, images: List[Image.Image], texts: List[str]) -> np.ndarray:
        """Compute similarity between images and texts."""
        if not images or not texts:
            return np.array([])
        
        image_emb = self.get_image_embeddings(images)
        text_emb = self.get_text_embeddings(texts)
        
        # Compute cosine similarity
        similarity = np.matmul(image_emb, text_emb.T)
        return similarity


def load_ground_truth(validation_file: str) -> Dict[int, List[str]]:
    """
    Load ground truth attributes from validation results.
    Ground truth = correct predicted attributes + added attributes
    
    Returns:
        Dict mapping object_id to list of attribute names
    """
    with open(validation_file, 'r') as f:
        data = json.load(f)
    
    ground_truth = defaultdict(list)
    
    # Add correct predicted attributes
    if 'attributes' in data and 'predicted' in data['attributes']:
        for attr in data['attributes']['predicted']['items']:
            if attr['validation'] == 'correct':
                ground_truth[attr['object_id']].append(attr['name'])
    
    # Add manually added attributes (missing from predictions)
    if 'attributes' in data and 'added' in data['attributes']:
        for attr in data['attributes']['added']:
            ground_truth[attr['object_id']].append(attr['name'])
    
    return ground_truth


def load_predictions(scene_graph_file: str) -> Dict[int, List[str]]:
    """
    Load predicted attributes from scene graph.
    
    Returns:
        Dict mapping object_id to list of attribute names
    """
    with open(scene_graph_file, 'r') as f:
        data = json.load(f)
    
    predictions = defaultdict(list)
    
    if 'attributes' in data:
        for attr in data['attributes']:
            predictions[attr['object_id']].append(attr['name'])
    
    return predictions


def find_object_images(scene_id: str, object_id: int, dataset: str, images_base_dir: str = "data/images") -> List[str]:
    """
    Find all image paths for a given object.
    
    Args:
        scene_id: Scene identifier (e.g., 'scene0001_00' or '02b33dfb-...')
        object_id: Object ID
        dataset: 'scannet' or '3rscan'
        images_base_dir: Base directory for images
    
    Returns:
        List of image file paths
    """
    image_dir = Path(images_base_dir) / dataset / scene_id
    if not image_dir.exists():
        return []
    
    # Find all images for this object: id_{object_id}_frame_*_rgb.png
    pattern = f"id_{object_id}_frame_*_rgb.png"
    image_paths = glob.glob(str(image_dir / pattern))
    return sorted(image_paths)


def load_object_images(image_paths: List[str], max_images: int = 3) -> List[Image.Image]:
    """
    Load images from file paths.
    
    Args:
        image_paths: List of image file paths
        max_images: Maximum number of images to load per object
    
    Returns:
        List of PIL Images
    """
    images = []
    for img_path in image_paths[:max_images]:
        try:
            img = Image.open(img_path).convert('RGB')
            images.append(img)
        except Exception as e:
            print(f"Warning: Could not load image {img_path}: {e}")
            continue
    return images


def calculate_similarity_scores(
    ground_truth: Dict[int, List[str]], 
    predictions: Dict[int, List[str]],
    evaluator: CLIPSimilarityEvaluator,
    num_random_trials: int = 10,
    scene_id: str = None,
    dataset: str = None,
    include_image_similarity: bool = False,
    max_images_per_object: int = 3
) -> Dict:
    """
    Calculate CLIP similarity scores between predicted and ground truth attributes.
    
    Averages over multiple random orderings to make the evaluation order-invariant.
    Optionally includes image-based CLIP similarity.
    
    Args:
        num_random_trials: Number of random orderings to average (default: 10)
        scene_id: Scene identifier (for loading images)
        dataset: Dataset name ('scannet' or '3rscan', for loading images)
        include_image_similarity: Whether to compute image-text similarity
        max_images_per_object: Maximum images to load per object
    """
    all_object_ids = set(ground_truth.keys()) | set(predictions.keys())
    
    per_object_results = []
    total_similarity = 0.0
    total_image_gt_sim = 0.0
    total_image_pred_sim = 0.0
    count = 0
    image_count = 0
    
    for obj_id in sorted(all_object_ids):
        gt_attrs = ground_truth.get(obj_id, [])
        pred_attrs = predictions.get(obj_id, [])
        
        if not gt_attrs and not pred_attrs:
            continue
        
        # Combine attributes into single text
        if gt_attrs and pred_attrs:
            # Average over multiple random orderings
            scores = []
            
            for trial in range(num_random_trials):
                # Shuffle attributes
                shuffled_gt = gt_attrs.copy()
                shuffled_pred = pred_attrs.copy()
                random.shuffle(shuffled_gt)
                random.shuffle(shuffled_pred)
                
                gt_text = ", ".join(shuffled_gt)
                pred_text = ", ".join(shuffled_pred)
                
                similarity_matrix = evaluator.compute_similarity_matrix([pred_text], [gt_text])
                scores.append(float(similarity_matrix[0, 0]))
            
            similarity_score = np.mean(scores)
            similarity_std = np.std(scores)
            
            # For display, use sorted order
            gt_text = ", ".join(sorted(gt_attrs))
            pred_text = ", ".join(sorted(pred_attrs))
        
        elif not gt_attrs:
            # Only predictions, no ground truth
            similarity_score = 0.0
            similarity_std = 0.0
            gt_text = "(none)"
            pred_text = ", ".join(sorted(pred_attrs))
        
        else:  # not pred_attrs
            # Only ground truth, no predictions
            similarity_score = 0.0
            similarity_std = 0.0
            gt_text = ", ".join(sorted(gt_attrs))
            pred_text = "(none)"
        
        total_similarity += similarity_score
        count += 1
        
        result_dict = {
            'object_id': obj_id,
            'similarity_score': similarity_score,
            'similarity_std': similarity_std,
            'ground_truth_text': gt_text,
            'predicted_text': pred_text,
            'ground_truth_attrs': gt_attrs,
            'predicted_attrs': pred_attrs,
            'num_ground_truth': len(gt_attrs),
            'num_predicted': len(pred_attrs)
        }
        
        # Add image-based similarity if requested
        if include_image_similarity and scene_id and dataset:
            image_paths = find_object_images(scene_id, obj_id, dataset)
            result_dict['num_image_files'] = len(image_paths)
            result_dict['has_images'] = len(image_paths) > 0
            
            if image_paths and gt_attrs and pred_attrs:
                images = load_object_images(image_paths, max_images=max_images_per_object)
                if images:
                    # Compute image-text similarity for ground truth and predicted
                    img_gt_sim_matrix = evaluator.compute_image_text_similarity(images, [gt_text])
                    img_pred_sim_matrix = evaluator.compute_image_text_similarity(images, [pred_text])
                    
                    # Average across all images
                    img_gt_similarity = float(np.mean(img_gt_sim_matrix))
                    img_pred_similarity = float(np.mean(img_pred_sim_matrix))
                    
                    result_dict['image_gt_similarity'] = img_gt_similarity
                    result_dict['image_pred_similarity'] = img_pred_similarity
                    result_dict['num_images_loaded'] = len(images)
                    
                    total_image_gt_sim += img_gt_similarity
                    total_image_pred_sim += img_pred_similarity
                    image_count += 1
                else:
                    result_dict['image_error'] = 'Failed to load images'
            elif not image_paths:
                result_dict['image_error'] = 'No images found'
            elif not gt_attrs or not pred_attrs:
                result_dict['image_error'] = 'No attributes to compare'
        
        per_object_results.append(result_dict)
    
    # Overall average similarity
    average_similarity = total_similarity / count if count > 0 else 0.0
    
    result = {
        'overall': {
            'average_similarity': average_similarity,
            'total_objects': count
        },
        'per_object': per_object_results
    }
    
    # Add image-based metrics if computed
    if include_image_similarity:
        objects_with_images = sum(1 for r in per_object_results if r.get('has_images', False))
        objects_with_loaded_images = sum(1 for r in per_object_results if 'image_gt_similarity' in r)
        
        result['overall']['objects_with_images'] = objects_with_images
        result['overall']['objects_without_images'] = count - objects_with_images
        result['overall']['objects_with_loaded_images'] = objects_with_loaded_images
        
        if image_count > 0:
            result['overall']['average_image_gt_similarity'] = total_image_gt_sim / image_count
            result['overall']['average_image_pred_similarity'] = total_image_pred_sim / image_count
    
    return result


def print_results(results: Dict, verbose: bool = False):
    """Print evaluation results in a readable format."""
    print("\n" + "="*80)
    print("ATTRIBUTE PREDICTION EVALUATION RESULTS (CLIP Similarity)")
    print("="*80)
    
    overall = results['overall']
    print(f"\nText-to-Text Similarity:")
    print(f"  Average CLIP Similarity: {overall['average_similarity']:.4f}")
    print(f"  Total Objects Evaluated: {overall['total_objects']}")
    
    # Print image-based metrics if available
    if 'objects_with_images' in overall:
        print(f"\nImage Availability:")
        print(f"  Objects with Images:       {overall['objects_with_images']}/{overall['total_objects']} "
              f"({100*overall['objects_with_images']/overall['total_objects']:.1f}%)")
        print(f"  Objects without Images:    {overall['objects_without_images']}/{overall['total_objects']} "
              f"({100*overall['objects_without_images']/overall['total_objects']:.1f}%)")
        
        if 'average_image_gt_similarity' in overall:
            print(f"\nImage-to-Text Similarity:")
            print(f"  Objects Successfully Evaluated: {overall['objects_with_loaded_images']}")
            print(f"  Avg Image-GT Similarity:        {overall['average_image_gt_similarity']:.4f}")
            print(f"  Avg Image-Pred Similarity:      {overall['average_image_pred_similarity']:.4f}")
            
            # Compare which is better
            diff = overall['average_image_pred_similarity'] - overall['average_image_gt_similarity']
            if diff > 0.01:
                print(f"  → Predictions are {diff:.4f} more similar to images than GT")
            elif diff < -0.01:
                print(f"  → GT is {abs(diff):.4f} more similar to images than predictions")
            else:
                print(f"  → Predictions and GT have similar image alignment")
    
    if verbose:
        print(f"\n{'='*80}")
        print("Per-Object Similarity Scores:")
        print(f"{'='*80}\n")
        
        # Sort by similarity score (lowest first to see worst cases)
        sorted_results = sorted(results['per_object'], key=lambda x: x['similarity_score'])
        
        for obj_result in sorted_results:
            print(f"Object ID: {obj_result['object_id']}")
            print(f"  Text-Text Similarity: {obj_result['similarity_score']:.4f} (±{obj_result['similarity_std']:.4f})")
            
            # Print image availability
            if 'has_images' in obj_result:
                if obj_result['has_images']:
                    print(f"  Images Found: {obj_result['num_image_files']} file(s)", end='')
                    if 'image_gt_similarity' in obj_result:
                        print(f" ({obj_result['num_images_loaded']} loaded)")
                    else:
                        print(f" (not loaded: {obj_result.get('image_error', 'unknown error')})")
                else:
                    print(f"  Images Found: None")
            
            # Print image-based metrics if available
            if 'image_gt_similarity' in obj_result:
                print(f"  Image-GT Similarity:  {obj_result['image_gt_similarity']:.4f}")
                print(f"  Image-Pred Similarity:{obj_result['image_pred_similarity']:.4f}")
                diff = obj_result['image_pred_similarity'] - obj_result['image_gt_similarity']
                indicator = "Pred better" if diff > 0.01 else "GT better" if diff < -0.01 else "Similar"
                print(f"  Image Comparison:     {indicator} (diff: {diff:+.4f})")
            
            print(f"  Ground Truth ({obj_result['num_ground_truth']}): {obj_result['ground_truth_text']}")
            print(f"  Predicted ({obj_result['num_predicted']}): {obj_result['predicted_text']}")
            print()


def extract_scene_info(scene_graph_path: str) -> tuple:
    """
    Extract scene_id and dataset from scene graph path.
    
    Examples:
        data/scenegraphs_sampled/scannet/scene0001_00/scene_graph.json -> ('scene0001_00', 'scannet')
        data/scenegraphs_sampled/3rscan/02b33dfb-.../scene_graph.json -> ('02b33dfb-...', '3rscan')
    """
    path = Path(scene_graph_path)
    scene_id = path.parent.name
    dataset = path.parent.parent.name
    return scene_id, dataset


def main():
    parser = argparse.ArgumentParser(
        description='Evaluate attribute prediction against ground truth using CLIP similarity'
    )
    parser.add_argument(
        '--validation',
        type=str,
        required=True,
        help='Path to validation results JSON file (ground truth)'
    )
    parser.add_argument(
        '--scene-graph',
        type=str,
        required=True,
        help='Path to scene graph JSON file (predictions)'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Path to save evaluation results JSON (optional)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Print per-object results'
    )
    parser.add_argument(
        '--model',
        type=str,
        default='openai/clip-vit-base-patch32',
        help='CLIP model to use (default: openai/clip-vit-base-patch32)'
    )
    parser.add_argument(
        '--device',
        type=str,
        default=None,
        help='Device to use (cuda/cpu, default: auto-detect)'
    )
    parser.add_argument(
        '--num-trials',
        type=int,
        default=10,
        help='Number of random orderings to average for order-invariant evaluation (default: 10)'
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
    
    # Validate files exist
    if not Path(args.validation).exists():
        print(f"Error: Validation file not found: {args.validation}")
        return
    
    if not Path(args.scene_graph).exists():
        print(f"Error: Scene graph file not found: {args.scene_graph}")
        return
    
    # Extract scene info for image loading
    scene_id, dataset = extract_scene_info(args.scene_graph)
    print(f"Scene: {scene_id}, Dataset: {dataset}")
    
    # Load data
    print(f"Loading ground truth from: {args.validation}")
    ground_truth = load_ground_truth(args.validation)
    
    print(f"Loading predictions from: {args.scene_graph}")
    predictions = load_predictions(args.scene_graph)
    
    # Initialize CLIP evaluator
    evaluator = CLIPSimilarityEvaluator(model_name=args.model, device=args.device)
    
    # Calculate similarity scores
    if args.include_images:
        print(f"Calculating CLIP similarity scores (text + image, averaging over {args.num_trials} random orderings)...")
    else:
        print(f"Calculating CLIP similarity scores (text only, averaging over {args.num_trials} random orderings)...")
    
    results = calculate_similarity_scores(
        ground_truth, 
        predictions, 
        evaluator, 
        num_random_trials=args.num_trials,
        scene_id=scene_id,
        dataset=dataset,
        include_image_similarity=args.include_images,
        max_images_per_object=args.max_images
    )
    
    # Print results
    print_results(results, verbose=args.verbose)
    
    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to: {args.output}")


if __name__ == '__main__':
    main()

