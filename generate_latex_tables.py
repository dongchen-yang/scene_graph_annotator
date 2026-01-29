#!/usr/bin/env python3
"""
Generate LaTeX table from evaluation results.

Usage:
    python generate_latex_tables.py
    python generate_latex_tables.py --output my_table.tex
"""

import json
import argparse
from pathlib import Path
from typing import Dict


def load_results():
    """Load all evaluation result files."""
    results = {}
    
    # Load attribute results
    attr_file = Path('attribute_evaluation_all_scenes.json')
    if attr_file.exists():
        with open(attr_file, 'r') as f:
            results['attributes'] = json.load(f)
    
    # Load relationship results
    rel_file = Path('relationship_eval_results.json')
    if rel_file.exists():
        with open(rel_file, 'r') as f:
            results['relationships'] = json.load(f)
    
    # Load similarity results
    sim_file = Path('similarity_eval_results.json')
    if sim_file.exists():
        with open(sim_file, 'r') as f:
            results['similarity'] = json.load(f)
    
    return results


def generate_results_table(results: Dict) -> str:
    """Generate comprehensive results table."""
    
    latex = []
    latex.append("% Scene Graph Evaluation Results")
    latex.append("\\begin{table}[ht]")
    latex.append("\\centering")
    latex.append("\\caption{Scene Graph Evaluation Results (Averaged Across Scenes)}")
    latex.append("\\label{tab:scenegraph_results}")
    latex.append("\\begin{tabular}{llc}")
    latex.append("\\toprule")
    latex.append("\\textbf{Task} & \\textbf{Metric} & \\textbf{Value} \\\\")
    latex.append("\\midrule")
    
    # Attributes
    if 'attributes' in results:
        attr = results['attributes']['overall']
        
        if 'average_image_gt_similarity' in attr and 'average_image_pred_similarity' in attr:
            img_gt = attr['average_image_gt_similarity']
            img_pred = attr['average_image_pred_similarity']
            latex.append(f"\\multirow{{2}}{{*}}{{Attributes}} & CLIP Sim. (Image-Pred) & ${img_pred:.3f}$ \\\\")
            latex.append(f" & CLIP Sim. (Image-GT) & ${img_gt:.3f}$ \\\\")
    
    latex.append("\\midrule")
    
    # Relationships
    if 'relationships' in results:
        rel = results['relationships']['overall']
        accuracy = rel['average_accuracy']
        n_scenes = rel['num_scenes']
        latex.append(f"Relationships & Accuracy & ${accuracy:.3f}$ \\\\")
    
    latex.append("\\midrule")
    
    # Similarity
    if 'similarity' in results:
        sim = results['similarity']['overall_metrics']
        precision = sim['precision']
        recall = sim['recall']
        f1 = sim['f1']
        n_scenes = sim['num_scenes']
        latex.append(f"\\multirow{{3}}{{*}}{{Similarity}} & Precision & ${precision:.3f}$ \\\\")
        latex.append(f" & Recall & ${recall:.3f}$ \\\\")
        latex.append(f" & F1 Score & ${f1:.3f}$ \\\\")
    
    latex.append("\\bottomrule")
    latex.append("\\end{tabular}")
    latex.append("\\end{table}")
    
    return '\n'.join(latex)




def generate_latex_preamble() -> str:
    """Generate LaTeX document preamble with required packages."""
    return """% LaTeX tables generated from scene graph evaluation results
% Required packages:
% \\usepackage{booktabs}
% \\usepackage{multirow}

"""


def main():
    parser = argparse.ArgumentParser(description='Generate LaTeX table from evaluation results')
    parser.add_argument('--output', type=str,
                       default='results_table.tex',
                       help='Output LaTeX file')
    
    args = parser.parse_args()
    
    # Load results
    print("Loading evaluation results...")
    results = load_results()
    
    if not results:
        print("Error: No evaluation result files found!")
        print("Expected files:")
        print("  - attribute_evaluation_all_scenes.json")
        print("  - relationship_eval_results.json")
        print("  - similarity_eval_results.json")
        return
    
    print(f"Loaded {len(results)} evaluation result files")
    
    # Generate table
    latex_output = []
    latex_output.append(generate_latex_preamble())
    latex_output.append(generate_results_table(results))
    
    # Write to file
    output_file = Path(args.output)
    with open(output_file, 'w') as f:
        f.write('\n'.join(latex_output))
    
    print(f"\n✓ LaTeX table generated: {output_file}")
    print(f"\nTo use in your LaTeX document:")
    print(f"  \\input{{{output_file.name}}}")
    print(f"\nOr copy the table directly from the file.")


if __name__ == '__main__':
    main()
