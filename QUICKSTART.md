# Quick Start Guide

## Setup (One-time)

### 1. Generate the Viewer

```bash
python generate_html.py
```

This creates `viewer.html` with all available scenes embedded.

### 2. Start HTTP Server

```bash
python -m http.server 8000
```

### 3. Open in Browser

Go to: `http://localhost:8000/viewer.html`

**Important:** You must use an HTTP server. Opening `viewer.html` directly with `file://` won't work due to browser security restrictions.

---

## Basic Usage

### Exploring Scenes

1. **Select a Scene**: Click any scene in the left panel
2. **View Auto-loads**: Point cloud and scene graph load automatically
3. **Browse Objects**: See all objects listed in the Objects panel

### Viewing Relationships

1. **Click an Object**: Select from the Objects panel
2. **See Relationships**: Displayed in the Relationships panel
3. **Visualize Connection**: Click on any related object name
   - A colored line appears between them
   - Both bounding boxes highlight
   - Click again to remove

### Filtering

**Filter Objects:**
- Select attributes from the "Filter Objects" dropdown
- Objects without selected attributes are hidden
- Click × on chips to remove filters

**Filter Relationships:**
- Select types from the "Filter Relationships" dropdown
- Only matching relationships shown
- Examples: "above", "below", "on", etc.

### 3D Controls

| Action | Control |
|--------|---------|
| Rotate | Left-click + drag |
| Pan | Right-click + drag |
| Zoom | Mouse wheel |

### Toggle Options

- ☑️ **Show All Bounding Boxes**: See all object boxes at once
- ☑️ **Show Mesh**: Toggle 3D model visibility
- 🔧 **Point Size**: Adjust size (point cloud mode only)

---

## Annotation Mode

Mark objects that are similar:

1. **Enable**: Check "Annotation Mode" in controls
2. **Select Object**: Click from Objects panel
3. **View Candidates**: Sorted by class similarity
4. **Mark Similar**: Click button next to candidate
5. **Export**: Save annotations as JSON

Annotations include object pairs, labels, and timestamps.

---

## Tips & Tricks

### Performance
- Large scenes auto-downsample for speed
- Use filters to focus on specific objects
- Meshes are faster than point clouds

### Workflow
```
1. Filter objects by attribute
   ↓
2. Select filtered object
   ↓
3. Filter relationships by type
   ↓
4. Click related objects to visualize
```

### Keyboard-free Navigation
- All controls accessible via mouse
- No keyboard shortcuts needed

---

## Troubleshooting

**Empty scene list?**
- Verify HTTP server is running
- Check `data/scenegraphs/scannet/` exists

**Point cloud not loading?**
- Ensure PLY files in `data/scannet/public/v2/scans/`
- Check browser console for errors

**Lines not appearing?**
- Ensure object is selected first
- Click related object names (not headers)

---

## Next Steps

📖 **Full Documentation**: See `README.md` for detailed features

🔧 **Customize**: Edit `generate_html.py` for custom paths

📊 **Data Format**: Check `README.md` for scene graph structure

---

## Alternative: Simple File Loading

If you don't have the full dataset structure:

1. Open `viewer.html` in browser (any method)
2. Use the "Load Files" section (if enabled)
3. Manually select scene graph JSON and PLY file

This won't have scene selection but works for single scenes.
