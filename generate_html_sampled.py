#!/usr/bin/env python3
"""
Generate standalone HTML viewer for ScanNet scene graphs.
"""

import os
import json
from pathlib import Path


def list_available_scenes(scenegraph_base="data/scenegraphs_sampled/scannet"):
    """
    List all available scenes in the scenegraph directory.
    
    Args:
        scenegraph_base: Base path to scene graph data directory
        
    Returns:
        List of scene IDs (e.g., ['scene0000_00', 'scene0001_00', ...])
    """
    base_path = Path(scenegraph_base)
    if not base_path.exists():
        return []
    
    scenes = []
    for scene_dir in sorted(base_path.iterdir()):
        if scene_dir.is_dir():
            scene_graph_file = scene_dir / "scene_graph.json"
            if scene_graph_file.exists():
                scenes.append(scene_dir.name)
    
    return scenes


def list_multiscan_scenes(multiscan_base="data/multiscan"):
    """
    List all available multiscan scenes that have scene graph data.
    
    Args:
        multiscan_base: Base path to multiscan data directory (used for PLY files)
        
    Returns:
        List of scene IDs (e.g., ['scene_00000_00', 'scene_00001_00', ...])
    """
    # Look for scenes in the scenegraphs directory (has proper relationships & attributes)
    scenegraph_path = Path("data/scenegraphs_sampled/multiscan")
    if not scenegraph_path.exists():
        return []
    
    scenes = []
    for scene_dir in sorted(scenegraph_path.iterdir()):
        if scene_dir.is_dir() and scene_dir.name.startswith('scene_'):
            # Check for scene_graph.json file
            scene_graph_file = scene_dir / "scene_graph.json"
            if scene_graph_file.exists():
                scenes.append(scene_dir.name)
    
    return scenes


def list_3rscan_scenes(rscan_base="data/3rscan/download"):
    """
    List all available 3RScan scenes that have scene graph data.
    
    Args:
        rscan_base: Base path to 3RScan data directory (used for mesh files)
        
    Returns:
        List of scene IDs (UUIDs like '02b33dfb-be2b-2d54-92d2-cd012b2b3c40')
    """
    # Look for scenes in the scenegraphs directory
    scenegraph_path = Path("data/scenegraphs_sampled/3rscan")
    if not scenegraph_path.exists():
        return []
    
    scenes = []
    for scene_dir in sorted(scenegraph_path.iterdir()):
        if scene_dir.is_dir():
            # 3RScan scene IDs are UUIDs (8-4-4-4-12 hex format)
            scene_id = scene_dir.name
            # Check for scene_graph.json file
            scene_graph_file = scene_dir / "scene_graph.json"
            if scene_graph_file.exists():
                scenes.append(scene_id)
    
    return scenes


PREDICATES_CACHE_FILE = Path("data/predicates_cache.json")

def collect_all_predicates(force_refresh=False):
    """
    Collect all unique relationship predicates from all scene graphs.
    Uses a cache file to avoid re-scanning all scenes every time.
    
    Args:
        force_refresh: If True, ignore cache and rescan all scenes
    
    Returns:
        Sorted list of unique predicate strings
    """
    # Check if cache exists and use it
    if not force_refresh and PREDICATES_CACHE_FILE.exists():
        try:
            with open(PREDICATES_CACHE_FILE, 'r') as f:
                cached = json.load(f)
            print(f"Using cached predicates from {PREDICATES_CACHE_FILE}")
            return cached
        except:
            pass
    
    print("Scanning all scene graphs for predicates (this may take a while)...")
    predicates = set()
    
    # Collect from ScanNet scenes
    scannet_path = Path("data/scenegraphs_sampled/scannet")
    if scannet_path.exists():
        for scene_dir in scannet_path.iterdir():
            if scene_dir.is_dir():
                sg_file = scene_dir / "scene_graph.json"
                if sg_file.exists():
                    try:
                        with open(sg_file, 'r') as f:
                            data = json.load(f)
                        for rel in data.get('relationships', []):
                            if rel.get('name'):
                                predicates.add(rel['name'])
                    except:
                        pass
    
    # Collect from MultiScan scenes
    multiscan_path = Path("data/scenegraphs_sampled/multiscan")
    if multiscan_path.exists():
        for scene_dir in multiscan_path.iterdir():
            if scene_dir.is_dir():
                sg_file = scene_dir / "scene_graph.json"
                if sg_file.exists():
                    try:
                        with open(sg_file, 'r') as f:
                            data = json.load(f)
                        for rel in data.get('relationships', []):
                            if rel.get('name'):
                                predicates.add(rel['name'])
                    except:
                        pass
    
    # Collect from 3RScan scenes
    rscan_path = Path("data/scenegraphs_sampled/3rscan")
    if rscan_path.exists():
        for scene_dir in rscan_path.iterdir():
            if scene_dir.is_dir():
                sg_file = scene_dir / "scene_graph.json"
                if sg_file.exists():
                    try:
                        with open(sg_file, 'r') as f:
                            data = json.load(f)
                        for rel in data.get('relationships', []):
                            if rel.get('name'):
                                predicates.add(rel['name'])
                    except:
                        pass
    
    result = sorted(predicates)
    
    # Save to cache
    try:
        PREDICATES_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(PREDICATES_CACHE_FILE, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"Cached predicates to {PREDICATES_CACHE_FILE}")
    except Exception as e:
        print(f"Warning: Could not cache predicates: {e}")
    
    return result


def convert_multiscan_to_scenegraph(annotations_file):
    """
    Convert multiscan annotations format to scene graph format.
    
    Args:
        annotations_file: Path to multiscan annotations.json file
        
    Returns:
        Dict with scene graph format (objects, relationships, attributes)
    """
    with open(annotations_file, 'r') as f:
        data = json.load(f)
    
    scene_id = data.get('scanId', 'unknown')
    objects = []
    
    # Convert multiscan objects to scene graph objects
    for obj in data.get('objects', []):
        obj_id = obj.get('objectId')
        label = obj.get('label', 'unknown')
        obb = obj.get('obb', {})
        
        # Extract OBB parameters
        centroid = obb.get('centroid', [0, 0, 0])
        axes_lengths = obb.get('axesLengths', [1, 1, 1])
        normalized_axes = obb.get('normalizedAxes', [1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1])
        
        # Convert normalized axes (3x3 matrix) to quaternion
        # The normalized axes are stored as a flattened 4x4 matrix (row-major)
        # Extract the 3x3 rotation matrix
        m = normalized_axes
        rotation_matrix = [
            [m[0], m[1], m[2]],
            [m[4], m[5], m[6]],
            [m[8], m[9], m[10]]
        ]
        
        # Convert rotation matrix to quaternion (simplified - assumes identity for now)
        # For proper conversion, we'd use a full matrix to quaternion converter
        # For now, use identity quaternion
        rotation = [0, 0, 0, 1]  # [qx, qy, qz, qw]
        
        # Half dimensions (multiscan uses full lengths)
        half_dims = [d / 2 for d in axes_lengths]
        
        scene_obj = {
            'id': obj_id,
            'labels': [label],
            'bbox': {
                'center': centroid,
                'half_dims': half_dims,
                'rotation': rotation
            }
        }
        objects.append(scene_obj)
    
    # Create scene graph structure
    scene_graph = {
        'id': scene_id,
        'objects': objects,
        'relationships': [],  # Multiscan doesn't have relationships by default
        'attributes': {}       # Multiscan doesn't have attributes by default
    }
    
    return scene_graph


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ScanNet Scene Graph Viewer</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/gh/mrdoob/three.js@r128/examples/js/controls/OrbitControls.js"></script>
    <script src="https://cdn.jsdelivr.net/gh/mrdoob/three.js@r128/examples/js/loaders/MTLLoader.js"></script>
    <script src="https://cdn.jsdelivr.net/gh/mrdoob/three.js@r128/examples/js/loaders/OBJLoader.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            display: flex;
            height: 100vh;
            overflow: hidden;
            background: #1a1a1a;
        }

        #left-panel {
            width: 220px;
            background: #f5f5f5;
            border-right: 1px solid #ddd;
            display: flex;
            flex-direction: column;
            overflow-y: auto;
        }

        #objects-panel {
            width: 350px;
            background: #f5f5f5;
            border-right: 1px solid #ddd;
            display: flex;
            flex-direction: column;
            overflow-y: auto;
        }

        #relationships-panel {
            width: 300px;
            background: #f5f5f5;
            border-right: 1px solid #ddd;
            display: flex;
            flex-direction: column;
            overflow-y: auto;
        }

        #left-panel h2, #objects-panel h2, #relationships-panel h2 {
            padding: 15px;
            background: #2c3e50;
            color: white;
            font-size: 16px;
            margin: 0;
        }

        #file-loader {
            padding: 15px;
            border-bottom: 1px solid #ddd;
            background: white;
        }

        #file-loader h3 {
            font-size: 14px;
            margin-bottom: 10px;
            color: #333;
        }

        .file-input-group {
            margin-bottom: 15px;
        }

        .file-input-group label {
            display: block;
            font-size: 12px;
            color: #666;
            margin-bottom: 5px;
        }

        .file-input-group input[type="file"] {
            width: 100%;
            padding: 8px;
            font-size: 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            background: white;
        }

        .file-status {
            font-size: 11px;
            color: #666;
            margin-top: 5px;
            font-style: italic;
        }

        .file-status.loaded {
            color: #27ae60;
        }

        #scene-info {
            padding: 10px 15px;
            border-bottom: 1px solid #ddd;
            background: #e8f4f8;
        }

        #scene-info h3 {
            font-size: 13px;
            margin-bottom: 8px;
            color: #2c3e50;
            font-weight: bold;
        }

        #scene-info p {
            font-size: 11px;
            color: #555;
            margin: 3px 0;
            line-height: 1.4;
        }

        #object-filters, #relationship-filters {
            padding: 10px 15px;
            border-bottom: 1px solid #ddd;
            background: #fff9e6;
        }

        #object-filters h3, #relationship-filters h3 {
            font-size: 12px;
            margin-bottom: 8px;
            color: #2c3e50;
            font-weight: bold;
        }

        .filter-section {
            margin-bottom: 8px;
        }

        .filter-section label {
            font-size: 11px;
            color: #555;
            display: block;
            margin-bottom: 4px;
        }

        .filter-section select {
            width: 100%;
            padding: 5px;
            font-size: 11px;
            border: 1px solid #ddd;
            border-radius: 3px;
            background: white;
        }

        .filter-chips {
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
            margin-top: 5px;
        }

        .filter-chip {
            display: inline-flex;
            align-items: center;
            padding: 3px 8px;
            background: #3498db;
            color: white;
            font-size: 10px;
            border-radius: 12px;
            cursor: pointer;
            transition: background 0.2s;
        }

        .filter-chip:hover {
            background: #2980b9;
        }

        .filter-chip .remove {
            margin-left: 5px;
            font-weight: bold;
            font-size: 12px;
        }

        .clear-filters-btn {
            background: #95a5a6;
            color: white;
            border: none;
            padding: 4px 10px;
            border-radius: 3px;
            cursor: pointer;
            font-size: 10px;
            margin-top: 5px;
            width: 100%;
        }

        .clear-filters-btn:hover {
            background: #7f8c8d;
        }

        #objects-list {
            flex: 1;
            overflow-y: auto;
            padding: 15px;
        }

        #objects-list h3 {
            font-size: 14px;
            margin-bottom: 10px;
            color: #333;
        }

        .object-item {
            padding: 10px;
            margin-bottom: 8px;
            background: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.2s;
        }

        .object-item:hover {
            border-color: #3498db;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .object-item.selected {
            border-color: #3498db;
            background: #ebf5fb;
        }

        .object-item .object-id {
            font-weight: bold;
            color: #2c3e50;
            font-size: 13px;
        }

        .object-item .object-labels {
            font-size: 12px;
            color: #7f8c8d;
            margin-top: 4px;
        }

        .object-item .object-attributes {
            font-size: 11px;
            color: #16a085;
            margin-top: 4px;
            font-style: italic;
        }

        .attribute-tag {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 2px 6px;
            margin: 2px 2px 0 0;
            background: #e8f8f5;
            border: 1px solid #16a085;
            border-radius: 3px;
            font-size: 10px;
            font-style: normal;
        }
        
        .attribute-tag.validated-correct {
            background: #d4edda;
            border-color: #28a745;
        }
        
        .attribute-tag.validated-incorrect {
            background: #f8d7da;
            border-color: #dc3545;
            text-decoration: line-through;
        }
        
        .attr-validation-btns {
            display: inline-flex;
            gap: 2px;
            margin-left: 4px;
        }
        
        .attr-validation-btn {
            width: 16px;
            height: 16px;
            border: none;
            border-radius: 3px;
            cursor: pointer;
            font-size: 10px;
            line-height: 16px;
            padding: 0;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .attr-validation-btn.correct {
            background: #28a745;
            color: white;
        }
        
        .attr-validation-btn.correct:hover {
            background: #218838;
        }
        
        .attr-validation-btn.incorrect {
            background: #dc3545;
            color: white;
        }
        
        .attr-validation-btn.incorrect:hover {
            background: #c82333;
        }
        
        .attr-validation-btn.active {
            box-shadow: 0 0 0 2px rgba(0,0,0,0.3);
        }
        
        #validation-stats {
            padding: 10px 15px;
            background: #fff3cd;
            border-bottom: 1px solid #ddd;
            font-size: 12px;
        }
        
        #validation-stats .stat {
            display: inline-block;
            margin-right: 15px;
        }
        
        #export-validations-btn {
            padding: 5px 10px;
            background: #17a2b8;
            color: white;
            border: none;
            border-radius: 3px;
            cursor: pointer;
            font-size: 11px;
            margin-top: 5px;
        }
        
        #export-validations-btn:hover {
            background: #138496;
        }
        
        /* Relationship validation styles */
        .relationship-item {
            padding: 8px;
            margin-bottom: 6px;
            background: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 12px;
        }
        
        .relationship-item.validated-correct {
            background: #d4edda;
            border-color: #28a745;
        }
        
        .relationship-item.validated-incorrect {
            background: #f8d7da;
            border-color: #dc3545;
        }
        
        .relationship-item.added-relationship {
            background: #d4edda;
            border-color: #28a745;
            border-style: dashed;
        }
        
        .rel-validation-btns {
            display: inline-flex;
            gap: 4px;
            margin-left: 8px;
        }
        
        .rel-validation-btn {
            width: 20px;
            height: 20px;
            border: none;
            border-radius: 3px;
            cursor: pointer;
            font-size: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .rel-validation-btn.correct {
            background: #28a745;
            color: white;
        }
        
        .rel-validation-btn.incorrect {
            background: #dc3545;
            color: white;
        }
        
        .rel-validation-btn:hover {
            opacity: 0.8;
        }
        
        .rel-validation-btn.active {
            box-shadow: 0 0 0 2px rgba(0,0,0,0.3);
        }
        
        .rel-delete-btn {
            width: 20px;
            height: 20px;
            border: none;
            border-radius: 3px;
            cursor: pointer;
            font-size: 12px;
            background: #6c757d;
            color: white;
            margin-left: 4px;
        }
        
        .rel-delete-btn:hover {
            background: #5a6268;
        }
        
        .highlight-both-btn {
            width: 22px;
            height: 22px;
            border: 1px solid #ccc;
            border-radius: 3px;
            cursor: pointer;
            font-size: 12px;
            background: #f0f0f0;
            color: #666;
            margin-left: 4px;
            padding: 0;
        }
        
        .highlight-both-btn:hover {
            background: #e0e0e0;
            border-color: #999;
        }
        
        .highlight-both-btn.active {
            background: #ffc107;
            border-color: #ffc107;
            color: #000;
        }
        
        #add-relationship-section {
            padding: 10px;
            background: #f8f9fa;
            border-top: 1px solid #ddd;
            margin-top: 10px;
        }
        
        #add-relationship-section h4 {
            font-size: 12px;
            margin: 0 0 8px 0;
            color: #333;
        }
        
        .add-rel-row {
            display: flex;
            gap: 4px;
            margin-bottom: 6px;
            align-items: center;
        }
        
        .add-rel-select, .add-rel-input {
            padding: 4px 6px;
            font-size: 11px;
            border: 1px solid #ced4da;
            border-radius: 3px;
        }
        
        .add-rel-select {
            flex: 1;
        }
        
        .add-rel-input {
            width: 100px;
        }
        
        .add-rel-btn {
            padding: 4px 10px;
            font-size: 11px;
            background: #28a745;
            color: white;
            border: none;
            border-radius: 3px;
            cursor: pointer;
        }
        
        .add-rel-btn:hover {
            background: #218838;
        }
        
        #rel-validation-stats {
            padding: 8px 10px;
            background: #e7f3ff;
            font-size: 11px;
            border-bottom: 1px solid #ddd;
        }
        
        #rel-validation-stats .stat {
            display: inline-block;
            margin-right: 10px;
        }
        
        /* Additional attribute annotation styles */
        .add-attribute-section {
            margin-top: 8px;
            padding: 8px;
            background: #f8f9fa;
            border-radius: 4px;
            border: 1px dashed #dee2e6;
        }
        
        .add-attribute-section.hidden {
            display: none;
        }
        
        .add-attr-row {
            display: flex;
            gap: 4px;
            margin-bottom: 4px;
        }
        
        .add-attr-input {
            flex: 1;
            padding: 4px 6px;
            font-size: 11px;
            border: 1px solid #ced4da;
            border-radius: 3px;
        }
        
        .add-attr-btn {
            padding: 4px 8px;
            font-size: 11px;
            border: none;
            border-radius: 3px;
            cursor: pointer;
            background: #28a745;
            color: white;
        }
        
        .add-attr-btn:hover {
            background: #218838;
        }
        
        .attribute-tag.annotated-added {
            background: #d4edda;
            border-color: #28a745;
            border-style: dashed;
        }
        
        .attr-delete-btn {
            width: 14px;
            height: 14px;
            border: none;
            border-radius: 2px;
            cursor: pointer;
            font-size: 10px;
            line-height: 14px;
            padding: 0;
            background: #6c757d;
            color: white;
            margin-left: 2px;
        }
        
        .attr-delete-btn:hover {
            background: #5a6268;
        }
        
        .toggle-add-attr-btn {
            font-size: 10px;
            padding: 2px 6px;
            background: #6c757d;
            color: white;
            border: none;
            border-radius: 3px;
            cursor: pointer;
            margin-top: 4px;
        }
        
        .toggle-add-attr-btn:hover {
            background: #5a6268;
        }

        #relationships-content {
            padding: 15px;
            flex: 1;
            overflow-y: auto;
        }

        #relationships-content h3 {
            font-size: 13px;
            margin-bottom: 10px;
            color: #333;
        }

        #annotations-section {
            padding: 15px;
            border-top: 1px solid #ddd;
            background: #f0f8ff;
        }

        #annotations-section h3 {
            font-size: 13px;
            margin-bottom: 10px;
            color: #333;
        }

        .annotation-item {
            padding: 8px;
            margin-bottom: 5px;
            background: white;
            border-left: 3px solid #9c27b0;
            font-size: 11px;
            color: #555;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .annotation-item .delete-btn {
            background: #e57373;
            color: white;
            border: none;
            padding: 2px 8px;
            border-radius: 3px;
            cursor: pointer;
            font-size: 10px;
        }

        .annotation-item .delete-btn:hover {
            background: #ef5350;
        }

        .annotation-pending {
            background: #fff3cd;
            padding: 8px;
            border-left: 3px solid #ffc107;
            font-size: 11px;
            margin-bottom: 10px;
        }

        .relationship-item {
            padding: 8px;
            margin-bottom: 5px;
            background: #f8f9fa;
            border-left: 3px solid #3498db;
            font-size: 12px;
            color: #555;
        }
        
        .relationship-item.in-between-item {
            background: #e8f4fc;
            border-left: 3px solid #17a2b8;
        }

        .relationship-item .rel-name {
            font-weight: bold;
            color: #2c3e50;
        }

        .relationship-item .rel-target {
            color: #3498db;
            cursor: pointer;
            padding: 2px 4px;
            border-radius: 3px;
            transition: all 0.2s;
        }

        .relationship-item .rel-target:hover {
            text-decoration: underline;
            background: #ebf5fb;
        }

        .relationship-item .rel-target.highlighted {
            background: #ffa726;
            color: white;
            font-weight: bold;
            border: 2px solid #ff6f00;
            padding: 2px 6px;
            box-shadow: 0 2px 4px rgba(255, 111, 0, 0.3);
        }

        .candidate-item {
            padding: 10px;
            margin-bottom: 5px;
            background: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            transition: all 0.2s;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .candidate-item:hover {
            border-color: #9c27b0;
            background: #f3e5f5;
            box-shadow: 0 2px 4px rgba(156, 39, 176, 0.2);
        }

        .candidate-item.previewing {
            border-color: #42a5f5;
            border-width: 2px;
            background: #e3f2fd;
            box-shadow: 0 3px 6px rgba(66, 165, 245, 0.4);
        }

        .candidate-info {
            flex: 1;
            cursor: pointer;
        }

        .candidate-item.same-class {
            border-left: 4px solid #4caf50;
        }

        .candidate-item.different-class {
            border-left: 4px solid #ff9800;
        }

        .candidate-item .candidate-label {
            font-weight: bold;
            color: #2c3e50;
            font-size: 12px;
        }

        .candidate-item .candidate-class {
            font-size: 10px;
            color: #7f8c8d;
            margin-top: 3px;
        }

        .candidate-item .candidate-match {
            font-size: 9px;
            margin-top: 3px;
        }

        .candidate-item.same-class .candidate-match {
            color: #4caf50;
        }

        .candidate-item.different-class .candidate-match {
            color: #ff9800;
        }

        .annotate-btn {
            background: #9c27b0;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 11px;
            font-weight: bold;
            transition: all 0.2s;
            white-space: nowrap;
        }

        .annotate-btn:hover {
            background: #7b1fa2;
            box-shadow: 0 2px 4px rgba(156, 39, 176, 0.4);
        }

        .annotate-btn:disabled {
            background: #ccc;
            cursor: not-allowed;
        }

        .remove-btn {
            background: #ff9800;
            color: white;
        }

        .remove-btn:hover {
            background: #f57c00;
            box-shadow: 0 2px 4px rgba(255, 152, 0, 0.4);
        }

        .preview-btn {
            background: #42a5f5;
            color: white;
            border: none;
            padding: 4px 8px;
            border-radius: 3px;
            cursor: pointer;
            font-size: 10px;
            margin-left: 5px;
        }

        .preview-btn:hover {
            background: #1976d2;
        }

        #viewer {
            flex: 1;
            position: relative;
            background: #1a1a1a;
        }

        #viewer canvas {
            display: block;
        }

        #controls {
            position: absolute;
            top: 10px;
            right: 10px;
            background: rgba(255, 255, 255, 0.9);
            padding: 10px;
            border-radius: 4px;
            font-size: 12px;
        }

        #controls label {
            display: block;
            margin-bottom: 5px;
        }

        #controls input[type="checkbox"] {
            margin-right: 5px;
        }
        
        .mode-btn {
            padding: 4px 8px;
            font-size: 10px;
            border: 1px solid #555;
            border-radius: 3px;
            background: #444;
            color: #ccc;
            cursor: pointer;
        }
        
        .mode-btn:hover {
            background: #555;
        }
        
        .mode-btn.active {
            background: #3498db;
            border-color: #3498db;
            color: white;
        }
        
        .mode-btn.active.similarity {
            background: #9c27b0;
            border-color: #9c27b0;
        }
        
        .mode-btn.active.attribute {
            background: #28a745;
            border-color: #28a745;
        }
        
        .mode-btn.active.relationship {
            background: #17a2b8;
            border-color: #17a2b8;
        }

        .loading {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: white;
            font-size: 18px;
        }

        .hidden {
            display: none;
        }

        .info-box {
            padding: 15px;
            margin: 15px;
            background: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 4px;
            font-size: 12px;
            color: #856404;
        }

        #scene-selector-section {
            padding: 15px;
            border-bottom: 1px solid #ddd;
            background: white;
        }

        #scene-selector-section h3 {
            font-size: 14px;
            margin-bottom: 10px;
            color: #333;
        }

        #scenes-list {
            max-height: 200px;
            overflow-y: auto;
        }

        .scene-item {
            padding: 8px;
            margin: 5px 0;
            background: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 12px;
        }

        .scene-item:hover {
            border-color: #3498db;
            background: #ebf5fb;
        }

        .scene-item.selected {
            border-color: #3498db;
            background: #3498db;
            color: white;
        }
    </style>
