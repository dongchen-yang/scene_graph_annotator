import json
import argparse
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple
import numpy as np
import torch
from transformers import CLIPProcessor, CLIPModel
import random


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
    
    def compute_similarity_matrix(self, texts1: List[str], texts2: List[str]) -> np.ndarray:
        """Compute pairwise cosine similarity between two sets of texts."""
        if not texts1 or not texts2:
            return np.array([])
        
        emb1 = self.get_text_embeddings(texts1)
        emb2 = self.get_text_embeddings(texts2)
        
        # Compute cosine similarity
        similarity = np.matmul(emb1, emb2.T)
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


def calculate_similarity_scores(
    ground_truth: Dict[int, List[str]], 
    predictions: Dict[int, List[str]],
    evaluator: CLIPSimilarityEvaluator,
    num_random_trials: int = 10
) -> Dict:
    """
    Calculate CLIP similarity scores between predicted and ground truth attributes.
    
    Averages over multiple random orderings to make the evaluation order-invariant.
    
    Args:
        num_random_trials: Number of random orderings to average (default: 10)
    """
    all_object_ids = set(ground_truth.keys()) | set(predictions.keys())
    
    per_object_results = []
    total_similarity = 0.0
    count = 0
    
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
        
        per_object_results.append({
            'object_id': obj_id,
            'similarity_score': similarity_score,
            'similarity_std': similarity_std,
            'ground_truth_text': gt_text,
            'predicted_text': pred_text,
            'ground_truth_attrs': gt_attrs,
            'predicted_attrs': pred_attrs,
            'num_ground_truth': len(gt_attrs),
            'num_predicted': len(pred_attrs)
        })
    
    # Overall average similarity
    average_similarity = total_similarity / count if count > 0 else 0.0
    
    return {
        'overall': {
            'average_similarity': average_similarity,
            'total_objects': count
        },
        'per_object': per_object_results
    }


def print_results(results: Dict, verbose: bool = False):
    """Print evaluation results in a readable format."""
    print("\n" + "="*80)
    print("ATTRIBUTE PREDICTION EVALUATION RESULTS (CLIP Similarity)")
    print("="*80)
    
    overall = results['overall']
    print(f"\nOverall Metrics:")
    print(f"  Average CLIP Similarity: {overall['average_similarity']:.4f}")
    print(f"  Total Objects Evaluated: {overall['total_objects']}")
    
    if verbose:
        print(f"\n{'='*80}")
        print("Per-Object Similarity Scores:")
        print(f"{'='*80}\n")
        
        # Sort by similarity score (lowest first to see worst cases)
        sorted_results = sorted(results['per_object'], key=lambda x: x['similarity_score'])
        
        for obj_result in sorted_results:
            print(f"Object ID: {obj_result['object_id']}")
            print(f"  Similarity Score: {obj_result['similarity_score']:.4f} (±{obj_result['similarity_std']:.4f})")
            print(f"  Ground Truth ({obj_result['num_ground_truth']}): {obj_result['ground_truth_text']}")
            print(f"  Predicted ({obj_result['num_predicted']}): {obj_result['predicted_text']}")
            print()


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
    
    args = parser.parse_args()
    
    # Validate files exist
    if not Path(args.validation).exists():
        print(f"Error: Validation file not found: {args.validation}")
        return
    
    if not Path(args.scene_graph).exists():
        print(f"Error: Scene graph file not found: {args.scene_graph}")
        return
    
    # Load data
    print(f"Loading ground truth from: {args.validation}")
    ground_truth = load_ground_truth(args.validation)
    
    print(f"Loading predictions from: {args.scene_graph}")
    predictions = load_predictions(args.scene_graph)
    
    # Initialize CLIP evaluator
    evaluator = CLIPSimilarityEvaluator(model_name=args.model, device=args.device)
    
    # Calculate similarity scores
    print(f"Calculating CLIP similarity scores (averaging over {args.num_trials} random orderings)...")
    
    results = calculate_similarity_scores(
        ground_truth, 
        predictions, 
        evaluator, 
        num_random_trials=args.num_trials
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

