# Quick Start Guide

## Option 1: Standalone HTML (No Installation Needed!)

1. **Just open `viewer.html` in your browser**
   - Double-click the file, or
   - Right-click > Open with > Browser

2. **Load your files:**
   - Click "Scene Graph JSON" and select your `scene_graph.json` file
   - Click "Point Cloud PLY" and select your `.ply` file

That's it! No server, no installation required.

## Option 2: Web Server (Optional)

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start the server:
```bash
python run_server.py
```

3. Open your browser to:
```
http://localhost:5000
```

## Using the Interface

1. **Select a Scene**: Use the dropdown at the top to select a scene (e.g., `scene0000_00`)

2. **View Scene Information**: The sidebar shows:
   - Number of objects
   - Number of relationships
   - Number of attributes

3. **Browse Objects**: Click on any object in the list to highlight its bounding box in the 3D view

4. **3D Controls**:
   - **Mouse drag**: Rotate the camera
   - **Mouse wheel**: Zoom in/out
   - **Show/Hide**: Use checkboxes to toggle point cloud and bounding boxes

5. **Object Highlighting**: Click an object in the sidebar to highlight it (green bounding box)

## Features

- ✅ Interactive 3D visualization using Three.js
- ✅ Point cloud rendering with colors
- ✅ Bounding box visualization with rotations
- ✅ Object selection and highlighting
- ✅ Scene graph data browsing
- ✅ Web-based (easy to deploy)

## Deployment

For production deployment, consider using:
- **Gunicorn** for production WSGI server
- **Nginx** as reverse proxy
- Environment variables for configuration

Example with Gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

