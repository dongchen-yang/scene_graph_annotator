# ScanNet Scene Graph Viewer

An interactive 3D viewer for ScanNet scene graphs with object filtering, relationship visualization, and annotation capabilities.

## Features

- 🎨 **Interactive 3D Visualization** - View ScanNet scenes with Three.js
- 🔍 **Smart Filtering** - Filter objects by attributes and relationships by type
- 📊 **Scene Graph Navigation** - Explore objects and their relationships
- 🔗 **Relationship Lines** - Visualize connections between related objects
- ✏️ **Annotation Mode** - Mark similar objects and export annotations
- 📦 **Standalone HTML** - Single-file viewer, no server dependencies

## Quick Start

### 1. Generate the Viewer

```bash
python generate_html.py
```

This creates `viewer.html` with all available scenes embedded.

### 2. Serve via HTTP

To access scene data, serve the directory via HTTP:

```bash
python -m http.server 8000
```

Then open: `http://localhost:8000/viewer.html`

**Note:** Opening `viewer.html` directly with `file://` won't load scene data due to browser security restrictions. Always use an HTTP server.

## Usage Guide

### Scene Selection

- Browse available scenes in the left panel
- Click a scene to load it automatically
- Scene info displays in the Objects panel

### Object Exploration

**View Objects:**
- All objects listed in the Objects panel
- Shows object ID, labels, and attributes
- Click an object to select it and view its relationships

**Filter Objects:**
- Use the "Filter Objects" dropdown to select attributes
- Multiple attributes can be selected (OR logic)
- Shows count of filtered vs. total objects
- Click × on filter chips to remove filters

### Relationship Visualization

**View Relationships:**
- Select an object to see its relationships in the Relationships panel
- Outgoing: relationships from selected object to others
- Incoming: relationships from others to selected object

**Filter Relationships:**
- Use the "Filter Relationships" dropdown to select types
- Examples: "above", "below", "on", "next to", etc.
- Multiple types can be selected
- Shows count of filtered relationships

**Visualize Connections:**
- Click on any related object name in the Relationships panel
- A colored line appears connecting the two objects
- Both bounding boxes are highlighted in the same color
- Click again to remove the line and highlighting
- Multiple objects can be highlighted simultaneously

### 3D Controls

- **Left-click + drag**: Rotate view
- **Right-click + drag**: Pan camera
- **Mouse wheel**: Zoom in/out
- **Show All Bounding Boxes**: Toggle to see all object boxes at once
- **Show Mesh**: Toggle point cloud/mesh visibility
- **Point Size**: Adjust point size for point cloud mode

### Annotation Mode

Create similarity annotations between objects:

1. **Enable Annotation Mode** in the controls panel
2. **Select an object** from the Objects panel
3. **View candidates** sorted by class match
4. **Preview** by clicking on candidate items (optional)
5. **Mark Similar** to create annotation
6. **Export Annotations** to save as JSON

Annotation files include:
- Pairs of similar objects
- Object labels and IDs
- Whether objects are same/different class
- Timestamps

## Data Structure

The viewer expects this directory structure:

```
data/
  scenegraphs/
    scannet/
      scene0000_00/
        scene_graph.json
      scene0001_00/
        scene_graph.json
      ...
  scannet/
    public/
      v2/
        scans/
          scene0000_00/
            scene0000_00_vh_clean_2.ply
          scene0001_00/
            scene0001_00_vh_clean_2.ply
          ...
```

### Scene Graph Format

Each `scene_graph.json` contains:

```json
{
  "id": "scene0000_00",
  "objects": [
    {
      "id": 0,
      "labels": ["chair"],
      "bbox": {
        "center": [x, y, z],
        "half_dims": [dx, dy, dz],
        "rotation": [qx, qy, qz, qw]
      }
    }
  ],
  "relationships": [
    {
      "id": 0,
      "name": "next to",
      "type": "near",
      "subject_id": 0,
      "recipient_id": [1, 2]
    }
  ],
  "attributes": [
    {
      "object_id": 0,
      "name": "wooden"
    }
  ]
}
```

**Objects:**
- `id`: Unique object identifier
- `labels`: Semantic labels (e.g., "chair", "table")
- `bbox`: Oriented bounding box (center, dimensions, rotation as quaternion)

**Relationships:**
- `name`: Relationship type (e.g., "above", "next to")
- `subject_id`: Source object
- `recipient_id`: Target object(s)

**Attributes:**
- `object_id`: Object this attribute applies to
- `name`: Attribute name (e.g., "wooden", "red", "small")

## Customization

### Generate with Custom Output

```bash
python generate_html.py --output custom_viewer.html
```

### Specify Data Paths

Edit `generate_html.py` to change default data paths:

```python
scenes = list_available_scenes("path/to/scenegraphs")
```

## Requirements

- Python 3.6+
- Modern web browser (Chrome, Firefox, Safari, Edge)
- HTTP server for loading scene data

No Python dependencies required for the viewer itself. The `generate_html.py` script only needs the Python standard library.

## Tips

**Performance:**
- Large scenes are automatically downsampled for performance
- Meshes render faster than point clouds when available
- Filter objects/relationships to focus on specific elements

**Workflow:**
1. Use filters to narrow down objects of interest
2. Click related objects to visualize spatial relationships
3. Switch to annotation mode to mark similar instances
4. Export annotations for downstream tasks

**Browser Compatibility:**
- Best performance in Chrome/Edge
- Firefox and Safari fully supported
- Requires WebGL support

## Troubleshooting

**Scene list is empty:**
- Ensure you're serving via HTTP (not `file://`)
- Check that `data/scenegraphs/scannet/` contains scene directories

**Point cloud not loading:**
- Verify PLY files exist in `data/scannet/public/v2/scans/`
- Check browser console for file path errors
- Some scenes may not have point cloud data

**Bounding boxes in wrong location:**
- Ensure scene graph and PLY file are from the same scene
- Check that coordinate systems match

## License

This tool is for research purposes. ScanNet data usage must comply with the [ScanNet Terms of Use](http://www.scan-net.org/ScanNet_TOS.pdf).

## Citation

If you use this tool in your research, please cite the ScanNet dataset:

```
@inproceedings{dai2017scannet,
  title={ScanNet: Richly-annotated 3D Reconstructions of Indoor Scenes},
  author={Dai, Angela and Chang, Angel X. and Savva, Manolis and Halber, Maciej and Funkhouser, Thomas and Nie{\ss}ner, Matthias},
  booktitle={Proc. Computer Vision and Pattern Recognition (CVPR), IEEE},
  year={2017}
}
```