</head>
<body>
    <div id="left-panel">
        <h2>Scenes</h2>
        
        <div class="info-box">
            <strong>Controls:</strong><br>
            • Left-click: Rotate<br>
            • Right-click: Pan<br>
            • Wheel: Zoom<br>
        </div>

        <div id="scene-selector-section">
            <h3>Available Scenes</h3>
            <div id="scenes-list">
                <!-- Scenes will be populated here -->
            </div>
        </div>
        
        <div id="file-loader" style="display: none;">
            <h3>Load Files</h3>
            <div class="file-input-group">
                <label for="scene-graph-file">Scene Graph JSON:</label>
                <input type="file" id="scene-graph-file" accept=".json">
                <div id="sg-status" class="file-status"></div>
            </div>
            <div class="file-input-group">
                <label for="ply-file">Point Cloud PLY:</label>
                <input type="file" id="ply-file" accept=".ply">
                <div id="ply-status" class="file-status"></div>
            </div>
        </div>
    </div>

    <div id="viewer">
        <div id="loading" class="loading hidden">Loading...</div>
        <div id="controls">
            <label><input type="checkbox" id="show-all-bboxes"> Show All Bounding Boxes</label>
            <label><input type="checkbox" id="show-points" checked> Show Mesh</label>
            <label id="point-size-control" style="display: none;">Point Size: <input type="range" id="point-size" min="0.1" max="30" step="0.1" value="8.0">
                <span id="point-size-value">8.0</span></label>
            <hr style="margin: 10px 0; border-color: #555;">
            <div style="font-size: 12px; margin-bottom: 5px;">Vertical Pan (Z-axis):</div>
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 10px;">
                <input type="range" id="camera-height" min="-20" max="20" step="0.1" value="0" style="flex: 1;">
                <span id="camera-height-value" style="min-width: 45px; font-size: 11px;">0.0</span>
            </div>
            <div style="font-size: 10px; color: #888; margin-bottom: 8px;">Keys: Q (up) / E (down) | Shift for faster</div>
            <hr style="margin: 10px 0; border-color: #555;">
            <div style="font-size: 12px; margin-bottom: 5px;">Annotation Mode:</div>
            <div id="annotation-mode-buttons" style="display: flex; gap: 4px; flex-wrap: wrap;">
                <button class="mode-btn" id="mode-none" onclick="setAnnotationMode(null)">Off</button>
                <button class="mode-btn" id="mode-similarity" onclick="setAnnotationMode('similarity')">Similarity</button>
                <button class="mode-btn" id="mode-attribute" onclick="setAnnotationMode('attribute')">Attribute</button>
                <button class="mode-btn" id="mode-relationship" onclick="setAnnotationMode('relationship')">Relationship</button>
            </div>
            <div id="annotation-info" style="font-size: 11px; color: #ccc; margin-top: 5px; display: none;"></div>
            <div style="margin-top: 5px; display: flex; gap: 5px;">
                <button id="export-annotations" style="padding: 5px 10px;">Export Annotations</button>
                <button id="load-annotations" style="padding: 5px 10px;">Load Annotations</button>
            </div>
            <input type="file" id="annotations-file" accept=".json" style="display: none;">
        </div>
    </div>

    <div id="objects-panel">
        <h2>Objects</h2>
        
        <div id="scene-info">
            <h3>Current Scene</h3>
            <p id="scene-summary">Select a scene to view information</p>
        </div>

        <div id="object-filters">
            <h3>🔍 Filter Objects</h3>
            <div class="filter-section">
                <label for="attribute-filter">By Attribute:</label>
                <select id="attribute-filter">
                    <option value="">All attributes</option>
                </select>
                <div id="selected-attributes" class="filter-chips"></div>
            </div>
            <button id="clear-object-filters" class="clear-filters-btn" style="display: none;">Clear Filters</button>
        </div>

        <div id="validation-stats">
            <span class="stat"><strong>Total:</strong> 0</span>
            <span class="stat" style="color: #28a745;"><strong>Correct:</strong> 0</span>
            <span class="stat" style="color: #dc3545;"><strong>Incorrect:</strong> 0</span>
            <span class="stat"><strong>Remaining:</strong> 0</span>
            <button id="export-validations-btn" onclick="exportAttributeValidations()">Export Validations</button>
        </div>

        <div id="objects-list">
            <div id="objects-container"></div>
        </div>
    </div>

        <div id="relationships-panel">
        <h2 id="relationships-title">Relationships</h2>
        
        <div id="relationship-filters">
            <h3>🔍 Filter Relationships</h3>
            <div class="filter-section">
                <label for="relationship-type-filter">By Type:</label>
                <select id="relationship-type-filter">
                    <option value="">All types</option>
                </select>
                <div id="selected-rel-types" class="filter-chips"></div>
            </div>
            <button id="clear-rel-filters" class="clear-filters-btn" style="display: none;">Clear Filters</button>
        </div>
        
        <div id="relationships-content">
            <div id="relationships-container">Select an object to view its relationships</div>
        </div>

        <div id="annotations-section">
            <h3>Similarity Annotations</h3>
            <div id="annotations-container">No annotations yet</div>
        </div>
    </div>

    <script>
        // Global error handler for debugging
        window.onerror = function(message, source, lineno, colno, error) {
            console.error('JavaScript Error:', { message, source, lineno, colno, error });
            return false;
        };
        
        window.addEventListener('unhandledrejection', function(event) {
            console.error('Unhandled Promise Rejection:', event.reason);
        });
        
        // PLY file parser - handles both ASCII and binary
        async function parsePLY(data) {
            let text, arrayBuffer;
            if (data instanceof ArrayBuffer) {
                arrayBuffer = data;
                // Read entire header as text (up to first \\n\\n after end_header)
                const headerBytes = new Uint8Array(arrayBuffer, 0, Math.min(2000, arrayBuffer.byteLength));
                let headerText = '';
                let endHeaderFound = false;
                for (let i = 0; i < headerBytes.length; i++) {
                    const byte = headerBytes[i];
                    headerText += String.fromCharCode(byte);
                    if (byte === 10) { // newline
                        if (headerText.includes('end_header')) {
                            endHeaderFound = true;
                        }
                        if (endHeaderFound && headerBytes[i+1] === 10) {
                            // Found double newline after end_header, this is the end
                            break;
                        }
                    }
                }
                text = headerText;
            } else {
                text = data;
                arrayBuffer = null;
            }
            
            const lines = text.split('\\n');
            let vertexCount = 0;
            let faceCount = 0;
            let headerEnd = 0;
            let hasColors = false;
            let hasNormals = false;
            let isBinary = false;
            let headerLength = 0;
            
            // Parse header
            let inVertexElement = false;
            let inFaceElement = false;
            let bytesPerVertex = 0;  // Total bytes per vertex (computed from header)
            let colorOffset = -1;  // Offset within vertex where colors start (-1 if no colors)
            let xOffset = 0, yOffset = 4, zOffset = 8;  // Default positions for x, y, z
            let xyzIsDouble = false;  // Whether x, y, z are doubles (8 bytes) or floats (4 bytes)
            let faceExtraBytes = 0;  // Extra bytes per face beyond vertex indices
            for (let i = 0; i < lines.length; i++) {
                const line = lines[i].trim();
                if (line.includes('format binary')) {
                    isBinary = true;
                }
                if (line.startsWith('element vertex')) {
                    vertexCount = parseInt(line.split(' ')[2]);
                    inVertexElement = true;
                    inFaceElement = false;
                    bytesPerVertex = 0;
                }
                if (line.startsWith('element face')) {
                    faceCount = parseInt(line.split(' ')[2]);
                    inVertexElement = false;
                    inFaceElement = true;
                    faceExtraBytes = 0;
                }
                if (line.startsWith('element') && !line.startsWith('element vertex') && !line.startsWith('element face')) {
                    // Some other element (e.g., edge)
                    inVertexElement = false;
                    inFaceElement = false;
                }
                if (inVertexElement && line.startsWith('property')) {
                    // Count bytes for ALL vertex properties and track positions
                    if (line.includes('property uchar red')) {
                        colorOffset = bytesPerVertex;  // Mark where colors start
                        hasColors = true;
                    }
                    // Track x, y, z property positions and data type
                    if (line.includes('property double x')) {
                        xOffset = bytesPerVertex;
                        xyzIsDouble = true;
                    } else if (line.includes('property float x')) {
                        xOffset = bytesPerVertex;
                    }
                    if (line.includes('property double y') || line.includes('property float y')) {
                        yOffset = bytesPerVertex;
                    }
                    if (line.includes('property double z') || line.includes('property float z')) {
                        zOffset = bytesPerVertex;
                    }
                    if (line.includes('uchar') || line.includes('char')) bytesPerVertex += 1;
                    else if (line.includes('ushort') || line.includes('short')) bytesPerVertex += 2;
                    else if (line.includes('uint') || line.includes('int') || line.includes('float')) bytesPerVertex += 4;
                    else if (line.includes('double')) bytesPerVertex += 8;
                }
                if (inFaceElement && line.startsWith('property')) {
                    // Count bytes for face properties beyond vertex_indices
                    if (!line.includes('vertex_indices')) {
                        if (line.includes('uchar')) faceExtraBytes += 1;
                        else if (line.includes('ushort') || line.includes('short')) faceExtraBytes += 2;
                        else if (line.includes('uint') || line.includes('int') || line.includes('float')) faceExtraBytes += 4;
                        else if (line.includes('double')) faceExtraBytes += 8;
                    }
                }
                if (line.includes('property float nx') || line.includes('property float ny') || line.includes('property float nz')) {
                    hasNormals = true;
                }
                if (line.includes('property uchar red') || line.includes('property uchar green') || line.includes('property uchar blue')) {
                    hasColors = true;
                }
                if (line === 'end_header') {
                    headerEnd = i + 1;
                    // Calculate header length in bytes - find the byte position after end_header\\n
                    if (arrayBuffer) {
                        // Search for "end_header" followed by newline in the raw bytes
                        const headerBytes = new Uint8Array(arrayBuffer, 0, Math.min(2000, arrayBuffer.byteLength));
                        let foundEnd = false;
                        for (let j = 0; j < headerBytes.length - 10; j++) {
                            let match = true;
                            const endHeaderStr = 'end_header';
                            for (let k = 0; k < endHeaderStr.length; k++) {
                                if (headerBytes[j + k] !== endHeaderStr.charCodeAt(k)) {
                                    match = false;
                                    break;
                                }
                            }
                            if (match && headerBytes[j + endHeaderStr.length] === 10) {
                                // Found "end_header\\n", header ends at j + endHeaderStr.length + 1
                                headerLength = j + endHeaderStr.length + 1;
                                foundEnd = true;
                                break;
                            }
                        }
                        if (!foundEnd) {
                            // Fallback: calculate from text
                            const headerTextUpToEnd = lines.slice(0, i + 1).join('\\n') + '\\n';
                            headerLength = new TextEncoder().encode(headerTextUpToEnd).length;
                        }
                    }
                    break;
                }
            }
            
            if (isBinary && arrayBuffer) {
                // If bytesPerVertex wasn't computed (e.g., empty or bad header), fall back to estimate
                if (bytesPerVertex === 0) {
                    bytesPerVertex = 12; // x, y, z minimum
                    if (hasNormals) bytesPerVertex += 12;
                    if (hasColors) bytesPerVertex += 4;
                    colorOffset = hasNormals ? 24 : 12;
                    xOffset = 0; yOffset = 4; zOffset = 8;
                }
                console.log('PLY Header parsed: bytesPerVertex=' + bytesPerVertex + ', x/y/z offsets=' + xOffset + '/' + yOffset + '/' + zOffset + ', xyzIsDouble=' + xyzIsDouble + ', colorOffset=' + colorOffset);
                return parseBinaryPLY(arrayBuffer, headerLength, vertexCount, faceCount, hasColors, bytesPerVertex, colorOffset, xOffset, yOffset, zOffset, xyzIsDouble, faceExtraBytes);
            } else {
                // For ASCII PLY, we need the full text content, not just the header
                let fullText = text;
                if (arrayBuffer) {
                    // Decode the entire ArrayBuffer as text for ASCII PLY
                    const decoder = new TextDecoder('utf-8');
                    fullText = decoder.decode(arrayBuffer);
                }
                return parseASCIIPLY(fullText, headerEnd, vertexCount, faceCount, hasColors, hasNormals);
            }
        }
        
        // Convert sRGB color value to linear space for proper rendering
        function sRGBToLinear(c) {
            return c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
        }
        
        function parseASCIIPLY(text, headerEnd, vertexCount, faceCount, hasColors) {
            const lines = text.split('\\n');
            const points = [];
            const colors = [];
            const indices = [];
            
            // Parse vertices
            const dataLines = lines.slice(headerEnd, headerEnd + vertexCount);
            dataLines.forEach(line => {
                if (!line.trim()) return;
                const parts = line.trim().split(/\\s+/);
                if (parts.length >= 3) {
                    let x = parseFloat(parts[0]);
                    let y = parseFloat(parts[1]);
                    let z = parseFloat(parts[2]);
                    // Replace NaN or invalid values with 0
                    if (isNaN(x) || !isFinite(x)) x = 0;
                    if (isNaN(y) || !isFinite(y)) y = 0;
                    if (isNaN(z) || !isFinite(z)) z = 0;
                    points.push(x, y, z);
                    
                    if (hasColors && parts.length >= 6) {
                        // Convert from sRGB to linear space for correct rendering
                        const r = parseInt(parts[3]) / 255;
                        const g = parseInt(parts[4]) / 255;
                        const b = parseInt(parts[5]) / 255;
                        colors.push(
                            sRGBToLinear(r),
                            sRGBToLinear(g),
                            sRGBToLinear(b)
                        );
                    }
                }
            });
            
            // Parse faces
            if (faceCount > 0) {
                const faceStart = headerEnd + vertexCount;
                const faceLines = lines.slice(faceStart, faceStart + faceCount);
                const maxVertex = (points.length / 3) - 1;
                faceLines.forEach(line => {
                    if (!line.trim()) return;
                    const parts = line.trim().split(/\\s+/);
                    const numVerts = parseInt(parts[0]);
                    if (numVerts === 3 && parts.length >= 4) {
                        // Triangle - validate indices
                        const v0 = parseInt(parts[1]);
                        const v1 = parseInt(parts[2]);
                        const v2 = parseInt(parts[3]);
                        if (v0 >= 0 && v0 <= maxVertex && v1 >= 0 && v1 <= maxVertex && v2 >= 0 && v2 <= maxVertex) {
                            indices.push(v0, v1, v2);
                        }
                    }
                });
            }
            
            return { points, colors, indices, hasColors: hasColors && colors.length > 0, hasFaces: faceCount > 0 };
        }
        
        function parseBinaryPLY(arrayBuffer, headerLength, vertexCount, faceCount, hasColors, bytesPerVertex, colorOffset, xOffset, yOffset, zOffset, xyzIsDouble, faceExtraBytes = 0) {
            console.log('Parsing binary PLY: headerLength=', headerLength, 'vertexCount=', vertexCount, 'faceCount=', faceCount, 'hasColors=', hasColors, 'bytesPerVertex=', bytesPerVertex, 'colorOffset=', colorOffset, 'xyzOffsets=', xOffset, yOffset, zOffset, 'xyzIsDouble=', xyzIsDouble, 'faceExtraBytes=', faceExtraBytes);
            const view = new DataView(arrayBuffer, headerLength);
            const points = [];
            const colors = [];
            const indices = [];
            let offset = 0;
            
            console.log('Total binary data size:', view.byteLength, 'Expected vertex data size:', vertexCount * bytesPerVertex);
            
            try {
                // Parse all vertices
                for (let i = 0; i < vertexCount; i++) {
                    if (offset + bytesPerVertex > view.byteLength) {
                        console.warn('Reached end of buffer at vertex', i);
                        break;
                    }
                    
                    // Read x, y, z from their actual positions (as double or float)
                    let x, y, z;
                    if (xyzIsDouble) {
                        x = view.getFloat64(offset + xOffset, true);
                        y = view.getFloat64(offset + yOffset, true);
                        z = view.getFloat64(offset + zOffset, true);
                    } else {
                        x = view.getFloat32(offset + xOffset, true);
                        y = view.getFloat32(offset + yOffset, true);
                        z = view.getFloat32(offset + zOffset, true);
                    }
                    
                    // Replace NaN with 0 (will be excluded from bounding box calculation)
                    if (isNaN(x) || !isFinite(x)) x = 0;
                    if (isNaN(y) || !isFinite(y)) y = 0;
                    if (isNaN(z) || !isFinite(z)) z = 0;
                    
                    points.push(x, y, z);
                    
                    if (hasColors && colorOffset >= 0 && offset + colorOffset + 4 <= view.byteLength) {
                        const r = view.getUint8(offset + colorOffset) / 255;
                        const g = view.getUint8(offset + colorOffset + 1) / 255;
                        const b = view.getUint8(offset + colorOffset + 2) / 255;
                        // Skip alpha at colorOffset + 3
                        // Convert from sRGB to linear space for correct rendering
                        colors.push(sRGBToLinear(r), sRGBToLinear(g), sRGBToLinear(b));
                    }
                    
                    offset += bytesPerVertex;
                }
                
                const actualVertexCount = points.length / 3;
                console.log('Parsed', actualVertexCount, 'vertices from binary PLY');
                console.log('Offset after vertices:', offset, '/', view.byteLength, 'bytes');
                console.log('Remaining bytes for faces:', view.byteLength - offset);
                console.log('Expected to parse', faceCount, 'faces');
                
                // Debug: show first few vertices to help diagnose data issues
                console.log('First 5 vertices:');
                for (let i = 0; i < Math.min(5, actualVertexCount); i++) {
                    console.log('  v' + i + ':', points[i*3].toFixed(4), points[i*3+1].toFixed(4), points[i*3+2].toFixed(4));
                }
                // Show some stats about coordinate ranges
                let validCount = 0, invalidCount = 0;
                let sampleInvalid = [];
                for (let i = 0; i < points.length; i += 3) {
                    const x = points[i], y = points[i+1], z = points[i+2];
                    if (Math.abs(x) < 100 && Math.abs(y) < 100 && Math.abs(z) < 100 && !(x === 0 && y === 0 && z === 0)) {
                        validCount++;
                    } else {
                        invalidCount++;
                        if (sampleInvalid.length < 3) sampleInvalid.push({i: i/3, x, y, z});
                    }
                }
                console.log('Coordinate check: valid=' + validCount + ', invalid=' + invalidCount);
                if (sampleInvalid.length > 0) console.log('Sample invalid vertices:', sampleInvalid);
                
                // Parse faces
                if (faceCount > 0) {
                    let invalidFaceCount = 0;
                    let facesProcessed = 0;
                    for (let i = 0; i < faceCount; i++) {
                        facesProcessed++;
                        if (offset + 1 > view.byteLength) {
                            console.warn('Ran out of buffer at face', i, 'offset:', offset, 'byteLength:', view.byteLength);
                            break;
                        }
                        
                        // Read number of vertices in face (uchar)
                        const numVerts = view.getUint8(offset);
                        offset += 1;
                        
                        if (numVerts === 3 && offset + 12 + faceExtraBytes <= view.byteLength) {
                            // Triangle - read 3 vertex indices as int32 (little endian)
                            const v0 = view.getInt32(offset, true);
                            const v1 = view.getInt32(offset + 4, true);
                            const v2 = view.getInt32(offset + 8, true);
                            const maxVertex = actualVertexCount - 1;
                            // Only add valid indices within vertex range
                            if (v0 >= 0 && v0 <= maxVertex && v1 >= 0 && v1 <= maxVertex && v2 >= 0 && v2 <= maxVertex) {
                                // Check if any vertex is at origin (likely a replaced NaN)
                                const v0IsOrigin = points[v0*3] === 0 && points[v0*3+1] === 0 && points[v0*3+2] === 0;
                                const v1IsOrigin = points[v1*3] === 0 && points[v1*3+1] === 0 && points[v1*3+2] === 0;
                                const v2IsOrigin = points[v2*3] === 0 && points[v2*3+1] === 0 && points[v2*3+2] === 0;
                                
                                // Skip triangles with vertices at origin
                                if (!v0IsOrigin && !v1IsOrigin && !v2IsOrigin) {
                                    indices.push(v0, v1, v2);
                                } else {
                                    invalidFaceCount++;
                                }
                            } else {
                                invalidFaceCount++;
                            }
                            offset += 12 + faceExtraBytes;  // Skip vertex indices and extra properties
                        } else {
                            // Skip other face types (quads, etc.) or invalid data
                            if (numVerts > 0 && numVerts < 10) {
                                offset += numVerts * 4 + faceExtraBytes;  // Skip vertex indices and extra properties
                            } else {
                                console.warn('Invalid face vertex count:', numVerts, 'at face', i, 'offset:', offset);
                                break;
                            }
                            if (offset > view.byteLength) {
                                console.warn('Offset exceeded after skipping non-triangle face');
                                break;
                            }
                        }
                    }
                    console.log('Parsed', indices.length / 3, 'valid faces from binary PLY');
                    console.log('Processed', facesProcessed, '/', faceCount, 'faces, skipped', invalidFaceCount, 'invalid');
                }
                
                return { points, colors, indices, hasColors: hasColors && colors.length > 0, hasFaces: faceCount > 0 };
            } catch (error) {
                console.error('Error parsing binary PLY:', error, 'at offset', offset);
                throw error;
            }
        }

        // Convert multiscan annotations format to scene graph format
        function convertMultiscanToSceneGraph(data) {
            const sceneId = data.scanId || 'unknown';
            const objects = [];
            
            // Convert multiscan objects to scene graph objects
            for (const obj of (data.objects || [])) {
                const objId = obj.objectId;
                const label = obj.label || 'unknown';
                const obb = obj.obb || {};
                
                // Extract OBB parameters
                const centroid = obb.centroid || [0, 0, 0];
                const axesLengths = obb.axesLengths || [1, 1, 1];
                const normalizedAxes = obb.normalizedAxes || [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1];
                
                // normalizedAxes can be either:
                // - 9 elements: 3x3 rotation matrix [m00,m01,m02, m10,m11,m12, m20,m21,m22] (row-major)
                // - 16 elements: 4x4 matrix [m00,m01,m02,m03, m10,m11,m12,m13, m20,m21,m22,m23, m30,m31,m32,m33]
                let m00, m01, m02, m10, m11, m12, m20, m21, m22;
                if (normalizedAxes.length === 9) {
                    // 3x3 matrix (row-major)
                    m00 = normalizedAxes[0]; m01 = normalizedAxes[1]; m02 = normalizedAxes[2];
                    m10 = normalizedAxes[3]; m11 = normalizedAxes[4]; m12 = normalizedAxes[5];
                    m20 = normalizedAxes[6]; m21 = normalizedAxes[7]; m22 = normalizedAxes[8];
                } else {
                    // 4x4 matrix - extract 3x3 rotation part
                    m00 = normalizedAxes[0]; m01 = normalizedAxes[1]; m02 = normalizedAxes[2];
                    m10 = normalizedAxes[4]; m11 = normalizedAxes[5]; m12 = normalizedAxes[6];
                    m20 = normalizedAxes[8]; m21 = normalizedAxes[9]; m22 = normalizedAxes[10];
                }
                
                // Convert rotation matrix to quaternion
                // First validate that matrix values are finite
                const matrixValid = [m00, m01, m02, m10, m11, m12, m20, m21, m22].every(v => isFinite(v));
                let qw = 1, qx = 0, qy = 0, qz = 0;  // Default to identity quaternion
                
                if (matrixValid) {
                    const trace = m00 + m11 + m22;
                    
                    if (trace > 0) {
                        const s = 0.5 / Math.sqrt(trace + 1.0);
                        qw = 0.25 / s;
                        qx = (m21 - m12) * s;
                        qy = (m02 - m20) * s;
                        qz = (m10 - m01) * s;
                    } else if (m00 > m11 && m00 > m22) {
                        const s = 2.0 * Math.sqrt(1.0 + m00 - m11 - m22);
                        qw = (m21 - m12) / s;
                        qx = 0.25 * s;
                        qy = (m01 + m10) / s;
                        qz = (m02 + m20) / s;
                    } else if (m11 > m22) {
                        const s = 2.0 * Math.sqrt(1.0 + m11 - m00 - m22);
                        qw = (m02 - m20) / s;
                        qx = (m01 + m10) / s;
                        qy = 0.25 * s;
                        qz = (m12 + m21) / s;
                    } else {
                        const s = 2.0 * Math.sqrt(1.0 + m22 - m00 - m11);
                        qw = (m10 - m01) / s;
                        qx = (m02 + m20) / s;
                        qy = (m12 + m21) / s;
                        qz = 0.25 * s;
                    }
                    
                    // Validate quaternion result
                    if (!isFinite(qx) || !isFinite(qy) || !isFinite(qz) || !isFinite(qw)) {
                        qw = 1; qx = 0; qy = 0; qz = 0;  // Fallback to identity
                    }
                }
                
                const rotation = [qx, qy, qz, qw];  // [qx, qy, qz, qw]
                
                // Half dimensions (multiscan uses full lengths)
                const halfDims = axesLengths.map(d => d / 2);
                
                objects.push({
                    id: objId,
                    labels: [label],
                    bbox: {
                        center: centroid,
                        half_dims: halfDims,
                        rotation: rotation
                    },
                    mobilityType: obj.mobilityType || 'unknown',
                    partIds: obj.partIds || []
                });
            }
            
            // Build attributes from object properties
            const attributes = {};
            for (const obj of objects) {
                const objAttrs = [];
                if (obj.mobilityType && obj.mobilityType !== 'unknown') {
                    objAttrs.push(obj.mobilityType);  // 'fixed' or 'movable'
                }
                if (objAttrs.length > 0) {
                    attributes[obj.id] = objAttrs;
                }
            }
            
            // Build relationships from parts hierarchy
            const relationships = [];
            const parts = data.parts || [];
            
            // Create a map from partId to objectId
            const partToObject = {};
            for (const obj of objects) {
                for (const partId of (obj.partIds || [])) {
                    partToObject[partId] = obj.id;
                }
            }
            
            // Create part-of relationships based on parentId
            for (const part of parts) {
                if (part.parentId !== undefined) {
                    const childObjId = partToObject[part.partId];
                    const parentObjId = partToObject[part.parentId];
                    
                    if (childObjId !== undefined && parentObjId !== undefined && childObjId !== parentObjId) {
                        relationships.push({
                            subject: childObjId,
                            predicate: 'part of',
                            object: parentObjId
                        });
                    }
                }
                
                // Add articulation info as relationships
                if (part.articulations && part.articulations.length > 0) {
                    const objId = partToObject[part.partId];
                    if (objId !== undefined) {
                        for (const art of part.articulations) {
                            if (art.type === 'rotation') {
                                // Object can rotate (e.g., door, drawer)
                                if (!attributes[objId]) attributes[objId] = [];
                                if (!attributes[objId].includes('rotatable')) {
                                    attributes[objId].push('rotatable');
                                }
                            } else if (art.type === 'translation') {
                                // Object can slide (e.g., drawer)
                                if (!attributes[objId]) attributes[objId] = [];
                                if (!attributes[objId].includes('slidable')) {
                                    attributes[objId].push('slidable');
                                }
                            }
                        }
                    }
                }
            }
            
            // Infer spatial relationships based on bounding box positions
            for (let i = 0; i < objects.length; i++) {
                for (let j = i + 1; j < objects.length; j++) {
                    const obj1 = objects[i];
                    const obj2 = objects[j];
                    
                    const c1 = obj1.bbox.center;
                    const c2 = obj2.bbox.center;
                    const h1 = obj1.bbox.half_dims;
                    const h2 = obj2.bbox.half_dims;
                    
                    // Check vertical relationships (Y is up in this coordinate system)
                    const verticalDist = c1[1] - c2[1];
                    const horizontalDist = Math.sqrt(Math.pow(c1[0] - c2[0], 2) + Math.pow(c1[2] - c2[2], 2));
                    
                    // If objects are vertically close and one is above the other
                    if (horizontalDist < Math.max(h1[0] + h2[0], h1[2] + h2[2])) {
                        const verticalOverlap = (h1[1] + h2[1]) - Math.abs(verticalDist);
                        if (verticalOverlap < 0.1 && Math.abs(verticalDist) < 0.5) {
                            // Objects are close vertically
                            if (verticalDist > 0.05) {
                                relationships.push({
                                    subject: obj1.id,
                                    predicate: 'on top of',
                                    object: obj2.id
                                });
                            } else if (verticalDist < -0.05) {
                                relationships.push({
                                    subject: obj2.id,
                                    predicate: 'on top of',
                                    object: obj1.id
                                });
                            }
                        }
                    }
                }
            }
            
            console.log('Converted multiscan to scene graph:', objects.length, 'objects,', relationships.length, 'relationships,', Object.keys(attributes).length, 'objects with attributes');
            
            // Create scene graph structure
            return {
                id: sceneId,
                objects: objects,
                relationships: relationships,
                attributes: attributes
            };
        }

        // Global variables
        let scene, camera, renderer, pointCloud, bboxes = [];
        let selectedObjectId = null;
        let highlightedObjectIds = new Map(); // Map of objectId -> color for highlighted related objects
        let sceneGraphData = null;
        let availableScenes = []; // All scenes from both datasets
        let allPredicates = []; // All unique predicates from all scene graphs
        let currentSceneId = null;
        let currentDataset = 'scannet'; // 'scannet', 'multiscan', or '3rscan'
        
        // Helper function to escape HTML special characters
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        // Detect dataset from scene ID pattern
        function getDatasetFromSceneId(sceneId) {
            // MultiScan scenes use underscore after "scene": scene_00000_00
            // ScanNet scenes don't: scene0000_00
            // 3RScan scenes use UUIDs: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
            if (sceneId.startsWith('scene_')) {
                return 'multiscan';
            } else if (sceneId.startsWith('scene')) {
                return 'scannet';
            } else {
                // UUID pattern for 3RScan
                return '3rscan';
            }
        }
        let showAllBboxes = false;
        let relationshipLines = []; // Lines connecting related objects
        
        // Annotation mode: null, 'similarity', 'attribute', 'relationship'
        let annotationMode = null;
        let annotationFirstObject = null;
        let similarityAnnotations = []; // Array of {id1, id2, label1, label2, timestamp}
        let annotationLines = [];
        let previewedCandidateId = null;
        
        // Attribute validation
        let attributeValidations = {}; // Map of attribute_id -> 'correct' | 'incorrect' | null
        
        // Added attribute annotations
        let additionalAttributes = []; // Array of {id, object_id, name, timestamp}
        
        // Relationship validation
        let relationshipValidations = {}; // Map of relationship index -> 'correct' | 'incorrect' | null
        
        // Added relationship annotations
        let additionalRelationships = []; // Array of {id, subject_id, object_id, predicate, timestamp}
        
        // Color palette for highlighted objects
        const highlightColors = [
            { hex: 0xffa726, css: '#ffa726', border: '#ff6f00', name: 'orange' },
            { hex: 0x42a5f5, css: '#42a5f5', border: '#1976d2', name: 'blue' },
            { hex: 0xec407a, css: '#ec407a', border: '#c2185b', name: 'pink' },
            { hex: 0xab47bc, css: '#ab47bc', border: '#7b1fa2', name: 'purple' },
            { hex: 0x26a69a, css: '#26a69a', border: '#00796b', name: 'teal' },
            { hex: 0xffca28, css: '#ffca28', border: '#f57f17', name: 'yellow' },
            { hex: 0x66bb6a, css: '#66bb6a', border: '#388e3c', name: 'green' },
            { hex: 0xff7043, css: '#ff7043', border: '#d84315', name: 'deep-orange' }
        ];
        let nextColorIndex = 0;
        
        // Filters
        let selectedAttributeFilters = new Set();
        let selectedRelTypeFilters = new Set();

        // Initialize Three.js
        function initViewer() {
            const container = document.getElementById('viewer');
            const width = container.clientWidth;
            const height = container.clientHeight;

            scene = new THREE.Scene();
            scene.background = new THREE.Color(0x1a1a1a);

            // Basic lighting for textured meshes (OBJ/MTL materials need lights)
            const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
            scene.add(ambientLight);
            const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
            dirLight.position.set(5, 10, 7);
            scene.add(dirLight);
            const fillLight = new THREE.DirectionalLight(0xffffff, 0.5);
            fillLight.position.set(-5, -6, -4);
            scene.add(fillLight);

            camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
            camera.position.set(5, 5, 5);
            camera.up.set(0, 0, 1);  // Set Z-up coordinate system for proper rotation
            camera.lookAt(0, 0, 0);

            renderer = new THREE.WebGLRenderer({ antialias: true });
            renderer.setSize(width, height);
            renderer.outputEncoding = THREE.sRGBEncoding;
            container.appendChild(renderer.domElement);

            // Add OrbitControls
            controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;
            controls.screenSpacePanning = false;
            controls.minDistance = 0.1;
            controls.maxDistance = 1000;
            // No maxPolarAngle constraint - allow free rotation around all axes

            // Handle window resize
            window.addEventListener('resize', () => {
                const width = container.clientWidth;
                const height = container.clientHeight;
                camera.aspect = width / height;
                camera.updateProjectionMatrix();
                renderer.setSize(width, height);
            });

            // Camera height control with slider - implements vertical pan
            const cameraHeightSlider = document.getElementById('camera-height');
            const cameraHeightValue = document.getElementById('camera-height-value');
            let verticalOffset = 0;
            let initialCameraZ = 0;
            let initialTargetZ = 0;
            
            function updateCameraHeight(deltaZ) {
                // Move both camera and target vertically (vertical pan)
                verticalOffset += deltaZ;
                camera.position.z = initialCameraZ + verticalOffset;
                controls.target.z = initialTargetZ + verticalOffset;
                controls.update();
                
                cameraHeightSlider.value = verticalOffset;
                cameraHeightValue.textContent = verticalOffset.toFixed(1);
            }
            
            cameraHeightSlider.addEventListener('input', (e) => {
                const offset = parseFloat(e.target.value);
                const deltaZ = offset - verticalOffset;
                updateCameraHeight(deltaZ);
            });
            
            // Keyboard controls for vertical camera movement (Q = up, E = down)
            window.addEventListener('keydown', (e) => {
                // Don't interfere with text input
                if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') {
                    return;
                }
                
                const heightStep = e.shiftKey ? 0.3 : 0.1; // Fine control
                
                if (e.key === 'q' || e.key === 'Q') {
                    updateCameraHeight(heightStep);
                    e.preventDefault();
                } else if (e.key === 'e' || e.key === 'E') {
                    updateCameraHeight(-heightStep);
                    e.preventDefault();
                }
            });

            animate();
        }

        function animate() {
            requestAnimationFrame(animate);
            if (controls) {
                controls.update();
            }
            renderer.render(scene, camera);
        }

        // Load scene graph JSON
        document.getElementById('scene-graph-file').addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file) return;

            const status = document.getElementById('sg-status');
            status.textContent = 'Loading...';
            status.className = 'file-status';

            try {
                const text = await file.text();
                sceneGraphData = JSON.parse(text);
                status.textContent = `Loaded: ${file.name}`;
                status.className = 'file-status loaded';
                
                // Clear filters when loading new scene
                selectedAttributeFilters.clear();
                selectedRelTypeFilters.clear();
                updateAttributeFilterChips();
                updateRelTypeFilterChips();
                document.getElementById('clear-object-filters').style.display = 'none';
                document.getElementById('clear-rel-filters').style.display = 'none';
                
                initializeFilters();
                updateSceneInfo();
                loadBoundingBoxes();
                updateObjectsList();
                
                // Clear all validations and annotations for new scene
                attributeValidations = {};
                additionalAttributes = [];
                relationshipValidations = {};
                additionalRelationships = [];
                updateValidationStats();
                
                // Try to load point cloud if already loaded
                const plyFile = document.getElementById('ply-file').files[0];
                if (plyFile) {
                    loadPointCloudFile(plyFile);
                }
            } catch (error) {
                status.textContent = `Error: ${error.message}`;
                status.className = 'file-status';
                console.error('Error loading scene graph:', error);
            }
        });

        // Load PLY file
        document.getElementById('ply-file').addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file) return;

            const status = document.getElementById('ply-status');
            status.textContent = 'Loading...';
            status.className = 'file-status';

            try {
                await loadPointCloudFile(file);
                status.textContent = `Loaded: ${file.name}`;
                status.className = 'file-status loaded';
            } catch (error) {
                status.textContent = `Error: ${error.message}`;
                status.className = 'file-status';
                console.error('Error loading PLY:', error);
            }
        });

        function disposeObject(object) {
            if (!object) return;
            object.traverse(child => {
                if (child.geometry) {
                    child.geometry.dispose();
                }
                if (child.material) {
                    if (Array.isArray(child.material)) {
                        child.material.forEach(m => m && m.dispose && m.dispose());
                    } else if (child.material.dispose) {
                        child.material.dispose();
                    }
                }
                if (child.texture && child.texture.dispose) {
                    child.texture.dispose();
                }
            });
        }

        async function loadTexturedMesh(candidate) {
            // candidate: { obj, mtl }
            const resourcePath = candidate.obj.substring(0, candidate.obj.lastIndexOf('/') + 1);
            console.log('Attempting textured mesh load:', candidate.obj);

            // Remove existing geometry
            if (pointCloud) {
                scene.remove(pointCloud);
                disposeObject(pointCloud);
            }

            let materials = null;
            if (candidate.mtl) {
                const mtlLoader = new THREE.MTLLoader();
                mtlLoader.setResourcePath(resourcePath);
                mtlLoader.setPath(resourcePath);
                materials = await new Promise((resolve, reject) => {
                    mtlLoader.load(candidate.mtl.replace(resourcePath, ''), resolve, undefined, reject);
                });
                materials.preload();
            }

            const objLoader = new THREE.OBJLoader();
            if (materials) objLoader.setMaterials(materials);
            objLoader.setPath(resourcePath);
            objLoader.setResourcePath(resourcePath); // for texture lookups referenced in OBJ/MTL
            const object = await new Promise((resolve, reject) => {
                objLoader.load(candidate.obj.replace(resourcePath, ''), resolve, undefined, reject);
            });

            pointCloud = object;

            // Ensure materials render in current lighting and show both sides
            pointCloud.traverse(node => {
                if (node.isMesh) {
                    if (node.material) {
                        const mats = Array.isArray(node.material) ? node.material : [node.material];
                        mats.forEach(m => {
                            if (!m) return;
                            m.side = THREE.DoubleSide;
                            if ('map' in m && m.map) {
                                m.map.encoding = THREE.sRGBEncoding;
                            } else if (!m.color || (m.color.r === 0 && m.color.g === 0 && m.color.b === 0)) {
                                // Default to a mid-gray if no texture/color
                                m.color = new THREE.Color(0x888888);
                            }
                            m.needsUpdate = true;
                        });
                    } else {
                        node.material = new THREE.MeshStandardMaterial({ color: 0x888888, side: THREE.DoubleSide });
                    }
                }
            });

            // Hide point size control for mesh
            const pointSizeControl = document.getElementById('point-size-control');
            if (pointSizeControl) pointSizeControl.style.display = 'none';

            // Ensure the visibility toggle stays in sync
            const showPointsCheckbox = document.getElementById('show-points');
            if (showPointsCheckbox) showPointsCheckbox.checked = true;

            scene.add(pointCloud);
            console.log('Textured mesh added to scene from', candidate.obj);
        }

        async function loadPointCloudFile(file) {
            document.getElementById('loading').classList.remove('hidden');
            
            try {
                const arrayBuffer = await file.arrayBuffer();
                const pcData = await parsePLY(arrayBuffer);
                
                // Sample if too many points (only if no faces, as sampling would break face indices)
                if (!pcData.hasFaces) {
                    const maxPoints = 200000;
                    const numVertices = pcData.points.length / 3;
                    if (numVertices > maxPoints) {
                        console.log('Sampling point cloud from', numVertices, 'to', maxPoints, 'points');
                        const step = Math.floor(numVertices / maxPoints);
                        const sampledPoints = [];
                        const sampledColors = [];
                        for (let v = 0; v < numVertices; v += step) {
                            const idx = v * 3;
                            sampledPoints.push(pcData.points[idx], pcData.points[idx+1], pcData.points[idx+2]);
                            if (pcData.hasColors && pcData.colors) {
                                const colorIdx = v * 3;
                                sampledColors.push(pcData.colors[colorIdx], pcData.colors[colorIdx+1], pcData.colors[colorIdx+2]);
                            }
                        }
                        pcData.points = sampledPoints;
                        pcData.colors = sampledColors;
                        console.log('Sampled to', sampledPoints.length / 3, 'points');
                    }
                }
                
                loadPointCloud(pcData);
            } finally {
                document.getElementById('loading').classList.add('hidden');
            }
        }

        function loadPointCloud(data) {
            // Remove existing point cloud/mesh
            if (pointCloud) {
                scene.remove(pointCloud);
                disposeObject(pointCloud);
            }

            const points = data.points;
            console.log('Loading 3D model with', points.length / 3, 'vertices, hasFaces:', data.hasFaces);
            
            if (!points || points.length === 0) {
                console.error('No points data provided');
                return;
            }

            // Validate positions - check for NaN and replace with 0
            for (let i = 0; i < points.length; i++) {
                if (isNaN(points[i]) || !isFinite(points[i])) {
                    points[i] = 0;
                }
            }
            
            const geometry = new THREE.BufferGeometry();
            geometry.setAttribute('position', new THREE.Float32BufferAttribute(points, 3));

            let material;
            
            // Use mesh if faces are available, otherwise use points
            if (data.hasFaces && data.indices && data.indices.length > 0) {
                console.log('Rendering as mesh with', data.indices.length / 3, 'faces');
                // Validate indices are within vertex range
                const maxIndex = (points.length / 3) - 1;
                const validIndices = [];
                for (let i = 0; i < data.indices.length; i++) {
                    const idx = data.indices[i];
                    if (idx >= 0 && idx <= maxIndex) {
                        validIndices.push(idx);
                    }
                }
                if (validIndices.length > 0) {
                    geometry.setIndex(validIndices);
                    geometry.computeVertexNormals();
                } else {
                    console.warn('No valid face indices found, rendering as point cloud instead');
                    data.hasFaces = false;
                }
                
                if (data.hasColors && data.colors && data.colors.length > 0) {
                    console.log('Using colored mesh, color count:', data.colors.length);
                    geometry.setAttribute('color', new THREE.Float32BufferAttribute(data.colors, 3));
                    material = new THREE.MeshBasicMaterial({ 
                        vertexColors: true,
                        side: THREE.DoubleSide
                    });
                } else {
                    console.log('Using grayscale mesh');
                    material = new THREE.MeshBasicMaterial({ 
                        color: 0x888888,
                        side: THREE.DoubleSide
                    });
                }
                
                pointCloud = new THREE.Mesh(geometry, material);
                // Hide point size control for mesh
                const pointSizeControl = document.getElementById('point-size-control');
                if (pointSizeControl) pointSizeControl.style.display = 'none';
                // Update label
                const showPointsLabel = document.querySelector('label[for="show-points"]');
                if (showPointsLabel) showPointsLabel.innerHTML = '<input type="checkbox" id="show-points" checked> Show Mesh';
            } else {
                console.log('Rendering as point cloud (no faces)');
                // Show point size control for point cloud
                const pointSizeControl = document.getElementById('point-size-control');
                if (pointSizeControl) pointSizeControl.style.display = 'block';
                // Update label
                const showPointsLabel = document.querySelector('label[for="show-points"]');
                if (showPointsLabel) showPointsLabel.innerHTML = '<input type="checkbox" id="show-points" checked> Show Point Cloud';
                // Use reasonable point size - larger for better visibility
                const pointSize = 8.0; // Larger size for better visibility with attenuation
                if (data.hasColors && data.colors && data.colors.length > 0) {
                    console.log('Using colored point cloud, color count:', data.colors.length);
                    // Colors are already in 0-1 range from PLY parser
                    geometry.setAttribute('color', new THREE.Float32BufferAttribute(data.colors, 3));
                    material = new THREE.PointsMaterial({ 
                        size: pointSize, 
                        vertexColors: true,
                        sizeAttenuation: true
                    });
                    console.log('Point cloud material with vertex colors created');
                } else {
                    console.log('Using grayscale point cloud');
                    material = new THREE.PointsMaterial({ 
                        size: pointSize, 
                        color: 0x888888,
                        sizeAttenuation: true
                    });
                }
                
                pointCloud = new THREE.Points(geometry, material);
            }
            
            // Don't apply transformation to mesh - bounding boxes are already in mesh coordinates
            // The axis alignment is already baked into the scene graph annotations
            
            scene.add(pointCloud);
            console.log('3D model added to scene. Scene has', scene.children.length, 'children');
            console.log('Mesh/Points visible:', pointCloud.visible, 'vertices:', pointCloud.geometry.attributes.position.count);

            // Manually compute bounds from valid positions only
            // Exclude vertices that are exactly 0,0,0 (likely replaced NaN values)
            let minX = Infinity, minY = Infinity, minZ = Infinity;
            let maxX = -Infinity, maxY = -Infinity, maxZ = -Infinity;
            let validPointCount = 0;
            
            for (let i = 0; i < points.length; i += 3) {
                const x = points[i];
                const y = points[i + 1];
                const z = points[i + 2];
                // Check if point is valid AND not a replaced NaN (0,0,0 or suspiciously large)
                // Use 100 meter threshold - appropriate for room-scale 3D scans
                // Values like 4294.97 (2^32/1e6) indicate data encoding issues
                const isValid = isFinite(x) && isFinite(y) && isFinite(z) &&
                               !(x === 0 && y === 0 && z === 0) &&
                               Math.abs(x) < 100 && Math.abs(y) < 100 && Math.abs(z) < 100;
                
                if (isValid) {
                    minX = Math.min(minX, x);
                    maxX = Math.max(maxX, x);
                    minY = Math.min(minY, y);
                    maxY = Math.max(maxY, y);
                    minZ = Math.min(minZ, z);
                    maxZ = Math.max(maxZ, z);
                    validPointCount++;
                }
            }
            
            if (validPointCount === 0) {
                console.error('No valid points found!');
                return;
            }
            
            const center = new THREE.Vector3((minX + maxX) / 2, (minY + maxY) / 2, (minZ + maxZ) / 2);
            const size = new THREE.Vector3(maxX - minX, maxY - minY, maxZ - minZ);
            const maxDim = Math.max(size.x, size.y, size.z);
            
            console.log('Model bounds:');
            console.log('  Center: [', center.x.toFixed(2), ',', center.y.toFixed(2), ',', center.z.toFixed(2), ']');
            console.log('  Size: [', size.x.toFixed(2), ',', size.y.toFixed(2), ',', size.z.toFixed(2), ']');
            console.log('  MaxDim:', maxDim.toFixed(2));
            console.log('  Valid points:', validPointCount, '/', points.length / 3);
            
            // Set camera target and position for OrbitControls (Z-up coordinate system)
            if (controls && isFinite(maxDim) && maxDim > 0) {
                controls.target.copy(center);
                const distance = maxDim * 2.5;
                // Position camera for Z-up: elevated in Z, offset in X and Y
                camera.position.set(center.x + distance, center.y + distance * 0.7, center.z + distance * 0.5);
                controls.update();
                
                // Reset vertical offset and store initial positions
                verticalOffset = 0;
                initialCameraZ = camera.position.z;
                initialTargetZ = controls.target.z;
                const cameraHeightSlider = document.getElementById('camera-height');
                const cameraHeightValue = document.getElementById('camera-height-value');
                if (cameraHeightSlider && cameraHeightValue) {
                    cameraHeightSlider.value = 0;
                    cameraHeightValue.textContent = '0.0';
                }
                
                console.log('Camera set to:', camera.position.x.toFixed(2), camera.position.y.toFixed(2), camera.position.z.toFixed(2));
                console.log('Looking at:', center.x.toFixed(2), center.y.toFixed(2), center.z.toFixed(2));
            } else {
                console.error('Could not set camera position! maxDim:', maxDim, 'isFinite:', isFinite(maxDim));
            }
        }

        function createBoundingBox(bbox) {
            const center = new THREE.Vector3(...bbox.center);
            const halfDims = new THREE.Vector3(...bbox.half_dims);
            const rot = bbox.rotation;

            if (bbox.object_id < 3) {
                console.log('Creating bbox', bbox.object_id, 'at [', center.x.toFixed(2), center.y.toFixed(2), center.z.toFixed(2), '] dims: [', halfDims.x.toFixed(2), halfDims.y.toFixed(2), halfDims.z.toFixed(2), ']');
            }

            const geometry = new THREE.BoxGeometry(
                halfDims.x * 2,
                halfDims.y * 2,
                halfDims.z * 2
            );

            // Use EdgesGeometry for clean, thick lines
            const edges = new THREE.EdgesGeometry(geometry);
            
            const material = new THREE.LineBasicMaterial({
                color: 0xff0000,
                linewidth: 3, // Note: linewidth > 1 may not work on all platforms, but we'll set it anyway
                transparent: true,
                opacity: 0.8
            });

            const box = new THREE.LineSegments(edges, material);
            box.position.copy(center);
            
            // Handle quaternion - ScanNet uses [x, y, z, w] format
            const quaternion = new THREE.Quaternion();
            if (rot && rot.length === 4) {
                // ScanNet format is [x, y, z, w]
                quaternion.set(rot[0], rot[1], rot[2], rot[3]);
                quaternion.normalize();
                
                if (bbox.object_id < 3) {
                    console.log('Bbox', bbox.object_id, 'quaternion:', rot, 'normalized:', quaternion.x.toFixed(3), quaternion.y.toFixed(3), quaternion.z.toFixed(3), quaternion.w.toFixed(3));
                }
            } else {
                quaternion.set(0, 0, 0, 1); // Identity quaternion
            }
            
            box.setRotationFromQuaternion(quaternion);
            box.userData.objectId = bbox.object_id;

            return box;
        }

        function loadBoundingBoxes() {
            if (!sceneGraphData || !sceneGraphData.objects) return;

            // Remove existing bboxes
            bboxes.forEach(bbox => {
                scene.remove(bbox);
                bbox.geometry.dispose();
                bbox.material.dispose();
            });
            bboxes = [];

            sceneGraphData.objects.forEach(obj => {
                const bbox = obj.bbox;
                if (bbox) {
                    const box = createBoundingBox({
                        center: bbox.center,
                        half_dims: bbox.half_dims,
                        rotation: bbox.rotation,
                        object_id: obj.id
                    });
                    bboxes.push(box);
                    // Don't add to scene by default - only show on selection or when "Show All" is checked
                }
            });
        }

        function updateSceneInfo() {
            if (!sceneGraphData) return;
            
            const info = `Scene ID: ${sceneGraphData.id || 'Unknown'}<br>
                Objects: ${sceneGraphData.objects ? sceneGraphData.objects.length : 0}<br>
                Relationships: ${sceneGraphData.relationships ? sceneGraphData.relationships.length : 0}<br>
                Attributes: ${sceneGraphData.attributes ? Object.keys(sceneGraphData.attributes).length : 0}`;
            
            document.getElementById('scene-summary').innerHTML = info;
        }

        function updateObjectsList() {
            if (!sceneGraphData || !sceneGraphData.objects) return;

            const container = document.getElementById('objects-container');
            container.innerHTML = '';
            
            let displayedCount = 0;
            let totalCount = sceneGraphData.objects.length;

            sceneGraphData.objects.forEach(obj => {
                // Apply filters
                if (!objectMatchesFilters(obj)) return;
                displayedCount++;
                
                const div = document.createElement('div');
                div.className = 'object-item';
                div.dataset.objectId = obj.id;
                
                // Get attributes for this object (predicted)
                let attributesHTML = '<div class="object-attributes">';
                let hasAttributes = false;
                
                if (sceneGraphData.attributes && sceneGraphData.attributes.length > 0) {
                    const objAttributes = sceneGraphData.attributes.filter(attr => attr.object_id === obj.id);
                    if (objAttributes.length > 0) {
                        hasAttributes = true;
                        objAttributes.forEach(attr => {
                            const validation = attributeValidations[attr.id];
                            const validationClass = validation === 'correct' ? 'validated-correct' : 
                                                   validation === 'incorrect' ? 'validated-incorrect' : '';
                            // Only show validation buttons in attribute mode
                            const validationBtnsHTML = annotationMode === 'attribute' ? `
                                    <span class="attr-validation-btns">
                                        <button class="attr-validation-btn correct ${validation === 'correct' ? 'active' : ''}" 
                                                onclick="validateAttribute('${attr.id}', 'correct', event)" 
                                                title="Mark as correct">✓</button>
                                        <button class="attr-validation-btn incorrect ${validation === 'incorrect' ? 'active' : ''}" 
                                                onclick="validateAttribute('${attr.id}', 'incorrect', event)" 
                                                title="Mark as incorrect">✗</button>
                                    </span>` : '';
                            attributesHTML += `
                                <span class="attribute-tag ${validationClass}" data-attr-id="${attr.id}">
                                    <span class="attr-name">${escapeHtml(attr.name)}</span>
                                    ${validationBtnsHTML}
                                </span>`;
                        });
                    }
                }
                
                // Get added attributes for this object
                const objAnnotatedAttrs = additionalAttributes.filter(attr => attr.object_id === obj.id);
                if (objAnnotatedAttrs.length > 0) {
                    hasAttributes = true;
                    objAnnotatedAttrs.forEach(attr => {
                        // Only show delete button in attribute mode
                        const deleteBtnHTML = annotationMode === 'attribute' ? 
                            `<button class="attr-delete-btn" onclick="deleteAnnotatedAttribute('${attr.id}', event)" title="Remove">×</button>` : '';
                        attributesHTML += `
                            <span class="attribute-tag annotated-added" data-annotated-attr-id="${attr.id}">
                                <span class="attr-name">${escapeHtml(attr.name)}</span>
                                ${deleteBtnHTML}
                            </span>`;
                    });
                }
                
                attributesHTML += '</div>';
                
                // Add attribute annotation form - only in attribute mode
                const addAttrHTML = annotationMode === 'attribute' ? `
                    <button class="toggle-add-attr-btn" onclick="toggleAddAttributeForm(${obj.id}, event)">+ Add Attribute</button>
                    <div class="add-attribute-section hidden" id="add-attr-form-${obj.id}">
                        <div class="add-attr-row">
                            <input type="text" class="add-attr-input" id="attr-name-${obj.id}" placeholder="Attribute name">
                            <button class="add-attr-btn" onclick="addAnnotatedAttribute(${obj.id}, event)">Add</button>
                        </div>
                    </div>
                ` : '';
                
                div.innerHTML = `
                    <div class="object-id">Object ${obj.id}</div>
                    <div class="object-labels">${obj.labels ? obj.labels.map(l => escapeHtml(l)).join(', ') : 'No labels'}</div>
                    ${hasAttributes ? attributesHTML : '<div class="object-attributes"><em style="color: #999;">No attributes</em></div>'}
                    ${addAttrHTML}
                `;
                div.addEventListener('click', (e) => {
                    // Don't select if clicking on buttons or inputs
                    if (e.target.tagName === 'BUTTON' || e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return;
                    selectObject(obj.id);
                });
                container.appendChild(div);
            });
            
            // Show filter status
            if (selectedAttributeFilters.size > 0) {
                const filterInfo = document.createElement('div');
                filterInfo.style.cssText = 'padding: 8px; font-size: 11px; color: #666; background: #f0f0f0; border-radius: 3px; margin-bottom: 8px;';
                filterInfo.textContent = `Showing ${displayedCount} of ${totalCount} objects`;
                container.insertBefore(filterInfo, container.firstChild);
            }
        }

        function selectObject(objectId) {
            selectedObjectId = objectId;
            
            // Update object list selection
            document.querySelectorAll('.object-item').forEach(item => {
                item.classList.toggle('selected', item.dataset.objectId == objectId);
            });
            
            // In similarity mode, show candidates for similar object annotation
            if (annotationMode === 'similarity') {
                highlightedObjectIds.clear();
                showAnnotationCandidates(objectId);
                
                // Highlight selected object in purple
                updateBoundingBoxes();
                const bbox = bboxes.find(b => b.userData.objectId === objectId);
                if (bbox) {
                    bbox.material.color.setHex(0x9c27b0);
                    bbox.material.opacity = 0.9;
                    scene.add(bbox);
                }
                updateRelationshipLines();
                return;
            }
            
            // For attribute/relationship/no mode, show normal relationships
            highlightedObjectIds.clear();
            
            // Update bounding box visibility and appearance
            updateBoundingBoxes();

            // Update relationships display
            updateRelationshipsDisplay(objectId);
            
            // Update lines (only for currently highlighted objects)
            updateRelationshipLines();
        }

        function createSimilarityAnnotation(candidateId, event) {
            console.log('createSimilarityAnnotation called:');
            console.log('  candidateId:', candidateId);
            console.log('  selectedObjectId:', selectedObjectId);
            console.log('  event:', event);
            
            if (event) event.stopPropagation();
            
            if (selectedObjectId === null || selectedObjectId === undefined) {
                console.warn('No object selected. Please select an object first.');
                return;
            }
            
            if (selectedObjectId === candidateId) {
                console.warn('Cannot mark object as similar to itself.');
                return;
            }
            
            const obj1 = sceneGraphData.objects.find(o => o.id === selectedObjectId);
            const obj2 = sceneGraphData.objects.find(o => o.id === candidateId);
            
            console.log('  obj1:', obj1);
            console.log('  obj2:', obj2);
            
            if (!obj1 || !obj2) {
                console.error('Could not find objects!');
                console.error('  selectedObjectId:', selectedObjectId, 'found obj1:', obj1);
                console.error('  candidateId:', candidateId, 'found obj2:', obj2);
                return;
            }
            
            const label1 = obj1 ? (obj1.labels[0] || `Object ${selectedObjectId}`) : `Object ${selectedObjectId}`;
            const label2 = obj2 ? (obj2.labels[0] || `Object ${candidateId}`) : `Object ${candidateId}`;
            
            // Check if this pair is already annotated
            const existingIndex = similarityAnnotations.findIndex(ann => 
                (ann.id1 === selectedObjectId && ann.id2 === candidateId) ||
                (ann.id2 === selectedObjectId && ann.id1 === candidateId)
            );
            
            if (existingIndex !== -1) {
                // Remove existing annotation (toggle off)
                console.log('Removing existing annotation at index:', existingIndex);
                similarityAnnotations.splice(existingIndex, 1);
                console.log('Annotation removed. Total annotations:', similarityAnnotations.length);
            } else {
                // Add new annotation (toggle on)
                // Check if same class
                const sameClass = obj1 && obj2 && obj1.labels[0] === obj2.labels[0];
                
                console.log('Creating similarity annotation:');
                console.log('  id1:', selectedObjectId, 'label1:', label1);
                console.log('  id2:', candidateId, 'label2:', label2);
                console.log('  sameClass:', sameClass);
                
                similarityAnnotations.push({
                    id1: selectedObjectId,
                    id2: candidateId,
                    label1: label1,
                    label2: label2,
                    sameClass: sameClass,
                    timestamp: new Date().toISOString()
                });
                
                console.log('Annotation created. Total annotations:', similarityAnnotations.length);
            }
            
            // Clear preview
            previewedCandidateId = null;
            
            updateAnnotationsDisplay();
            showAnnotationCandidates(selectedObjectId); // Refresh to show updated button state
            updateAnnotationLines();
        }

        function togglePreviewCandidate(candidateId, event) {
            console.log('togglePreviewCandidate called:', { candidateId, event });
            // Stop event from bubbling
            if (event) event.stopPropagation();
            
            if (previewedCandidateId === candidateId) {
                // Un-preview
                console.log('Un-previewing candidate:', candidateId);
                previewedCandidateId = null;
                updateBoundingBoxes();
                // Remove highlight from candidate item
                document.querySelectorAll('.candidate-item').forEach(item => {
                    item.classList.remove('previewing');
                });
            } else {
                // Preview this candidate
                console.log('Previewing candidate:', candidateId);
                previewedCandidateId = candidateId;
                updateBoundingBoxes();
                
                // Show candidate's bounding box in blue
                const bbox = bboxes.find(b => b.userData.objectId === candidateId);
                if (bbox) {
                    bbox.material.color.setHex(0x42a5f5); // Blue for preview
                    bbox.material.opacity = 0.8;
                    scene.add(bbox);
                }
                
                // Highlight the candidate item
                document.querySelectorAll('.candidate-item').forEach(item => {
                    item.classList.remove('previewing');
                });
                const candidateItem = event?.currentTarget;
                if (candidateItem) {
                    candidateItem.classList.add('previewing');
                }
            }
        }

        function showAnnotationCandidates(firstObjectId) {
            console.log('showAnnotationCandidates called with firstObjectId:', firstObjectId);
            console.log('  selectedObjectId:', selectedObjectId);
            
            const container = document.getElementById('relationships-container');
            
            if (annotationMode !== 'similarity') {
                // Show normal relationships
                updateRelationshipsDisplay(selectedObjectId);
                return;
            }
            
            if (firstObjectId === null || firstObjectId === undefined) {
                container.innerHTML = '<div style="color: #999; font-size: 12px; padding: 10px;">Select an object from the list to see annotation candidates</div>';
                return;
            }
            
            const firstObj = sceneGraphData.objects.find(o => o.id === firstObjectId);
            console.log('  firstObj:', firstObj ? `id=${firstObj.id}, label="${firstObj.labels[0]}"` : 'null');
            if (!firstObj) return;
            
            const firstClass = firstObj.labels[0];
            
            // Get all other objects, prioritize same class
            const candidates = sceneGraphData.objects
                .filter(o => o.id !== firstObjectId)
                .map(o => {
                    const sameClass = o.labels[0] === firstClass;
                    const alreadyAnnotated = similarityAnnotations.some(ann => 
                        (ann.id1 === firstObjectId && ann.id2 === o.id) ||
                        (ann.id2 === firstObjectId && ann.id1 === o.id)
                    );
                    return {
                        id: o.id,
                        label: o.labels[0] || `Object ${o.id}`,
                        sameClass: sameClass,
                        alreadyAnnotated: alreadyAnnotated
                    };
                })
                .sort((a, b) => {
                    // Sort: same class first, then by label
                    // Note: We DON'T sort by annotation status to keep items stable
                    // This prevents confusion where users click item #1, then see it
                    // jump to the bottom after being annotated
                    if (a.sameClass !== b.sameClass) return b.sameClass ? 1 : -1;
                    // Removed: if (a.alreadyAnnotated !== b.alreadyAnnotated) return a.alreadyAnnotated ? 1 : -1;
                    return a.label.localeCompare(b.label);
                });
            
            let html = `<div style="font-size: 12px; margin-bottom: 10px; padding: 10px; background: #f3e5f5; border-radius: 4px;">
                <strong>Selected:</strong> ${firstObj.labels[0] || `Object ${firstObjectId}`}<br>
                <span style="font-size: 10px; color: #666;">Click "Mark Similar" to create annotation</span>
            </div>`;
            
            // Show same class first
            const sameClassCandidates = candidates.filter(c => c.sameClass);
            const otherCandidates = candidates.filter(c => !c.sameClass);
            
            if (sameClassCandidates.length > 0) {
                html += '<div style="font-weight: bold; font-size: 11px; margin: 10px 0 5px 0; color: #4caf50;">✓ Same Class</div>';
                console.log('Rendering same class candidates:', sameClassCandidates.length);
                sameClassCandidates.slice(0, 10).forEach((c, index) => {
                    console.log(`  Candidate ${index}: id=${c.id}, label="${c.label}"`);
                    const btnText = c.alreadyAnnotated ? 'Remove' : 'Mark Similar';
                    const btnClass = c.alreadyAnnotated ? 'annotate-btn remove-btn' : 'annotate-btn';
                    const previewClass = previewedCandidateId === c.id ? 'previewing' : '';
                    html += `<div class="candidate-item same-class ${previewClass}" onclick="togglePreviewCandidate(${c.id}, event)">
                        <div class="candidate-info">
                            <div class="candidate-label">${c.label}</div>
                            <div class="candidate-match">✓ Matching class</div>
                        </div>
                        <div>
                            <button class="${btnClass}" onclick="createSimilarityAnnotation(${c.id}, event)">${btnText}</button>
                        </div>
                    </div>`;
                });
            }
            
            if (otherCandidates.length > 0) {
                html += `<div style="font-weight: bold; font-size: 11px; margin: 10px 0 5px 0; color: #ff9800;">⚠ Different Class (${otherCandidates.length})</div>`;
                console.log('Rendering different class candidates:', otherCandidates.length);
                otherCandidates.forEach((c, index) => {
                    console.log(`  Candidate ${index}: id=${c.id}, label="${c.label}"`);
                    const btnText = c.alreadyAnnotated ? 'Remove' : 'Mark Similar';
                    const btnClass = c.alreadyAnnotated ? 'annotate-btn remove-btn' : 'annotate-btn';
                    const previewClass = previewedCandidateId === c.id ? 'previewing' : '';
                    html += `<div class="candidate-item different-class ${previewClass}" onclick="togglePreviewCandidate(${c.id}, event)">
                        <div class="candidate-info">
                            <div class="candidate-label">${c.label}</div>
                            <div class="candidate-match">⚠ Different class</div>
                        </div>
                        <div>
                            <button class="${btnClass}" onclick="createSimilarityAnnotation(${c.id}, event)">${btnText}</button>
                        </div>
                    </div>`;
                });
            }
            
            container.innerHTML = html;
        }

        function updateAnnotationsDisplay() {
            const container = document.getElementById('annotations-container');
            let html = '';
            
            if (similarityAnnotations.length === 0) {
                html += '<div style="color: #999; font-size: 11px;">No annotations yet. Enable annotation mode and select objects.</div>';
            } else {
                similarityAnnotations.forEach((ann, idx) => {
                    const icon = ann.sameClass ? '✓' : '⚠';
                    const classInfo = ann.sameClass ? 'Same class' : 'Different classes';
                    html += `<div class="annotation-item">
                        <div>
                            <span style="color: ${ann.sameClass ? '#4caf50' : '#ff9800'};">${icon}</span>
                            <strong>${escapeHtml(ann.label1)}</strong> ↔ <strong>${escapeHtml(ann.label2)}</strong>
                            <div style="font-size: 9px; color: #999;">${classInfo}</div>
                        </div>
                        <button class="delete-btn" onclick="deleteAnnotation(${idx})">×</button>
                    </div>`;
                });
            }
            
            container.innerHTML = html;
        }

        function deleteAnnotation(index) {
            similarityAnnotations.splice(index, 1);
            updateAnnotationsDisplay();
            updateAnnotationLines();
        }

        // Attribute validation functions
        function validateAttribute(attrId, status, event) {
            if (event) event.stopPropagation();
            
            // Toggle validation: if already set to this status, clear it
            if (attributeValidations[attrId] === status) {
                delete attributeValidations[attrId];
            } else {
                attributeValidations[attrId] = status;
            }
            
            // Update the UI
            updateObjectsList();
            updateValidationStats();
        }
        
        function updateValidationStats() {
            const statsContainer = document.getElementById('validation-stats');
            if (!statsContainer) return;
            
            let html = '';
            
            // Show attribute stats only in attribute mode
            if (annotationMode === 'attribute') {
                const totalAttrs = sceneGraphData.attributes ? sceneGraphData.attributes.length : 0;
                const attrCorrectCount = Object.values(attributeValidations).filter(v => v === 'correct').length;
                const attrIncorrectCount = Object.values(attributeValidations).filter(v => v === 'incorrect').length;
                const attrAddedCount = additionalAttributes.length;
                
                html += `
                    <div>
                        <strong>Attrs:</strong> ${totalAttrs} | 
                        <span style="color: #28a745;">✓${attrCorrectCount}</span> 
                        <span style="color: #dc3545;">✗${attrIncorrectCount}</span> 
                        <span style="color: #28a745;">+${attrAddedCount}</span>
                    </div>
                `;
            }
            
            // Show relationship stats only in relationship mode
            if (annotationMode === 'relationship') {
                const totalRels = sceneGraphData.relationships ? sceneGraphData.relationships.length : 0;
                const relCorrectCount = Object.values(relationshipValidations).filter(v => v === 'correct').length;
                const relIncorrectCount = Object.values(relationshipValidations).filter(v => v === 'incorrect').length;
                const relAddedCount = additionalRelationships.length;
                
                html += `
                    <div>
                        <strong>Rels:</strong> ${totalRels} | 
                        <span style="color: #28a745;">✓${relCorrectCount}</span> 
                        <span style="color: #dc3545;">✗${relIncorrectCount}</span> 
                        <span style="color: #28a745;">+${relAddedCount}</span>
                    </div>
                `;
            }
            
            // Show similarity stats in similarity mode
            if (annotationMode === 'similarity') {
                html += `
                    <div>
                        <strong>Similar pairs:</strong> ${similarityAnnotations.length}
                    </div>
                `;
            }
            
            statsContainer.innerHTML = html;
        }
        
        function exportAnnotations() {
            if (!sceneGraphData && annotationMode !== 'similarity') {
                alert('No scene graph loaded');
                return;
            }
            
            const exportData = {
                scene_id: sceneGraphData?.id || currentSceneId,
                timestamp: new Date().toISOString(),
                annotation_type: annotationMode || 'all'
            };
            
            // Similarity (always include)
            exportData.similarity = {
                annotations: similarityAnnotations,
                summary: {
                    total: similarityAnnotations.length
                }
            };
            
            // Attributes (always include)
            const predictedAttrs = sceneGraphData?.attributes || [];
            exportData.attributes = {
                predicted: {
                    total: predictedAttrs.length,
                    items: predictedAttrs.map(attr => ({
                        id: attr.id,
                        object_id: attr.object_id,
                        name: attr.name,
                        type: attr.type || null,
                        validation: attributeValidations[attr.id] || null
                    }))
                },
                added: additionalAttributes,
                summary: {
                    predicted_total: predictedAttrs.length,
                    correct: Object.values(attributeValidations).filter(v => v === 'correct').length,
                    incorrect: Object.values(attributeValidations).filter(v => v === 'incorrect').length,
                    added: additionalAttributes.length
                }
            };
            
            // Relationships (always include)
            const predictedRels = sceneGraphData?.relationships || [];
            exportData.relationships = {
                predicted: {
                    total: predictedRels.length,
                    items: predictedRels.map((rel, idx) => ({
                        index: idx,
                        subject_id: rel.subject_id,
                        predicate: rel.name,
                        object_ids: rel.recipient_id || [],
                        validation: relationshipValidations[idx] || null
                    }))
                },
                added: additionalRelationships,
                summary: {
                    predicted_total: predictedRels.length,
                    correct: Object.values(relationshipValidations).filter(v => v === 'correct').length,
                    incorrect: Object.values(relationshipValidations).filter(v => v === 'incorrect').length,
                    added: additionalRelationships.length
                }
            };
            
            const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `annotations_${sceneGraphData?.id || currentSceneId}_${Date.now()}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }
        
        function loadAnnotations() {
            const fileInput = document.getElementById('annotations-file');
            fileInput.click();
        }
        
        function processAnnotationFile(file) {
            if (!file) return;
            
            const reader = new FileReader();
            reader.onload = (e) => {
                try {
                    const data = JSON.parse(e.target.result);
                    
                    // Check if the scene matches (optional warning)
                    if (data.scene_id && sceneGraphData && data.scene_id !== sceneGraphData.id) {
                        if (!confirm(`Warning: This annotation file is for scene "${data.scene_id}" but you have "${sceneGraphData.id}" loaded.\n\nLoad annotations anyway?`)) {
                            return;
                        }
                    }
                    
                    // Load similarity annotations
                    if (data.similarity && data.similarity.annotations) {
                        similarityAnnotations = data.similarity.annotations;
                        console.log(`Loaded ${similarityAnnotations.length} similarity annotations`);
                    }
                    
                    // Load attribute validations
                    if (data.attributes) {
                        if (data.attributes.predicted && data.attributes.predicted.items) {
                            attributeValidations = {};
                            data.attributes.predicted.items.forEach(attr => {
                                if (attr.validation) {
                                    attributeValidations[attr.id] = attr.validation;
                                }
                            });
                            console.log(`Loaded ${Object.keys(attributeValidations).length} attribute validations`);
                        }
                        
                        if (data.attributes.added) {
                            additionalAttributes = data.attributes.added;
                            console.log(`Loaded ${additionalAttributes.length} additional attributes`);
                        }
                    }
                    
                    // Load relationship validations
                    if (data.relationships) {
                        if (data.relationships.predicted && data.relationships.predicted.items) {
                            relationshipValidations = {};
                            data.relationships.predicted.items.forEach(rel => {
                                if (rel.validation) {
                                    relationshipValidations[rel.index] = rel.validation;
                                }
                            });
                            console.log(`Loaded ${Object.keys(relationshipValidations).length} relationship validations`);
                        }
                        
                        if (data.relationships.added) {
                            additionalRelationships = data.relationships.added;
                            console.log(`Loaded ${additionalRelationships.length} additional relationships`);
                        }
                    }
                    
                    // Update the UI
                    updateObjectsList();
                    updateRelationshipsDisplay(selectedObjectId);
                    updateValidationStats();
                    
                    alert(`Annotations loaded successfully!\n\nScene: ${data.scene_id || 'unknown'}\nTimestamp: ${data.timestamp || 'unknown'}`);
                    
                } catch (error) {
                    console.error('Error loading annotations:', error);
                    alert('Error loading annotation file: ' + error.message);
                }
                
                // Reset file input
                fileInput.value = '';
            };
            
            reader.readAsText(file);
        }
        
        function clearAttributeValidations() {
            attributeValidations = {};
            additionalAttributes = [];
            relationshipValidations = {};
            additionalRelationships = [];
            updateObjectsList();
            updateRelationshipsDisplay(selectedObjectId);
            updateValidationStats();
        }
        
        // Additional/missing attribute annotation functions
        function toggleAddAttributeForm(objectId, event) {
            if (event) event.stopPropagation();
            const form = document.getElementById(`add-attr-form-${objectId}`);
            if (form) {
                form.classList.toggle('hidden');
            }
        }
        
        function addAnnotatedAttribute(objectId, event) {
            if (event) event.stopPropagation();
            
            const nameInput = document.getElementById(`attr-name-${objectId}`);
            
            const name = nameInput.value.trim();
            if (!name) {
                alert('Please enter an attribute name');
                return;
            }
            
            const id = `added_${objectId}_${Date.now()}`;
            
            additionalAttributes.push({
                id: id,
                object_id: objectId,
                name: name,
                timestamp: new Date().toISOString()
            });
            
            // Clear input
            nameInput.value = '';
            
            // Update UI
            updateObjectsList();
            updateValidationStats();
        }
        
        function deleteAnnotatedAttribute(attrId, event) {
            if (event) event.stopPropagation();
            
            const index = additionalAttributes.findIndex(a => a.id === attrId);
            if (index !== -1) {
                additionalAttributes.splice(index, 1);
                updateObjectsList();
                updateValidationStats();
            }
        }
        
        // Relationship validation functions
        function validateRelationship(relIndex, status, event) {
            if (event) event.stopPropagation();
            
            // Toggle validation: if already set to this status, clear it
            if (relationshipValidations[relIndex] === status) {
                delete relationshipValidations[relIndex];
            } else {
                relationshipValidations[relIndex] = status;
            }
            
            // Update the UI
            updateRelationshipsDisplay(selectedObjectId);
            updateValidationStats();
        }
        
        function addRelationship(subjectId, event) {
            if (event) event.stopPropagation();
            
            const predicateInput = document.getElementById(`rel-predicate-${subjectId}`);
            const objectSelect = document.getElementById(`rel-object-${subjectId}`);
            
            const predicate = predicateInput.value.trim();
            const objectId = parseInt(objectSelect.value);
            
            if (!predicate) {
                alert('Please select a predicate');
                return;
            }
            if (!objectId) {
                alert('Please select a target object');
                return;
            }
            
            const id = `added_rel_${subjectId}_${objectId}_${Date.now()}`;
            
            additionalRelationships.push({
                id: id,
                subject_id: subjectId,
                object_id: objectId,
                predicate: predicate,
                timestamp: new Date().toISOString()
            });
            
            // Clear inputs
            predicateInput.value = '';
            objectSelect.value = '';
            
            // Update UI
            updateRelationshipsDisplay(selectedObjectId);
            updateValidationStats();
        }
        
        function deleteAddedRelationship(relId, event) {
            if (event) event.stopPropagation();
            
            const index = additionalRelationships.findIndex(r => r.id === relId);
            if (index !== -1) {
                additionalRelationships.splice(index, 1);
                updateRelationshipsDisplay(selectedObjectId);
                updateValidationStats();
            }
        }

        function updateAnnotationLines() {
            // Remove existing annotation lines
            annotationLines.forEach(line => {
                scene.remove(line);
                line.geometry.dispose();
                line.material.dispose();
            });
            annotationLines = [];
            
            if (annotationMode !== 'similarity') return;
            
            // Draw lines for all similarity annotations
            similarityAnnotations.forEach(ann => {
                const bbox1 = bboxes.find(b => b.userData.objectId === ann.id1);
                const bbox2 = bboxes.find(b => b.userData.objectId === ann.id2);
                
                if (bbox1 && bbox2) {
                    const points = [];
                    points.push(bbox1.position.clone());
                    points.push(bbox2.position.clone());
                    
                    const geometry = new THREE.BufferGeometry().setFromPoints(points);
                    const color = ann.sameClass ? 0x9c27b0 : 0xff9800; // Purple for same class, orange for different
                    const material = new THREE.LineDashedMaterial({ 
                        color: color,
                        linewidth: 2,
                        dashSize: 0.3,
                        gapSize: 0.1,
                        transparent: true,
                        opacity: 0.7
                    });
                    
                    const line = new THREE.Line(geometry, material);
                    line.computeLineDistances(); // Required for dashed lines
                    annotationLines.push(line);
                    scene.add(line);
                    
                    // Show both bboxes
                    scene.add(bbox1);
                    scene.add(bbox2);
                }
            });
        }

        function highlightRelatedObject(objectId) {
            // Toggle highlight
            if (highlightedObjectIds.has(objectId)) {
                highlightedObjectIds.delete(objectId);
            } else {
                // Assign a color to this object
                const color = highlightColors[nextColorIndex % highlightColors.length];
                highlightedObjectIds.set(objectId, color);
                nextColorIndex++;
            }
            updateBoundingBoxes();
            updateRelationshipsDisplay(selectedObjectId); // Refresh to update visual indicators
            updateRelationshipLines(); // Draw/update lines to highlighted objects
        }
        
        function highlightBothObjects(objectId1, objectId2) {
            // Check if both are already highlighted
            const bothHighlighted = highlightedObjectIds.has(objectId1) && highlightedObjectIds.has(objectId2);
            
            if (bothHighlighted) {
                // Remove both
                highlightedObjectIds.delete(objectId1);
                highlightedObjectIds.delete(objectId2);
            } else {
                // Add both (if not already highlighted)
                if (!highlightedObjectIds.has(objectId1)) {
                    const color1 = highlightColors[nextColorIndex % highlightColors.length];
                    highlightedObjectIds.set(objectId1, color1);
                    nextColorIndex++;
                }
                if (!highlightedObjectIds.has(objectId2)) {
                    const color2 = highlightColors[nextColorIndex % highlightColors.length];
                    highlightedObjectIds.set(objectId2, color2);
                    nextColorIndex++;
                }
            }
            updateBoundingBoxes();
            updateRelationshipsDisplay(selectedObjectId);
            updateRelationshipLines();
        }

        function updateBoundingBoxes() {
            bboxes.forEach(bbox => {
                const objId = bbox.userData.objectId;
                if (objId === selectedObjectId && annotationMode === 'similarity') {
                    // Selected object in similarity mode - show in purple
                    bbox.material.color.setHex(0x9c27b0);
                    bbox.material.opacity = 1.0;
                    scene.add(bbox);
                } else if (objId === selectedObjectId) {
                    // Selected object in normal/attribute/relationship mode - show in green
                    bbox.material.color.setHex(0x00ff00);
                    bbox.material.opacity = 1.0;
                    scene.add(bbox);
                } else if (objId === previewedCandidateId && annotationMode === 'similarity') {
                    // Previewed candidate in similarity mode - show in blue
                    bbox.material.color.setHex(0x42a5f5);
                    bbox.material.opacity = 1.0;
                    scene.add(bbox);
                } else if (highlightedObjectIds.has(objId)) {
                    // Highlighted related object - show in assigned color
                    const color = highlightedObjectIds.get(objId);
                    bbox.material.color.setHex(color.hex);
                    bbox.material.opacity = 1.0;
                    scene.add(bbox);
                } else {
                    // Other objects - show in red only if "Show All" is checked
                    bbox.material.color.setHex(0xff0000);
                    bbox.material.opacity = 0.7;
                    if (showAllBboxes) {
                        scene.add(bbox);
                    } else {
                        scene.remove(bbox);
                    }
                }
            });
        }

        function updateRelationshipsDisplay(objectId) {
            const container = document.getElementById('relationships-container');
            if (!sceneGraphData || objectId === null) {
                container.innerHTML = 'Select an object to view its relationships';
                return;
            }
            
            const relationships = sceneGraphData.relationships || [];

            // Find relationships where this object is the subject (outgoing only, no incoming since they're reciprocal)
            let outgoing = relationships.filter(rel => rel.subject_id === objectId);
            
            // Separate "in between" relationships - only when selected object is the middle node
            let inBetween = [];
            
            // From outgoing: subject is the selected object (selected is the middle)
            const outgoingBetween = outgoing.filter(rel => 
                rel.name.toLowerCase().includes('between') && rel.recipient_id && rel.recipient_id.length >= 2
            );
            inBetween.push(...outgoingBetween);
            
            // Remove "in between" from outgoing
            outgoing = outgoing.filter(rel => !outgoingBetween.includes(rel));
            
            // Get added relationships for this object
            const addedRels = additionalRelationships.filter(rel => 
                rel.subject_id === objectId || rel.object_id === objectId
            );
            
            // Apply relationship type filters
            if (selectedRelTypeFilters.size > 0) {
                outgoing = outgoing.filter(rel => selectedRelTypeFilters.has(rel.name));
                inBetween = inBetween.filter(rel => selectedRelTypeFilters.has(rel.name));
            }

            const hasRelationships = outgoing.length > 0 || inBetween.length > 0 || addedRels.length > 0;
            
            if (!hasRelationships) {
                const msg = selectedRelTypeFilters.size > 0 
                    ? '<div style="color: #999; font-size: 12px;">No relationships match the selected filters</div>'
                    : '<div style="color: #999; font-size: 12px;">No relationships found</div>';
                container.innerHTML = msg + buildAddRelationshipForm(objectId);
                return;
            }

            let html = '';
            
            // Show filter status if filters are active
            if (selectedRelTypeFilters.size > 0) {
                const totalAll = relationships.filter(rel => rel.subject_id === objectId).length;
                const totalDisplayed = outgoing.length + inBetween.length;
                
                html += `<div style="padding: 8px; font-size: 11px; color: #666; background: #f0f0f0; border-radius: 3px; margin-bottom: 8px;">
                    Showing ${totalDisplayed} of ${totalAll} relationships
                </div>`;
            }
            
            // Helper to create validation buttons - only in relationship mode
            function getRelValidationButtons(relIndex) {
                if (annotationMode !== 'relationship') return '';
                const validation = relationshipValidations[relIndex];
                return `<span class="rel-validation-btns">
                    <button class="rel-validation-btn correct ${validation === 'correct' ? 'active' : ''}" 
                            onclick="validateRelationship(${relIndex}, 'correct', event)" title="Mark correct">✓</button>
                    <button class="rel-validation-btn incorrect ${validation === 'incorrect' ? 'active' : ''}" 
                            onclick="validateRelationship(${relIndex}, 'incorrect', event)" title="Mark incorrect">✗</button>
                </span>`;
            }
            
            function getRelValidationClass(relIndex) {
                const validation = relationshipValidations[relIndex];
                if (validation === 'correct') return 'validated-correct';
                if (validation === 'incorrect') return 'validated-incorrect';
                return '';
            }
            
            if (outgoing.length > 0) {
                html += '<div style="font-weight: bold; margin-bottom: 5px; font-size: 12px;">Relationships:</div>';
                outgoing.forEach(rel => {
                    const relIndex = relationships.indexOf(rel);
                    const targetIds = rel.recipient_id || [];
                    targetIds.forEach(targetId => {
                        const targetObj = sceneGraphData.objects.find(o => o.id === targetId);
                        const targetLabel = targetObj ? escapeHtml(targetObj.labels[0] || `Object ${targetId}`) : `Object ${targetId}`;
                        let style = '';
                        if (highlightedObjectIds.has(targetId)) {
                            const color = highlightedObjectIds.get(targetId);
                            style = `style="background: ${color.css}; color: white; font-weight: bold; border: 2px solid ${color.border}; padding: 2px 6px; border-radius: 3px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);"`;
                        }
                        html += `<div class="relationship-item ${getRelValidationClass(relIndex)}">
                            <span style="color: #666;">→</span>
                            <span class="rel-name"> ${rel.name} </span>
                            <span style="color: #666;">→</span>
                            <span class="rel-target" ${style} onclick="highlightRelatedObject(${targetId})">${targetLabel}</span>
                            ${getRelValidationButtons(relIndex)}
                        </div>`;
                    });
                });
            }
            
            if (inBetween.length > 0) {
                html += '<div style="font-weight: bold; margin: 10px 0 5px 0; font-size: 12px; background: #e8f4fc; padding: 5px; border-radius: 3px;">In Between:</div>';
                inBetween.forEach(rel => {
                    const relIndex = relationships.indexOf(rel);
                    const targetIds = rel.recipient_id || [];
                    
                    // Selected object is the middle - show both endpoints
                    const target1Obj = sceneGraphData.objects.find(o => o.id === targetIds[0]);
                    const target2Obj = sceneGraphData.objects.find(o => o.id === targetIds[1]);
                    
                    const target1Label = target1Obj ? escapeHtml(target1Obj.labels[0] || `Object ${targetIds[0]}`) : `Object ${targetIds[0]}`;
                    const target2Label = target2Obj ? escapeHtml(target2Obj.labels[0] || `Object ${targetIds[1]}`) : `Object ${targetIds[1]}`;
                    
                    let style1 = '';
                    let style2 = '';
                    
                    if (highlightedObjectIds.has(targetIds[0])) {
                        const color = highlightedObjectIds.get(targetIds[0]);
                        style1 = `style="background: ${color.css}; color: white; font-weight: bold; border: 2px solid ${color.border}; padding: 2px 6px; border-radius: 3px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);"`;
                    }
                    if (highlightedObjectIds.has(targetIds[1])) {
                        const color = highlightedObjectIds.get(targetIds[1]);
                        style2 = `style="background: ${color.css}; color: white; font-weight: bold; border: 2px solid ${color.border}; padding: 2px 6px; border-radius: 3px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);"`;
                    }
                    
                    const bothHighlighted = highlightedObjectIds.has(targetIds[0]) && highlightedObjectIds.has(targetIds[1]);
                    
                    // Display: [endpoint1] ← (selected is between) → [endpoint2]
                    html += `<div class="relationship-item in-between-item ${getRelValidationClass(relIndex)}">
                        <span class="rel-target" ${style1} onclick="highlightRelatedObject(${targetIds[0]})">${target1Label}</span>
                        <span style="color: #666;">←</span>
                        <span class="rel-name">(${rel.name})</span>
                        <span style="color: #666;">→</span>
                        <span class="rel-target" ${style2} onclick="highlightRelatedObject(${targetIds[1]})">${target2Label}</span>
                        <button class="highlight-both-btn ${bothHighlighted ? 'active' : ''}" 
                                onclick="highlightBothObjects(${targetIds[0]}, ${targetIds[1]})" 
                                title="Highlight both objects">⚡</button>
                        ${getRelValidationButtons(relIndex)}
                    </div>`;
                });
            }
            
            // Show added relationships
            if (addedRels.length > 0) {
                html += '<div style="font-weight: bold; margin: 10px 0 5px 0; font-size: 12px;">Added:</div>';
                addedRels.forEach(rel => {
                    const otherObjId = rel.subject_id === objectId ? rel.object_id : rel.subject_id;
                    const otherObj = sceneGraphData.objects.find(o => o.id === otherObjId);
                    const otherLabel = otherObj ? escapeHtml(otherObj.labels[0] || `Object ${otherObjId}`) : `Object ${otherObjId}`;
                    const direction = rel.subject_id === objectId ? '→' : '←';
                    
                    // Only show delete button in relationship mode
                    const deleteBtnHTML = annotationMode === 'relationship' ? 
                        `<button class="rel-delete-btn" onclick="deleteAddedRelationship('${rel.id}', event)" title="Remove">×</button>` : '';
                    
                    html += `<div class="relationship-item added-relationship">
                        <span class="rel-name">${rel.predicate}</span> ${direction} 
                        <span class="rel-target" onclick="highlightRelatedObject(${otherObjId})">${otherLabel}</span>
                        ${deleteBtnHTML}
                    </div>`;
                });
            }
            
            // Add relationship form
            html += buildAddRelationshipForm(objectId);

            container.innerHTML = html;
        }
        
        function buildAddRelationshipForm(objectId) {
            // Only show form in relationship mode
            if (annotationMode !== 'relationship') return '';
            if (!sceneGraphData || !sceneGraphData.objects) return '';
            
            // Build object options
            const objectOptions = sceneGraphData.objects
                .filter(o => o.id !== objectId)
                .map(o => `<option value="${o.id}">${escapeHtml(o.labels[0] || 'Object ' + o.id)} (${o.id})</option>`)
                .join('');
            
            // Use global predicates list (collected from all scene graphs)
            const predicateOptions = (allPredicates || [])
                .map(p => `<option value="${p}">${p}</option>`)
                .join('');
            
            return `
                <div id="add-relationship-section">
                    <h4>Add Relationship</h4>
                    <div class="add-rel-row">
                        <span style="font-size: 11px;">Subject: Current Object</span>
                    </div>
                    <div class="add-rel-row">
                        <select class="add-rel-select" id="rel-predicate-${objectId}" style="flex: 1;">
                            <option value="">Select predicate...</option>
                            ${predicateOptions}
                        </select>
                        <select class="add-rel-select" id="rel-object-${objectId}">
                            <option value="">Select object...</option>
                            ${objectOptions}
                        </select>
                    </div>
                    <div class="add-rel-row">
                        <button class="add-rel-btn" onclick="addRelationship(${objectId}, event)">Add Relationship</button>
                    </div>
                </div>
            `;
        }

        function updateRelationshipLines() {
            // Remove existing relationship lines
            relationshipLines.forEach(line => {
                scene.remove(line);
                line.geometry.dispose();
                line.material.dispose();
            });
            relationshipLines = [];
            
            // Don't show lines in similarity mode or if no object selected
            if (annotationMode === 'similarity' || selectedObjectId === null) {
                return;
            }
            
            const selectedBbox = bboxes.find(b => b.userData.objectId === selectedObjectId);
            if (!selectedBbox) return;
            
            // Draw lines only for highlighted related objects
            highlightedObjectIds.forEach((color, relatedObjectId) => {
                const relatedBbox = bboxes.find(b => b.userData.objectId === relatedObjectId);
                if (relatedBbox) {
                    const points = [];
                    points.push(selectedBbox.position.clone());
                    points.push(relatedBbox.position.clone());
                    
                    const geometry = new THREE.BufferGeometry().setFromPoints(points);
                    const material = new THREE.LineBasicMaterial({ 
                        color: color.hex,
                        linewidth: 2,
                        transparent: true,
                        opacity: 0.7
                    });
                    
                    const line = new THREE.Line(geometry, material);
                    relationshipLines.push(line);
                    scene.add(line);
                }
            });
        }

        // Filter functions
        function initializeFilters() {
            if (!sceneGraphData) return;
            
            // Initialize attribute filters
            const attributeSet = new Set();
            if (sceneGraphData.attributes && sceneGraphData.attributes.length > 0) {
                sceneGraphData.attributes.forEach(attr => {
                    if (attr.name) attributeSet.add(attr.name);
                });
            }
            
            const attributeFilter = document.getElementById('attribute-filter');
            attributeFilter.innerHTML = '<option value="">All attributes</option>';
            Array.from(attributeSet).sort().forEach(attr => {
                const option = document.createElement('option');
                option.value = attr;
                option.textContent = attr;
                attributeFilter.appendChild(option);
            });
            
            // Initialize relationship type filters
            const relTypeSet = new Set();
            if (sceneGraphData.relationships && sceneGraphData.relationships.length > 0) {
                sceneGraphData.relationships.forEach(rel => {
                    if (rel.name) relTypeSet.add(rel.name);
                });
            }
            
            const relTypeFilter = document.getElementById('relationship-type-filter');
            relTypeFilter.innerHTML = '<option value="">All types</option>';
            Array.from(relTypeSet).sort().forEach(relType => {
                const option = document.createElement('option');
                option.value = relType;
                option.textContent = relType;
                relTypeFilter.appendChild(option);
            });
        }
        
        function addAttributeFilter(attribute) {
            if (!attribute || selectedAttributeFilters.has(attribute)) return;
            selectedAttributeFilters.add(attribute);
            updateAttributeFilterChips();
            updateObjectsList();
            document.getElementById('clear-object-filters').style.display = 'block';
        }
        
        function removeAttributeFilter(attribute) {
            selectedAttributeFilters.delete(attribute);
            updateAttributeFilterChips();
            updateObjectsList();
            if (selectedAttributeFilters.size === 0) {
                document.getElementById('clear-object-filters').style.display = 'none';
            }
        }
        
        function updateAttributeFilterChips() {
            const container = document.getElementById('selected-attributes');
            container.innerHTML = '';
            selectedAttributeFilters.forEach(attr => {
                const chip = document.createElement('div');
                chip.className = 'filter-chip';
                chip.innerHTML = `${attr} <span class="remove">×</span>`;
                chip.onclick = () => removeAttributeFilter(attr);
                container.appendChild(chip);
            });
        }
        
        function addRelTypeFilter(relType) {
            if (!relType || selectedRelTypeFilters.has(relType)) return;
            selectedRelTypeFilters.add(relType);
            updateRelTypeFilterChips();
            if (selectedObjectId !== null) {
                updateRelationshipsDisplay(selectedObjectId);
            }
            document.getElementById('clear-rel-filters').style.display = 'block';
        }
        
        function removeRelTypeFilter(relType) {
            selectedRelTypeFilters.delete(relType);
            updateRelTypeFilterChips();
            if (selectedObjectId !== null) {
                updateRelationshipsDisplay(selectedObjectId);
            }
            if (selectedRelTypeFilters.size === 0) {
                document.getElementById('clear-rel-filters').style.display = 'none';
            }
        }
        
        function updateRelTypeFilterChips() {
            const container = document.getElementById('selected-rel-types');
            container.innerHTML = '';
            selectedRelTypeFilters.forEach(relType => {
                const chip = document.createElement('div');
                chip.className = 'filter-chip';
                chip.innerHTML = `${relType} <span class="remove">×</span>`;
                chip.onclick = () => removeRelTypeFilter(relType);
                container.appendChild(chip);
            });
        }
        
        function clearAllObjectFilters() {
            selectedAttributeFilters.clear();
            updateAttributeFilterChips();
            updateObjectsList();
            document.getElementById('clear-object-filters').style.display = 'none';
        }
        
        function clearAllRelFilters() {
            selectedRelTypeFilters.clear();
            updateRelTypeFilterChips();
            if (selectedObjectId !== null) {
                updateRelationshipsDisplay(selectedObjectId);
            }
            document.getElementById('clear-rel-filters').style.display = 'none';
        }
        
        function objectMatchesFilters(obj) {
            // If no filters selected, show all objects
            if (selectedAttributeFilters.size === 0) return true;
            
            // Get attributes for this object
            const objAttributes = sceneGraphData.attributes
                ? sceneGraphData.attributes.filter(attr => attr.object_id === obj.id).map(attr => attr.name)
                : [];
            
            // Object must have at least one of the selected attributes
            for (let attr of selectedAttributeFilters) {
                if (objAttributes.includes(attr)) return true;
            }
            return false;
        }

        // Event listeners for controls
        document.getElementById('show-all-bboxes').addEventListener('change', (e) => {
            showAllBboxes = e.target.checked;
            updateBoundingBoxes();
        });
        
        // Filter event listeners
        document.getElementById('attribute-filter').addEventListener('change', (e) => {
            const value = e.target.value;
            if (value) {
                addAttributeFilter(value);
                e.target.value = ''; // Reset dropdown
            }
        });
        
        document.getElementById('relationship-type-filter').addEventListener('change', (e) => {
            const value = e.target.value;
            if (value) {
                addRelTypeFilter(value);
                e.target.value = ''; // Reset dropdown
            }
        });
        
        document.getElementById('clear-object-filters').addEventListener('click', clearAllObjectFilters);
        document.getElementById('clear-rel-filters').addEventListener('click', clearAllRelFilters);

        function setAnnotationMode(mode) {
            // Toggle off if clicking the same mode button
            if (annotationMode === mode && mode !== null) {
                mode = null;
            }
            
            annotationMode = mode;
            
            // Update button states
            document.querySelectorAll('.mode-btn').forEach(btn => {
                btn.classList.remove('active', 'similarity', 'attribute', 'relationship');
            });
            
            const activeBtn = document.getElementById(`mode-${mode || 'none'}`);
            if (activeBtn) {
                activeBtn.classList.add('active');
                if (mode) activeBtn.classList.add(mode);
            }
            
            // Update info text based on mode
            const infoEl = document.getElementById('annotation-info');
            if (mode === 'similarity') {
                infoEl.textContent = 'Select two objects to mark as similar';
                infoEl.style.display = 'block';
            } else if (mode === 'attribute') {
                infoEl.textContent = 'Validate attributes (✓/✗) or add new ones';
                infoEl.style.display = 'block';
            } else if (mode === 'relationship') {
                infoEl.textContent = 'Validate relationships (✓/✗) or add new ones';
                infoEl.style.display = 'block';
            } else {
                infoEl.style.display = 'none';
            }
            
            // Show/hide relationship filters (hidden in similarity mode)
            const relFilters = document.getElementById('relationship-filters');
            if (relFilters) {
                relFilters.style.display = mode === 'similarity' ? 'none' : 'block';
            }
            
            // Update panel title
            const title = document.getElementById('relationships-title');
            if (title) {
                if (mode === 'similarity') {
                    title.textContent = 'Similar Object Candidates';
                } else if (mode === 'relationship') {
                    title.textContent = 'Relationships (Annotation)';
                } else {
                    title.textContent = 'Relationships';
                }
            }
            
            // Refresh the objects list to show/hide attribute annotation UI
            updateObjectsList();
            
            if (mode === 'similarity') {
                // Keep selection if any
                highlightedObjectIds.clear();
                showAnnotationCandidates(selectedObjectId);
                // Clear relationship lines in similarity mode
                updateRelationshipLines();
            } else {
                // Back to normal/attribute/relationship mode
                updateRelationshipsDisplay(selectedObjectId);
                // Restore relationship lines (only if objects are highlighted)
                updateRelationshipLines();
            }
            
            updateBoundingBoxes();
            updateAnnotationsDisplay();
            updateAnnotationLines();
            updateValidationStats();
        }
        
        // Initialize with mode off
        setAnnotationMode(null);

        document.getElementById('export-annotations').addEventListener('click', () => {
            exportAnnotations();
        });
        
        document.getElementById('load-annotations').addEventListener('click', () => {
            loadAnnotations();
        });
        
        document.getElementById('annotations-file').addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                processAnnotationFile(e.target.files[0]);
            }
        });

        document.getElementById('show-points').addEventListener('change', (e) => {
            if (pointCloud) {
                pointCloud.visible = e.target.checked;
            }
        });

        // Point size control
        const pointSizeSlider = document.getElementById('point-size');
        const pointSizeValue = document.getElementById('point-size-value');
        if (pointSizeSlider && pointSizeValue) {
            pointSizeSlider.addEventListener('input', (e) => {
                const size = parseFloat(e.target.value);
                pointSizeValue.textContent = size.toFixed(1);
                if (pointCloud && pointCloud.material) {
                    pointCloud.material.size = size;
                }
            });
        }

        // Scene loading functions
        function populateScenesList() {
            const container = document.getElementById('scenes-list');
            container.innerHTML = '';
            
            availableScenes.forEach(sceneId => {
                const div = document.createElement('div');
                div.className = 'scene-item';
                // Highlight if this is the currently loaded scene
                if (sceneId === currentSceneId) {
                    div.classList.add('selected');
                }
                div.textContent = sceneId;
                div.addEventListener('click', () => loadScene(sceneId));
                container.appendChild(div);
            });
        }

        async function loadScene(sceneId) {
            if (currentSceneId === sceneId) return;
            
            // Auto-detect dataset from scene ID pattern
            currentDataset = getDatasetFromSceneId(sceneId);
            currentSceneId = sceneId;
            document.getElementById('loading').classList.remove('hidden');
            
            // Update selected scene in list
            document.querySelectorAll('.scene-item').forEach(item => {
                item.classList.toggle('selected', item.textContent === sceneId);
            });
            
            try {
                // Load scene graph based on dataset type
                let sgUrl, plyUrls, alignUrl = null, colorUrl = null;
                
                if (currentDataset === 'multiscan') {
                    // Load scene graph from scenegraphs directory (has proper relationships & attributes)
                    sgUrl = `data/scenegraphs_sampled/multiscan/${sceneId}/scene_graph.json`;
                    alignUrl = `data/multiscan/${sceneId}/${sceneId}.align.json`;
                    // PLY mesh is still in the multiscan data directory
                    plyUrls = [
                        `data/multiscan/${sceneId}/${sceneId}.ply`
                    ];
                } else if (currentDataset === '3rscan') {
                    // 3RScan scenes
                    sgUrl = `data/scenegraphs_sampled/3rscan/${sceneId}/scene_graph.json`;
                    // 3RScan: use labeled mesh for geometry (has faces)
                    plyUrls = [
                        `data/3rscan/download/${sceneId}/labels.instances.align.annotated.v2.ply`,
                        `data/3rscan/download/${sceneId}/labels.instances.annotated.v2.ply`,
                        `data/3rscan/download/${sceneId}/labels.instances.annotated.ply`
                    ];
                    // Also try to load real colors from color.align.ply
                    colorUrl = `data/3rscan/download/${sceneId}/color.align.ply`;
                } else {
                    sgUrl = `data/scenegraphs_sampled/scannet/${sceneId}/scene_graph.json`;
                    plyUrls = [
                        `data/scannet/public/v2/scans/${sceneId}/${sceneId}_vh_clean.ply`,
                        `data/scannet/public/v2/scans/${sceneId}/${sceneId}_vh_clean_2.ply`,
                        `data/scannet/public/v2/scans/${sceneId}/${sceneId}_vh_clean_2.labels.ply`
                    ];
                }
                
                // Load alignment transform for multiscan
                let alignTransform = null;
                if (alignUrl) {
                    try {
                        const alignResponse = await fetch(alignUrl);
                        if (alignResponse.ok) {
                            const alignData = await alignResponse.json();
                            alignTransform = alignData.coordinate_transform;
                            console.log('Loaded alignment transform:', alignTransform);
                        }
                    } catch (e) {
                        console.warn('Could not load alignment transform:', e);
                    }
                }
                
                const sgResponse = await fetch(sgUrl);
                const sgText = await sgResponse.text();
                let data = JSON.parse(sgText);
                
                // The scene_graph.json files are already in the correct format for both datasets
                sceneGraphData = data;
                console.log('Loaded scene graph:', sceneGraphData.id, 'with', 
                    (sceneGraphData.objects || []).length, 'objects,',
                    (sceneGraphData.relationships || []).length, 'relationships,',
                    (sceneGraphData.attributes || []).length, 'attributes');
                console.log('DEBUG - First 3 object IDs:', sceneGraphData.objects.slice(0, 3).map(o => o.id));
                console.log('DEBUG - First relationship:', sceneGraphData.relationships[0]);
                console.log('DEBUG - URL loaded from:', sgUrl);
                
                // Clear filters when loading new scene
                selectedAttributeFilters.clear();
                selectedRelTypeFilters.clear();
                updateAttributeFilterChips();
                updateRelTypeFilterChips();
                document.getElementById('clear-object-filters').style.display = 'none';
                document.getElementById('clear-rel-filters').style.display = 'none';
                
                initializeFilters();
                updateSceneInfo();
                loadBoundingBoxes();
                updateObjectsList();
                
                // Clear all validations and annotations for new scene
                attributeValidations = {};
                additionalAttributes = [];
                relationshipValidations = {};
                additionalRelationships = [];
                updateValidationStats();
                
                // Try textured mesh first for multiscan / 3rscan, then fall back to PLY
                let meshLoaded = false;
                const meshCandidates = [];
                if (currentDataset === 'multiscan') {
                    meshCandidates.push({
                        obj: `data/multiscan/${sceneId}/textured_mesh/${sceneId}.obj`,
                        mtl: `data/multiscan/${sceneId}/textured_mesh/${sceneId}.mtl`
                    });
                } else if (currentDataset === '3rscan') {
                    meshCandidates.push({
                        obj: `data/3rscan/download/${sceneId}/mesh.refined.obj`,
                        mtl: `data/3rscan/download/${sceneId}/mesh.refined.mtl`
                    });
                    meshCandidates.push({
                        obj: `data/3rscan/download/${sceneId}/textured_mesh/${sceneId}.obj`,
                        mtl: `data/3rscan/download/${sceneId}/textured_mesh/${sceneId}.mtl`
                    });
                }

                for (const mesh of meshCandidates) {
                    try {
                        await loadTexturedMesh(mesh);
                        meshLoaded = true;
                        console.log('Loaded textured mesh:', mesh.obj);
                        break;
                    } catch (meshErr) {
                        console.warn('Failed to load textured mesh', mesh.obj, '-', meshErr.message || meshErr);
                    }
                }

                // Load point cloud - try various naming patterns if mesh was not loaded
                let plyLoaded = meshLoaded;
                
                if (!meshLoaded) {
                    for (const plyUrl of plyUrls) {
                        try {
                            console.log('Attempting to fetch:', plyUrl);
                            const plyResponse = await fetch(plyUrl);
                            console.log('Fetch response status:', plyResponse.status, plyResponse.statusText);
                            if (!plyResponse.ok) {
                                throw new Error(`HTTP ${plyResponse.status}: ${plyResponse.statusText}`);
                            }
                            console.log('Loading PLY from:', plyUrl);
                            const plyArrayBuffer = await plyResponse.arrayBuffer();
                            console.log('PLY file loaded, size:', plyArrayBuffer.byteLength, 'bytes');
                            const pcData = await parsePLY(plyArrayBuffer);
                            console.log('Parsed PLY - points:', pcData.points.length / 3, 'hasColors:', pcData.hasColors);
                            
                            if (!pcData.points || pcData.points.length === 0) {
                                throw new Error('No points found in PLY file');
                            }
                            
                            // For multiscan/3rscan: Check if we need coordinate transforms
                            // The annotations use Z-up coordinate system (based on "up": [0, 0, 1] in bbox)
                            // Log info to help debug coordinate alignment
                            if (currentDataset === 'multiscan' || currentDataset === '3rscan') {
                                console.log(currentDataset + ' PLY loaded without transform - checking alignment');
                                console.log('Raw mesh first vertex:', pcData.points[0].toFixed(4), pcData.points[1].toFixed(4), pcData.points[2].toFixed(4));
                            }
                            
                            // For 3RScan: try to load real colors from separate file
                            if (colorUrl && currentDataset === '3rscan') {
                                try {
                                    console.log('Attempting to load real colors from:', colorUrl);
                                    const colorResponse = await fetch(colorUrl);
                                    if (colorResponse.ok) {
                                        const colorArrayBuffer = await colorResponse.arrayBuffer();
                                        const colorData = await parsePLY(colorArrayBuffer);
                                        // Only use if vertex count matches
                                        if (colorData.points.length === pcData.points.length && colorData.hasColors) {
                                            console.log('Applying real colors from color.align.ply');
                                            pcData.colors = colorData.colors;
                                            pcData.hasColors = true;
                                        } else {
                                            console.warn('Color file vertex count mismatch:', colorData.points.length / 3, 'vs', pcData.points.length / 3);
                                        }
                                    }
                                } catch (colorErr) {
                                    console.warn('Could not load real colors:', colorErr.message);
                                }
                            }
                            
                            // Sample if too many points (only if no faces, as sampling would break face indices)
                            if (!pcData.hasFaces) {
                                const maxPoints = 200000;
                                const numVertices = pcData.points.length / 3;
                                if (numVertices > maxPoints) {
                                    console.log('Sampling point cloud from', numVertices, 'to', maxPoints, 'points');
                                    const step = Math.floor(numVertices / maxPoints);
                                    const sampledPoints = [];
                                    const sampledColors = [];
                                    for (let v = 0; v < numVertices; v += step) {
                                        const idx = v * 3;
                                        sampledPoints.push(pcData.points[idx], pcData.points[idx+1], pcData.points[idx+2]);
                                        if (pcData.hasColors && pcData.colors) {
                                            const colorIdx = v * 3;
                                            sampledColors.push(pcData.colors[colorIdx], pcData.colors[colorIdx+1], pcData.colors[colorIdx+2]);
                                        }
                                    }
                                    pcData.points = sampledPoints;
                                    pcData.colors = sampledColors;
                                    console.log('Sampled to', sampledPoints.length / 3, 'points');
                                }
                            }
                            
                        loadPointCloud(pcData);
                        plyLoaded = true;
                        console.log('Point cloud loaded successfully from:', plyUrl);
                        break; // Success, exit the loop
                        } catch (plyError) {
                            console.warn('Failed to load from', plyUrl, '- Error:', plyError.message || plyError);
                            // Try next URL
                            continue;
                        }
                    }
                }
                
                if (!plyLoaded) {
                    console.error('Could not load mesh or PLY file from any location');
                    alert('Warning: Could not load geometry. Bounding boxes will be shown, but no mesh/point cloud data.');
                }
            } catch (error) {
                console.error('Error loading scene:', error);
                alert('Error loading scene: ' + error.message);
            } finally {
                document.getElementById('loading').classList.add('hidden');
            }
        }

        // Initialize
        initViewer();
        populateScenesList();
    </script>
</body>
</html>
"""


def generate_html(output_path="viewer_sampled.html", scene_graph_url=None, ply_url=None, 
                  scenegraph_base="data/scenegraphs_sampled/scannet",
                  multiscan_base="data/multiscan",
                  rscan_base="data/3rscan/download",
                  refresh_predicates=False,
                  max_scannet_scenes=None,
                  max_multiscan_scenes=None,
                  max_rscan_scenes=None):
    """
    Generate the standalone HTML viewer file with ScanNet, MultiScan, and 3RScan datasets.
    
    Args:
        output_path: Path where to save the HTML file
        scene_graph_url: Optional URL/path to scene graph JSON (auto-loads if provided)
        ply_url: Optional URL/path to PLY file (auto-loads if provided)
        scenegraph_base: Base path to scene graph data directory
        multiscan_base: Base path to multiscan data directory
        rscan_base: Base path to 3RScan data directory
        max_scannet_scenes: Optional limit on number of ScanNet scenes to include
        max_multiscan_scenes: Optional limit on number of MultiScan scenes to include
        max_rscan_scenes: Optional limit on number of 3RScan scenes to include
    """
    output_path = Path(output_path)
    
    # Get available scenes from ALL datasets
    scannet_scenes = list_available_scenes(scenegraph_base)
    multiscan_scenes = list_multiscan_scenes(multiscan_base)
    rscan_scenes = list_3rscan_scenes(rscan_base)
    
    # Apply limits if specified
    if max_scannet_scenes is not None:
        scannet_scenes = sorted(scannet_scenes)[:max_scannet_scenes]
    if max_multiscan_scenes is not None:
        multiscan_scenes = sorted(multiscan_scenes)[:max_multiscan_scenes]
    if max_rscan_scenes is not None:
        rscan_scenes = sorted(rscan_scenes)[:max_rscan_scenes]
    
    # Combine all scenes into a single sorted list
    all_scenes = sorted(scannet_scenes + multiscan_scenes + rscan_scenes)
    
    # Collect all unique predicates from all scene graphs (uses cache if available)
    all_predicates = collect_all_predicates(force_refresh=refresh_predicates)
    print(f"Found {len(all_predicates)} unique predicates")
    
    # Modify template
    template = HTML_TEMPLATE
    
    # Embed scene list and predicates as JavaScript
    scenes_json = json.dumps(all_scenes)
    predicates_json = json.dumps(all_predicates)
    scenes_script = f'\n        availableScenes = {scenes_json};\n        allPredicates = {predicates_json};\n'
    
    # Insert scene list after global variables declaration  
    global_vars_marker = '        // Detect dataset from scene ID pattern\n        function getDatasetFromSceneId'
    if global_vars_marker in template:
        template = template.replace(global_vars_marker, 
                                   scenes_script + global_vars_marker)
    else:
        # Fallback: insert before Initialize Three.js comment
        template = template.replace('        // Initialize Three.js', 
                                   scenes_script + '        // Initialize Three.js')
    
    if scene_graph_url or ply_url:
        # Add auto-load functionality
        auto_load_script = """
        // Auto-load files if URLs provided
        (async function() {
            const sceneGraphUrl = """ + (f'"{scene_graph_url}"' if scene_graph_url else 'null') + """;
            const plyUrl = """ + (f'"{ply_url}"' if ply_url else 'null') + """;
            
            if (sceneGraphUrl) {
                try {
                    const response = await fetch(sceneGraphUrl);
                    const text = await response.text();
                    sceneGraphData = JSON.parse(text);
                    document.getElementById('sg-status').textContent = `Loaded: ${sceneGraphUrl}`;
                    document.getElementById('sg-status').className = 'file-status loaded';
                    updateSceneInfo();
                    loadBoundingBoxes();
                    updateObjectsList();
                } catch (error) {
                    console.error('Error loading scene graph:', error);
                    document.getElementById('sg-status').textContent = `Error loading: ${error.message}`;
                }
            }
            
            if (plyUrl) {
                try {
                    const response = await fetch(plyUrl);
                    const arrayBuffer = await response.arrayBuffer();
                    const pcData = await parsePLY(arrayBuffer);
                    
                    // Sample if too many points (only if no faces, as sampling would break face indices)
                    if (!pcData.hasFaces) {
                        const maxPoints = 200000;
                        const numVertices = pcData.points.length / 3;
                        if (numVertices > maxPoints) {
                            console.log('Sampling point cloud from', numVertices, 'to', maxPoints, 'points');
                            const step = Math.floor(numVertices / maxPoints);
                            const sampledPoints = [];
                            const sampledColors = [];
                            for (let v = 0; v < numVertices; v += step) {
                                const idx = v * 3;
                                sampledPoints.push(pcData.points[idx], pcData.points[idx+1], pcData.points[idx+2]);
                                if (pcData.hasColors && pcData.colors) {
                                    const colorIdx = v * 3;
                                    sampledColors.push(pcData.colors[colorIdx], pcData.colors[colorIdx+1], pcData.colors[colorIdx+2]);
                                }
                            }
                            pcData.points = sampledPoints;
                            pcData.colors = sampledColors;
                            console.log('Sampled to', sampledPoints.length / 3, 'points');
                        }
                    }
                    
                    loadPointCloud(pcData);
                    document.getElementById('ply-status').textContent = `Loaded: ${plyUrl}`;
                    document.getElementById('ply-status').className = 'file-status loaded';
                } catch (error) {
                    console.error('Error loading PLY:', error);
                    document.getElementById('ply-status').textContent = `Error loading: ${error.message}`;
                }
            }
        })();
"""
        
        # Insert before initViewer() call - find the exact marker with actual newline
        init_marker = '        // Initialize\n        initViewer();'
        if init_marker in template:
            template = template.replace(init_marker, auto_load_script + init_marker)
        else:
            # Fallback: insert before closing script tag
            template = template.replace('    </script>', auto_load_script + '    </script>')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(template)
    
    print(f"Generated HTML viewer: {output_path.absolute()}")
    print(f"Found {len(scannet_scenes)} ScanNet scenes, {len(multiscan_scenes)} MultiScan scenes, {len(rscan_scenes)} 3RScan scenes ({len(all_scenes)} total)")
    if scene_graph_url or ply_url:
        print(f"Auto-loading configured:")
        if scene_graph_url:
            print(f"  Scene graph: {scene_graph_url}")
        if ply_url:
            print(f"  PLY file: {ply_url}")
        print("Note: Auto-loading only works when HTML is served via HTTP (not file://)")
    else:
        print("Open this file in your browser to use the viewer.")
        print("Note: To load scenes, serve the HTML via HTTP (e.g., python -m http.server)")
        print("      Scenes will be listed and clickable when served via HTTP.")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate standalone HTML viewer for scene graphs (supports ScanNet, MultiScan, and 3RScan)")
    parser.add_argument(
        "--output", "-o",
        default="viewer_sampled.html",
        help="Output HTML file path (default: viewer_sampled.html)"
    )
    parser.add_argument(
        "--scene-graph-url",
        help="URL/path to scene graph JSON file (auto-loads when HTML is served via HTTP)"
    )
    parser.add_argument(
        "--ply-url",
        help="URL/path to PLY file (auto-loads when HTML is served via HTTP)"
    )
    parser.add_argument(
        "--multiscan-base",
        default="data/multiscan",
        help="Base path to multiscan data directory (default: data/multiscan)"
    )
    parser.add_argument(
        "--3rscan-base",
        dest="rscan_base",
        default="data/3rscan/download",
        help="Base path to 3RScan data directory (default: data/3rscan/download)"
    )
    parser.add_argument(
        "--refresh-predicates",
        action="store_true",
        help="Force refresh the predicates cache (rescan all scene graphs)"
    )
    parser.add_argument(
        "--max-scannet-scenes",
        type=int,
        help="Maximum number of ScanNet scenes to include"
    )
    parser.add_argument(
        "--max-multiscan-scenes",
        type=int,
        help="Maximum number of MultiScan scenes to include"
    )
    parser.add_argument(
        "--max-rscan-scenes",
        type=int,
        help="Maximum number of 3RScan scenes to include"
    )
    
    args = parser.parse_args()
    generate_html(args.output, args.scene_graph_url, args.ply_url, 
                  multiscan_base=args.multiscan_base,
                  rscan_base=args.rscan_base,
                  refresh_predicates=args.refresh_predicates,
                  max_scannet_scenes=args.max_scannet_scenes,
                  max_multiscan_scenes=args.max_multiscan_scenes,
                  max_rscan_scenes=args.max_rscan_scenes)
