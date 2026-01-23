# Scene Graph Viewer

Interactive 3D viewer for ScanNet and MultiScan scene graphs with filtering and annotation capabilities.

## Quick Start

```bash
# 1. Generate the viewer
# For ScanNet:
python generate_html.py --dataset scannet

# For MultiScan:
python generate_html.py --dataset multiscan

# 2. Start HTTP server
python -m http.server 8000

# 3. Open in browser
# http://localhost:8000/viewer.html
```

## Command Line Options

```bash
python generate_html.py [OPTIONS]

Options:
  -o, --output PATH          Output HTML file path (default: viewer.html)
  -d, --dataset DATASET      Dataset type: scannet or multiscan (default: scannet)
  --multiscan-base PATH      Base path to multiscan data (default: data/multiscan)
  --scene-graph-url URL      Auto-load scene graph from URL
  --ply-url URL              Auto-load PLY file from URL
```

## Features

- **3D Visualization** - View ScanNet and MultiScan scenes with point clouds/meshes and bounding boxes
- **Object Filtering** - Filter objects by attributes (e.g., show only "wooden" objects)
- **Relationship Filtering** - Filter relationships by type (e.g., "above", "below")
- **Relationship Lines** - Click related objects to visualize connections
- **Annotation Mode** - Mark similar objects and export annotations

## Usage

### Viewing Scenes

1. Select a scene from the left panel
2. Browse objects in the Objects panel
3. Click an object to see its relationships

### Filtering

**Objects:**
- Select attributes from dropdown (e.g., "wooden", "red")
- Only matching objects are shown

**Relationships:**
- Select relationship types (e.g., "above", "on")
- Only matching relationships are shown

### Visualizing Relationships

1. Select an object
2. Click on any related object name in the Relationships panel
3. A colored line appears connecting them
4. Click again to remove

### Annotation Mode

1. Enable "Annotation Mode" in controls
2. Select an object
3. Click "Mark Similar" on candidates
4. Export annotations as JSON

## Controls

- **Left-click + drag** - Rotate
- **Right-click + drag** - Pan
- **Mouse wheel** - Zoom
- **Show All Bounding Boxes** - Toggle all boxes
- **Show Mesh** - Toggle 3D model

## Data Structure

### ScanNet

```
data/
  scenegraphs/scannet/
    scene0000_00/
      scene_graph.json
  scannet/public/v2/scans/
    scene0000_00/
      scene0000_00_vh_clean_2.ply
```

### MultiScan

```
data/
  multiscan/
    scene_00000_00/
      scene_00000_00.annotations.json
      scene_00000_00.ply
      textured_mesh/
        scene_00000_00.obj
        scene_00000_00.mtl
        *.png
```

### Scene Graph Format (ScanNet)

```json
{
  "objects": [{
    "id": 0,
    "labels": ["chair"],
    "bbox": {
      "center": [x, y, z],
      "half_dims": [dx, dy, dz],
      "rotation": [qx, qy, qz, qw]
    }
  }],
  "relationships": [{
    "name": "next to",
    "subject_id": 0,
    "recipient_id": [1]
  }],
  "attributes": [{
    "object_id": 0,
    "name": "wooden"
  }]
}
```

### Annotations Format (MultiScan)

MultiScan annotations are automatically converted to scene graph format. The original format includes:

```json
{
  "scanId": "scene_00000_00",
  "objects": [{
    "objectId": 1,
    "label": "wall_cabinet.1",
    "obb": {
      "centroid": [x, y, z],
      "axesLengths": [width, height, depth],
      "normalizedAxes": [...]
    }
  }]
}
```
