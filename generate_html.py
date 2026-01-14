#!/usr/bin/env python3
"""
Generate standalone HTML viewer for ScanNet scene graphs.
"""

import os
import json
from pathlib import Path


def list_available_scenes(scenegraph_base="data/scenegraphs/scannet"):
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


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ScanNet Scene Graph Viewer</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/gh/mrdoob/three.js@r128/examples/js/controls/OrbitControls.js"></script>
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
            display: inline-block;
            padding: 2px 6px;
            margin: 2px 2px 0 0;
            background: #e8f8f5;
            border: 1px solid #16a085;
            border-radius: 3px;
            font-size: 10px;
            font-style: normal;
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
            <label><input type="checkbox" id="annotation-mode"> Annotation Mode</label>
            <div id="annotation-info" style="font-size: 11px; color: #ccc; margin-top: 5px; display: none;">
                Select two objects to mark as similar
            </div>
            <button id="export-annotations" style="margin-top: 5px; padding: 5px 10px; display: none;">Export Annotations</button>
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
            for (let i = 0; i < lines.length; i++) {
                const line = lines[i].trim();
                if (line.includes('format binary')) {
                    isBinary = true;
                }
                if (line.startsWith('element vertex')) {
                    vertexCount = parseInt(line.split(' ')[2]);
                }
                if (line.startsWith('element face')) {
                    faceCount = parseInt(line.split(' ')[2]);
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
                return parseBinaryPLY(arrayBuffer, headerLength, vertexCount, faceCount, hasColors, hasNormals);
            } else {
                return parseASCIIPLY(text, headerEnd, vertexCount, faceCount, hasColors, hasNormals);
            }
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
                        colors.push(
                            parseInt(parts[3]) / 255,
                            parseInt(parts[4]) / 255,
                            parseInt(parts[5]) / 255
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
        
        function parseBinaryPLY(arrayBuffer, headerLength, vertexCount, faceCount, hasColors, hasNormals) {
            console.log('Parsing binary PLY: headerLength=', headerLength, 'vertexCount=', vertexCount, 'faceCount=', faceCount, 'hasColors=', hasColors, 'hasNormals=', hasNormals);
            const view = new DataView(arrayBuffer, headerLength);
            const points = [];
            const colors = [];
            const indices = [];
            let offset = 0;
            
            // Calculate bytes per vertex
            let bytesPerVertex = 12; // x, y, z (3 floats)
            if (hasNormals) bytesPerVertex += 12; // nx, ny, nz (3 floats)
            if (hasColors) bytesPerVertex += 4; // r, g, b, a (4 uchars)
            console.log('Bytes per vertex:', bytesPerVertex);
            
            try {
                // Parse all vertices
                for (let i = 0; i < vertexCount; i++) {
                    if (offset + 12 > view.byteLength) {
                        console.warn('Reached end of buffer at vertex', i);
                        break;
                    }
                    
                    // Read x, y, z as float32 (little endian)
                    let x = view.getFloat32(offset, true);
                    let y = view.getFloat32(offset + 4, true);
                    let z = view.getFloat32(offset + 8, true);
                    let colorOffset = 12; // Start after x, y, z
                    
                    // Skip normals if present
                    if (hasNormals) {
                        colorOffset += 12; // Skip nx, ny, nz (3 floats)
                    }
                    
                    // Replace NaN with 0 (will be excluded from bounding box calculation)
                    if (isNaN(x) || !isFinite(x)) x = 0;
                    if (isNaN(y) || !isFinite(y)) y = 0;
                    if (isNaN(z) || !isFinite(z)) z = 0;
                    
                    points.push(x, y, z);
                    
                    if (hasColors && offset + colorOffset + 4 <= view.byteLength) {
                        const r = view.getUint8(offset + colorOffset) / 255;
                        const g = view.getUint8(offset + colorOffset + 1) / 255;
                        const b = view.getUint8(offset + colorOffset + 2) / 255;
                        // Skip alpha at colorOffset + 3
                        colors.push(r, g, b);
                    }
                    
                    offset += bytesPerVertex;
                }
                
                const actualVertexCount = points.length / 3;
                console.log('Parsed', actualVertexCount, 'vertices from binary PLY');
                console.log('Offset after vertices:', offset, '/', view.byteLength, 'bytes');
                console.log('Remaining bytes for faces:', view.byteLength - offset);
                console.log('Expected to parse', faceCount, 'faces');
                
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
                        
                        if (numVerts === 3 && offset + 12 <= view.byteLength) {
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
                            offset += 12;
                        } else {
                            // Skip other face types (quads, etc.) or invalid data
                            if (numVerts > 0 && numVerts < 10) {
                                offset += numVerts * 4;
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

        // Global variables
        let scene, camera, renderer, pointCloud, bboxes = [];
        let selectedObjectId = null;
        let highlightedObjectIds = new Map(); // Map of objectId -> color for highlighted related objects
        let sceneGraphData = null;
        let availableScenes = [];
        let currentSceneId = null;
        let showAllBboxes = false;
        let relationshipLines = []; // Lines connecting related objects
        
        // Annotation mode
        let annotationMode = false;
        let annotationFirstObject = null;
        let similarityAnnotations = []; // Array of {id1, id2, label1, label2, timestamp}
        let annotationLines = [];
        let previewedCandidateId = null;
        
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
                pointCloud.geometry.dispose();
                pointCloud.material.dispose();
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
                const isValid = isFinite(x) && isFinite(y) && isFinite(z) &&
                               !(x === 0 && y === 0 && z === 0) &&
                               Math.abs(x) < 1e10 && Math.abs(y) < 1e10 && Math.abs(z) < 1e10;
                
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
                
                // Get attributes for this object
                let attributesHTML = '';
                if (sceneGraphData.attributes && sceneGraphData.attributes.length > 0) {
                    const objAttributes = sceneGraphData.attributes.filter(attr => attr.object_id === obj.id);
                    if (objAttributes.length > 0) {
                        attributesHTML = '<div class="object-attributes">';
                        objAttributes.forEach(attr => {
                            attributesHTML += `<span class="attribute-tag">${attr.name}</span>`;
                        });
                        attributesHTML += '</div>';
                    }
                }
                
                div.innerHTML = `
                    <div class="object-id">Object ${obj.id}</div>
                    <div class="object-labels">${obj.labels ? obj.labels.join(', ') : 'No labels'}</div>
                    ${attributesHTML}
                `;
                div.addEventListener('click', () => selectObject(obj.id));
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
            // In annotation mode, select object and show candidates
            if (annotationMode) {
                selectedObjectId = objectId;
                document.querySelectorAll('.object-item').forEach(item => {
                    item.classList.toggle('selected', item.dataset.objectId == objectId);
                });
                showAnnotationCandidates(objectId);
                
                // Highlight selected object in purple
                updateBoundingBoxes();
                const bbox = bboxes.find(b => b.userData.objectId === objectId);
                if (bbox) {
                    bbox.material.color.setHex(0x9c27b0);
                    bbox.material.opacity = 0.9;
                    scene.add(bbox);
                }
                return;
            }
            
            selectedObjectId = objectId;
            highlightedObjectIds.clear(); // Clear highlighted objects when selecting new object
            
            document.querySelectorAll('.object-item').forEach(item => {
                item.classList.toggle('selected', item.dataset.objectId == objectId);
            });

            // Update bounding box visibility and appearance
            updateBoundingBoxes();

            // Update relationships display
            updateRelationshipsDisplay(objectId);
            
            // Update lines (only for currently highlighted objects)
            updateRelationshipLines();
        }

        function createSimilarityAnnotation(candidateId, event) {
            if (event) event.stopPropagation();
            if (!selectedObjectId || selectedObjectId === candidateId) return;
            
            const obj1 = sceneGraphData.objects.find(o => o.id === selectedObjectId);
            const obj2 = sceneGraphData.objects.find(o => o.id === candidateId);
            const label1 = obj1 ? (obj1.labels[0] || `Object ${selectedObjectId}`) : `Object ${selectedObjectId}`;
            const label2 = obj2 ? (obj2.labels[0] || `Object ${candidateId}`) : `Object ${candidateId}`;
            
            // Check if same class
            const sameClass = obj1 && obj2 && obj1.labels[0] === obj2.labels[0];
            
            similarityAnnotations.push({
                id1: selectedObjectId,
                id2: candidateId,
                label1: label1,
                label2: label2,
                sameClass: sameClass,
                timestamp: new Date().toISOString()
            });
            
            // Clear preview
            previewedCandidateId = null;
            
            updateAnnotationsDisplay();
            showAnnotationCandidates(selectedObjectId); // Refresh to show updated "annotated" status
            updateAnnotationLines();
        }

        function togglePreviewCandidate(candidateId, event) {
            // Stop event from bubbling
            if (event) event.stopPropagation();
            
            if (previewedCandidateId === candidateId) {
                // Un-preview
                previewedCandidateId = null;
                updateBoundingBoxes();
                // Remove highlight from candidate item
                document.querySelectorAll('.candidate-item').forEach(item => {
                    item.classList.remove('previewing');
                });
            } else {
                // Preview this candidate
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
            const container = document.getElementById('relationships-container');
            
            if (!annotationMode) {
                // Show normal relationships
                updateRelationshipsDisplay(selectedObjectId);
                return;
            }
            
            if (firstObjectId === null || firstObjectId === undefined) {
                container.innerHTML = '<div style="color: #999; font-size: 12px; padding: 10px;">Select an object from the list to see annotation candidates</div>';
                return;
            }
            
            const firstObj = sceneGraphData.objects.find(o => o.id === firstObjectId);
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
                    // Sort: same class first, then not annotated, then by label
                    if (a.sameClass !== b.sameClass) return b.sameClass ? 1 : -1;
                    if (a.alreadyAnnotated !== b.alreadyAnnotated) return a.alreadyAnnotated ? 1 : -1;
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
                sameClassCandidates.slice(0, 10).forEach(c => {
                    const disabled = c.alreadyAnnotated ? 'disabled' : '';
                    const btnText = c.alreadyAnnotated ? 'Annotated' : 'Mark Similar';
                    const previewClass = previewedCandidateId === c.id ? 'previewing' : '';
                    html += `<div class="candidate-item same-class ${previewClass}" onclick="togglePreviewCandidate(${c.id}, event)">
                        <div class="candidate-info">
                            <div class="candidate-label">${c.label}</div>
                            <div class="candidate-match">✓ Matching class</div>
                        </div>
                        <div>
                            <button class="annotate-btn" onclick="createSimilarityAnnotation(${c.id}, event)" ${disabled}>${btnText}</button>
                        </div>
                    </div>`;
                });
            }
            
            if (otherCandidates.length > 0) {
                html += `<div style="font-weight: bold; font-size: 11px; margin: 10px 0 5px 0; color: #ff9800;">⚠ Different Class (${otherCandidates.length})</div>`;
                otherCandidates.forEach(c => {
                    const disabled = c.alreadyAnnotated ? 'disabled' : '';
                    const btnText = c.alreadyAnnotated ? 'Annotated' : 'Mark Similar';
                    const previewClass = previewedCandidateId === c.id ? 'previewing' : '';
                    html += `<div class="candidate-item different-class ${previewClass}" onclick="togglePreviewCandidate(${c.id}, event)">
                        <div class="candidate-info">
                            <div class="candidate-label">${c.label}</div>
                            <div class="candidate-match">⚠ Different class</div>
                        </div>
                        <div>
                            <button class="annotate-btn" onclick="createSimilarityAnnotation(${c.id}, event)" ${disabled}>${btnText}</button>
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
                            <strong>${ann.label1}</strong> ↔ <strong>${ann.label2}</strong>
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

        function updateAnnotationLines() {
            // Remove existing annotation lines
            annotationLines.forEach(line => {
                scene.remove(line);
                line.geometry.dispose();
                line.material.dispose();
            });
            annotationLines = [];
            
            if (!annotationMode) return;
            
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

        function updateBoundingBoxes() {
            bboxes.forEach(bbox => {
                const objId = bbox.userData.objectId;
                if (objId === selectedObjectId && annotationMode) {
                    // Selected object in annotation mode - show in purple
                    bbox.material.color.setHex(0x9c27b0);
                    bbox.material.opacity = 1.0;
                    scene.add(bbox);
                } else if (objId === selectedObjectId) {
                    // Selected object in normal mode - show in green
                    bbox.material.color.setHex(0x00ff00);
                    bbox.material.opacity = 1.0;
                    scene.add(bbox);
                } else if (objId === previewedCandidateId && annotationMode) {
                    // Previewed candidate - show in blue
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
            if (!sceneGraphData || !sceneGraphData.relationships || objectId === null) {
                container.innerHTML = 'Select an object to view its relationships';
                return;
            }

            // Find relationships where this object is the subject or recipient
            let outgoing = sceneGraphData.relationships.filter(rel => rel.subject_id === objectId);
            let incoming = sceneGraphData.relationships.filter(rel => 
                rel.recipient_id && rel.recipient_id.includes(objectId)
            );
            
            // Apply relationship type filters
            if (selectedRelTypeFilters.size > 0) {
                outgoing = outgoing.filter(rel => selectedRelTypeFilters.has(rel.name));
                incoming = incoming.filter(rel => selectedRelTypeFilters.has(rel.name));
            }

            if (outgoing.length === 0 && incoming.length === 0) {
                const msg = selectedRelTypeFilters.size > 0 
                    ? '<div style="color: #999; font-size: 12px;">No relationships match the selected filters</div>'
                    : '<div style="color: #999; font-size: 12px;">No relationships found</div>';
                container.innerHTML = msg;
                return;
            }

            let html = '';
            
            // Show filter status if filters are active
            if (selectedRelTypeFilters.size > 0) {
                const totalOutgoing = sceneGraphData.relationships.filter(rel => rel.subject_id === objectId).length;
                const totalIncoming = sceneGraphData.relationships.filter(rel => 
                    rel.recipient_id && rel.recipient_id.includes(objectId)
                ).length;
                const totalDisplayed = outgoing.length + incoming.length;
                const totalAll = totalOutgoing + totalIncoming;
                
                html += `<div style="padding: 8px; font-size: 11px; color: #666; background: #f0f0f0; border-radius: 3px; margin-bottom: 8px;">
                    Showing ${totalDisplayed} of ${totalAll} relationships
                </div>`;
            }
            
            if (outgoing.length > 0) {
                html += '<div style="font-weight: bold; margin-bottom: 5px; font-size: 12px;">Outgoing:</div>';
                outgoing.forEach(rel => {
                    const targetIds = rel.recipient_id || [];
                    targetIds.forEach(targetId => {
                        const targetObj = sceneGraphData.objects.find(o => o.id === targetId);
                        const targetLabel = targetObj ? (targetObj.labels[0] || `Object ${targetId}`) : `Object ${targetId}`;
                        let style = '';
                        if (highlightedObjectIds.has(targetId)) {
                            const color = highlightedObjectIds.get(targetId);
                            style = `style="background: ${color.css}; color: white; font-weight: bold; border: 2px solid ${color.border}; padding: 2px 6px; border-radius: 3px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);"`;
                        }
                        html += `<div class="relationship-item">
                            <span class="rel-name">${rel.name}</span> → 
                            <span class="rel-target" ${style} onclick="highlightRelatedObject(${targetId})">${targetLabel}</span>
                        </div>`;
                    });
                });
            }

            if (incoming.length > 0) {
                html += '<div style="font-weight: bold; margin: 10px 0 5px 0; font-size: 12px;">Incoming:</div>';
                incoming.forEach(rel => {
                    const sourceObj = sceneGraphData.objects.find(o => o.id === rel.subject_id);
                    const sourceLabel = sourceObj ? (sourceObj.labels[0] || `Object ${rel.subject_id}`) : `Object ${rel.subject_id}`;
                    let style = '';
                    if (highlightedObjectIds.has(rel.subject_id)) {
                        const color = highlightedObjectIds.get(rel.subject_id);
                        style = `style="background: ${color.css}; color: white; font-weight: bold; border: 2px solid ${color.border}; padding: 2px 6px; border-radius: 3px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);"`;
                    }
                    html += `<div class="relationship-item">
                        <span class="rel-target" ${style} onclick="highlightRelatedObject(${rel.subject_id})">${sourceLabel}</span> → 
                        <span class="rel-name">${rel.name}</span>
                    </div>`;
                });
            }

            container.innerHTML = html;
        }

        function updateRelationshipLines() {
            // Remove existing relationship lines
            relationshipLines.forEach(line => {
                scene.remove(line);
                line.geometry.dispose();
                line.material.dispose();
            });
            relationshipLines = [];
            
            // Don't show lines in annotation mode or if no object selected
            if (annotationMode || selectedObjectId === null) {
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

        document.getElementById('annotation-mode').addEventListener('change', (e) => {
            annotationMode = e.target.checked;
            
            // Show/hide annotation UI
            document.getElementById('annotation-info').style.display = annotationMode ? 'block' : 'none';
            document.getElementById('export-annotations').style.display = annotationMode ? 'block' : 'none';
            
            // Show/hide relationship filters (hidden in annotation mode)
            const relFilters = document.getElementById('relationship-filters');
            if (relFilters) {
                relFilters.style.display = annotationMode ? 'none' : 'block';
            }
            
            // Update panel title
            const title = document.getElementById('relationships-title');
            if (title) {
                title.textContent = annotationMode ? 'Annotation Candidates' : 'Relationships';
            }
            
            if (annotationMode) {
                // Keep selection if any
                highlightedObjectIds.clear();
                showAnnotationCandidates(selectedObjectId);
                // Clear relationship lines in annotation mode
                updateRelationshipLines();
            } else {
                // Back to normal mode
                updateRelationshipsDisplay(selectedObjectId);
                // Restore relationship lines (only if objects are highlighted)
                updateRelationshipLines();
            }
            
            updateBoundingBoxes();
            updateAnnotationsDisplay();
            updateAnnotationLines();
        });

        document.getElementById('export-annotations').addEventListener('click', () => {
            if (similarityAnnotations.length === 0) {
                alert('No annotations to export');
                return;
            }
            
            const data = {
                scene_id: currentSceneId,
                annotations: similarityAnnotations,
                export_time: new Date().toISOString()
            };
            
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `similarity_annotations_${currentSceneId}.json`;
            a.click();
            URL.revokeObjectURL(url);
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
                div.textContent = sceneId;
                div.addEventListener('click', () => loadScene(sceneId));
                container.appendChild(div);
            });
        }

        async function loadScene(sceneId) {
            if (currentSceneId === sceneId) return;
            
            currentSceneId = sceneId;
            document.getElementById('loading').classList.remove('hidden');
            
            // Update selected scene in list
            document.querySelectorAll('.scene-item').forEach(item => {
                item.classList.toggle('selected', item.textContent === sceneId);
            });
            
            try {
                // Load scene graph
                const sgUrl = `data/scenegraphs/scannet/${sceneId}/scene_graph.json`;
                const sgResponse = await fetch(sgUrl);
                const sgText = await sgResponse.text();
                sceneGraphData = JSON.parse(sgText);
                
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
                
                // Load point cloud - try various naming patterns
                const plyUrls = [
                    `data/scannet/public/v2/scans/${sceneId}/${sceneId}_vh_clean.ply`,
                    `data/scannet/public/v2/scans/${sceneId}/${sceneId}_vh_clean_2.ply`,
                    `data/scannet/public/v2/scans/${sceneId}/${sceneId}_vh_clean_2.labels.ply`
                ];
                let plyLoaded = false;
                
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
                
                if (!plyLoaded) {
                    console.error('Could not load PLY file from any location');
                    alert('Warning: Could not load point cloud. Bounding boxes will be shown, but no point cloud data.');
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


def generate_html(output_path="viewer.html", scene_graph_url=None, ply_url=None, 
                  scenegraph_base="data/scenegraphs/scannet"):
    """
    Generate the standalone HTML viewer file.
    
    Args:
        output_path: Path where to save the HTML file
        scene_graph_url: Optional URL/path to scene graph JSON (auto-loads if provided)
        ply_url: Optional URL/path to PLY file (auto-loads if provided)
        scenegraph_base: Base path to scene graph data directory
    """
    output_path = Path(output_path)
    
    # Get available scenes
    scenes = list_available_scenes(scenegraph_base)
    
    # Modify template
    template = HTML_TEMPLATE
    
    # Embed scene list as JavaScript array
    scenes_json = json.dumps(scenes)
    scenes_script = f'\n        availableScenes = {scenes_json};\n'
    
    # Insert scene list after global variables declaration
    global_vars_marker = '        let currentSceneId = null;\n\n        // Initialize Three.js'
    if global_vars_marker in template:
        template = template.replace(global_vars_marker, 
                                   global_vars_marker.replace('        let currentSceneId = null;',
                                                             f'        let currentSceneId = null;{scenes_script}'))
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
    print(f"Found {len(scenes)} available scenes")
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
    
    parser = argparse.ArgumentParser(description="Generate standalone HTML viewer for scene graphs")
    parser.add_argument(
        "--output", "-o",
        default="viewer.html",
        help="Output HTML file path (default: viewer.html)"
    )
    parser.add_argument(
        "--scene-graph-url",
        help="URL/path to scene graph JSON file (auto-loads when HTML is served via HTTP)"
    )
    parser.add_argument(
        "--ply-url",
        help="URL/path to PLY file (auto-loads when HTML is served via HTTP)"
    )
    
    args = parser.parse_args()
    generate_html(args.output, args.scene_graph_url, args.ply_url)

