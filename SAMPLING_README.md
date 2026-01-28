# Scene Graph Sampling Guide

This guide explains how to sample a subset of objects from scene graphs to reduce the annotation workload.

## Overview

The sampling process:
1. Samples a subset of objects from each scene (prioritizing targetable objects)
2. Keeps only relationships where ALL involved objects are in the sampled set
3. Filters attributes to match the sampled objects
4. Saves the reduced scene graphs to `data/scenegraphs_sampled/`

## Quick Start

### Step 1: Run the Sampling Script

Sample 15 objects per scene (default):
```bash
python sample_scene_graphs.py
```

**Sample from augmented data** (includes <AGENT> objects):
```bash
python sample_scene_graphs.py --input-dir data/scenegraphs_augmented
```

Custom number of objects per scene:
```bash
python sample_scene_graphs.py --num-objects 10
```

Sample only specific datasets:
```bash
python sample_scene_graphs.py --datasets 3rscan scannet
```

Save statistics to file:
```bash
python sample_scene_graphs.py --num-objects 15 --stats-file sampling_stats.json
```

### Step 2: Generate the Viewer for Sampled Data

```bash
python generate_html_sampled.py
```

This creates `viewer_sampled.html` that loads from `data/scenegraphs_sampled/`.

### Step 3: Use the Sampled Viewer

Open `viewer_sampled.html` in your browser (serve via HTTP):
```bash
python -m http.server
# Then open http://localhost:8000/viewer_sampled.html
```

## Script Options

### sample_scene_graphs.py

```
--num-objects N        Number of objects to sample per scene (default: 15)
--input-dir PATH       Input directory with scene graphs (default: data/scenegraphs)
--output-dir PATH      Output directory for sampled graphs (default: data/scenegraphs_sampled)
--datasets [LIST]      Which datasets to process: scannet, multiscan, 3rscan (default: all)
--seed N               Random seed for reproducibility (default: 42)
--stats-file PATH      Save statistics to JSON file
```

### generate_html_sampled.py

Same options as `generate_html.py`, but defaults to:
- Input: `data/scenegraphs_sampled/`
- Output: `viewer_sampled.html`

## Example Workflow

1. **Sample with different object counts:**
   ```bash
   # Try 10 objects per scene
   python sample_scene_graphs.py --num-objects 10 --stats-file stats_10obj.json
   
   # Check the statistics, then try 20 if needed
   python sample_scene_graphs.py --num-objects 20 --stats-file stats_20obj.json
   ```

2. **Generate viewer:**
   ```bash
   python generate_html_sampled.py
   ```

3. **Annotate using the sampled viewer:**
   - Open `viewer_sampled.html`
   - Annotate relationships/attributes
   - Export annotations (per-scene JSON files)

4. **Re-run with different sampling if needed:**
   - The sampling script can be re-run to try different object counts
   - This will overwrite the previous sampled data

## Statistics Output

The script prints:
- Total scenes processed
- Object counts (original vs sampled)
- Relationship counts (original vs sampled)
- Attribute counts (original vs sampled)
- Reduction percentages
- Top 10 scenes with most relationships after sampling

Example output:
```
======================================================================
SAMPLING STATISTICS
======================================================================

Total scenes processed: 429

Objects:
  Original: 14,157 (33.0 avg per scene)
  Sampled:  6,435 (15.0 avg per scene)
  Reduction: 7,722 (54.5%)

Relationships:
  Original: 323,766 (754.7 avg per scene)
  Sampled:  48,230 (112.4 avg per scene)
  Reduction: 275,536 (85.1%)

Attributes:
  Original: 126,555 (295.0 avg per scene)
  Sampled:  72,135 (168.1 avg per scene)
  Reduction: 54,420 (43.0%)
...
```

## Notes

- **Reproducibility:** Use the same `--seed` value to get consistent sampling
- **Prioritization:** The script prioritizes objects in this order:
  1. **`<AGENT>` objects** (ALWAYS included, never filtered out)
  2. `is_targetable=true` objects
  3. Other objects
- **Relationships:** Only keeps relationships where the subject AND all recipients are in the sampled set
- **Original data:** Your original scene graphs in `data/scenegraphs/` are never modified
- **Annotations:** Export/import annotations work the same way with sampled scenes
- **Augmented data:** Use `--input-dir data/scenegraphs_augmented` to sample from augmented scenes with <AGENT> objects

## Comparison: Original vs Sampled

| Dataset | Original Objects/Scene | Sampled (15 obj) | Original Rels/Scene | Sampled Rels/Scene | Reduction |
|---------|------------------------|------------------|---------------------|--------------------|-----------|
| ScanNet | 20-50                  | 15               | 200-800             | 30-150             | ~80-85%   |
| 3RScan  | 20-40                  | 15               | 300-1000            | 40-180             | ~80-85%   |

*Exact numbers depend on scene complexity*
