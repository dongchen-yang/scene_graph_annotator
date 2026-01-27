# Scene Graph Annotation Tool

- Open directly: **https://aspis.cmpt.sfu.ca/projects/lightgen/scene_graph_annotation/visualize_scannet_3rscan_10.html**. in a **incognito window**
- Pick a scene from **Scenes → Available Scenes** (ScanNet, MultiScan, 3RScan).

## UI at a glance
- **Left panel (Scenes):** choose scenes; quick camera controls reminder.
- **Center (Viewer):** 3D view with mesh/point cloud, bounding boxes, and relationship/annotation lines.
- **Right – Objects panel:** scene summary, attribute filter chips, per-object attributes with validation controls, stats bar, and object list.
- **Right – Relationships panel:** relationship filters, per-object relationships, add/validate controls, similarity annotations list.
- **Top-right controls (in viewer):** toggles for bounding boxes/mesh, point-size slider (for point clouds), and annotation mode buttons.

## Camera & display controls
- Mouse: left-drag = rotate, right-drag = pan, wheel = zoom.
- Check **Show All Bounding Boxes** to render every box; otherwise only selected/highlighted ones show.
- Toggle **Show Mesh** to hide/show the point cloud or mesh; adjust **Point Size** when viewing point clouds.

## Annotation modes
Select a mode under **Annotation Mode**. The mode also changes the Relationships panel title and available controls.

### Similarity mode
1) Click an object in the Objects list; its bounding box appears.
2) The right panel shows **Similar Object Candidates**. Click a candidate to highlight it in the viewer.
3) If the two are similar, click **Mark Similar**.

### Attribute mode
1) Select an object; its attributes appear in chips under it.
2) Mark each predicted attribute with ✓ (correct) or ✗ (incorrect). Click again to clear.
3) Add additional attributes: **+ Add attribute** → enter name → **Add**. Added items show dashed green styling and can be removed.
4) Stats bar (yellow strip) shows totals and counts of ✓, ✗, and added attributes.


### Relationship mode
1) Select an object; outgoing, incoming, and “in between” relationships display.
2) Validate each relationship with ✓ / ✗; click again to clear. Highlighting uses green/red backgrounds.
3) Add new relationships in **Add Relationship**: type predicate, choose target object, click **Add**. Added rows show dashed green borders and can be deleted.
4) Use the dot icon to highlight both subject and object boxes; relationship lines render between highlighted objects.

## Annotation & validation guidelines
- **Per-scene workflow:** (1) Load a scene and briefly orbit/zoom to understand the layout. (2) Toggle **Show All Bounding Boxes** if you need to see every box, then return to normal view. (3) Work object-by-object: validate attributes → validate/add relationships → check similarity candidates.
- **Attribute validation rules:** Attributes describe shape, size, material (mainly color), and functionality. Mark ✓ when accurate, ✗ when wrong, and add missing but observable attributes. If a predicted attribute is wrong, add the correct one. For floor and ceiling, you can ignore the attribute.
- **Relationship validation rules:** Verify spatial/topological relations. Mark ✓ when clearly true, ✗ when clearly false. If a relationship is false, add the correct one.
- **What counts as similar:** Same real-world class with matching shape, size, and material. If two boxes duplicate the same physical object in different positions, mark as similar. Also mark visually identical pairs that were put in different classes because of labeling errors.
- **Quality checks before export:** Scan the stats bars for coverage; use filters briefly to spot any missed items.


## Export
- After finish one scene, you need to export the annotation.
- Click **Export All Annotations** to download a single JSON containing similarity pairs, attribute validations/additions, and relationship validations/additions for the current scene.



## Filters
- **Objects → By Attribute:** choose attributes to show only matching objects; chips appear under the dropdown; **Clear Filters** resets.
- **Relationships → By Type:** filter relationship predicates; affects the lists and counts; **Clear Filters** resets.

## Selecting & highlighting
- Click an object card to select; selected box is green (or purple in similarity mode).
- Click a relationship target name to highlight that object and draw a line; repeated clicks toggle highlights.
- Use the small “both” button (square with two dots) in relationship rows to highlight both objects simultaneously.

## Exported JSON structure (single file)
- `scene_id`, `timestamp`, `annotation_type` (last active mode when exported, or `all`).
- `similarity`: `annotations` array and `summary.total`.
- `attributes`: predicted items with validation state, `added`, and summary counts.
- `relationships`: predicted items with validation state, `added`, and summary counts.

## Troubleshooting
- If the point cloud fails to load, the tool still shows bounding boxes; check data paths and filenames listed above.
- For large meshes, the viewer samples dense point clouds (>200k points) to keep interaction smooth.
- Reloading a scene clears all current annotations/validations for that scene.
