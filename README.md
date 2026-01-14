# Scene Graph Annotation Tool for ScanNet

This tool provides a web-based interface to load and visualize ScanNet 3D scenes along with their associated scene graphs.

## Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Standalone HTML Viewer (Simplest - No Server Needed!)

Generate and use the standalone HTML viewer:

```bash
# Generate the HTML file
python generate_html.py

# Then open viewer.html in your browser:
# Option 1: Double-click viewer.html
# Option 2: Open from browser: File > Open > viewer.html
```

You can also specify a custom output path:
```bash
python generate_html.py --output my_viewer.html
```

Then use the file inputs to load:
- Scene Graph JSON file (e.g., `scene_graph.json`)
- Point Cloud PLY file (e.g., `scene0000_00_vh_clean_2.ply`)

**This is completely standalone - no server required!**

### Web Server Interface (Alternative)

If you prefer a server-based approach with scene selection:

Start the web server:

```bash
python run_server.py
```

Then open your browser to: `http://localhost:5000`

**Web Interface Features:**
- Interactive 3D visualization using Three.js
- Scene selector dropdown
- Object list with labels
- Click objects to highlight their bounding boxes
- Toggle point cloud and bounding boxes on/off
- Mouse controls: drag to rotate, wheel to zoom

### Command-Line Interface

You can also use the command-line tool:

```bash
# List available scenes
python scannet_annotation_tool.py --list_scenes

# Visualize a scene (opens desktop window)
python scannet_annotation_tool.py --scene_id scene0000_00
```

### Options for CLI

- `--scene_id`: Scene ID to load (e.g., `scene0000_00`)
- `--list_scenes`: List all available scenes
- `--scannet_base`: Base path to ScanNet data (default: `data/scannet/public/v2`)
- `--scenegraph_base`: Base path to scene graph data (default: `data/scenegraphs/scannet`)
- `--no_bboxes`: Don't show bounding boxes (only point cloud)
- `--point_size`: Point size in visualization (default: 1.0)

## Python API

You can also use the loader programmatically:

```python
from scannet_loader import ScanNetScene

# Load a scene
scene = ScanNetScene('scene0000_00')

# Print scene summary
print(scene.get_summary())

# Load point cloud
scene.load_point_cloud()

# Get object information
obj = scene.get_object_by_id(0)
print(f"Object 0: {obj['labels']}")

# Get relationships for an object
relationships = scene.get_relationships_for_object(0)
print(f"Object 0 has {len(relationships)} relationships")

# Visualize
scene.visualize_scene(show_bboxes=True)
```

## Data Structure

### Scene Graph Format

The scene graph JSON contains:

- **objects**: List of objects with:
  - `id`: Object ID
  - `labels`: List of semantic labels
  - `bbox`: Bounding box with `center`, `half_dims`, and `rotation` (quaternion)
  - `is_targetable`: Whether object can be targeted
  - `attribute_ids`: List of attribute IDs

- **relationships**: List of relationships with:
  - `id`: Relationship ID
  - `name`: Relationship name (e.g., "next to")
  - `type`: Relationship type (e.g., "near")
  - `subject_id`: Subject object ID
  - `recipient_id`: List of recipient object IDs

- **attributes**: Dictionary of attribute data

### ScanNet 3D Models

The tool loads PLY point cloud files from the ScanNet dataset. By default, it looks for files named like `{scene_id}_vh_clean_2.ply`.

## Example

```bash
# List available scenes
python scannet_annotation_tool.py --list_scenes

# Visualize scene0000_00
python scannet_annotation_tool.py --scene_id scene0000_00

# Visualize without bounding boxes
python scannet_annotation_tool.py --scene_id scene0000_00 --no_bboxes

# Visualize with larger points
python scannet_annotation_tool.py --scene_id scene0000_00 --point_size 2.0
```

