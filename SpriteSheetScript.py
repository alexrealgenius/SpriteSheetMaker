import os
import math
import bpy
import mathutils

folder_path = r""
collection_name = "LoadedSprites"

use_custom_grid = False  # Set to True to use custom dimensions, False for auto square
grid_size_x = 3         # Custom horizontal tile columns
grid_size_y = 3        # Custom vertical tile rows
# ---------------------------------------------

sprite_resolution = 128   # Each individual sprite cell resolution (px)
grid_total_size_x = 10.0  # Total horizontal width of the grid in Blender units

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"  # Every valid PNG file starts with these exact 8 bytes


def is_png(filepath):
    """Checks the file's actual header bytes rather than trusting its extension."""
    try:
        with open(filepath, "rb") as f:
            header = f.read(8)
        return header == PNG_SIGNATURE
    except (IsADirectoryError, PermissionError, OSError):
        return False

# Clean up old collections and objects
if collection_name in bpy.data.collections:
    old_collection = bpy.data.collections[collection_name]
    for obj in list(old_collection.objects):
        mesh_data = obj.data if obj.type == 'MESH' else None
        materials = list(obj.data.materials) if mesh_data else []

        bpy.data.objects.remove(obj, do_unlink=True)
        if mesh_data and mesh_data.users == 0:
            bpy.data.meshes.remove(mesh_data)
        for mat in materials:
            if mat.users == 0:
                bpy.data.materials.remove(mat)

    for parent_coll in bpy.data.collections:
        if old_collection.name in parent_coll.children:
            parent_coll.children.unlink(old_collection)
    if old_collection.name in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.unlink(old_collection)

    bpy.data.collections.remove(old_collection)
    print(f"Removed existing '{collection_name}' collection and its contents.")

collection = bpy.data.collections.new(collection_name)
bpy.context.scene.collection.children.link(collection)

all_entries = sorted(os.listdir(folder_path))
png_files = [
    f for f in all_entries
    if os.path.isfile(os.path.join(folder_path, f)) and is_png(os.path.join(folder_path, f))
]
count = len(png_files)

# Determine final grid dimensions based on toggle
if not use_custom_grid:
    n = math.ceil(math.sqrt(count))
    if n % 2 != 0:
        n += 1
    final_cols = n
    final_rows = n
    print(f"Auto-Square Grid Toggle Active: Using a {final_cols}x{final_rows} layout.")
else:
    max_slots = grid_size_x * grid_size_y
    if count > max_slots:
        print(f"WARNING: Found {count} images, but your custom {grid_size_x}x{grid_size_y} grid only holds {max_slots}. Truncating list.")
        png_files = png_files[:max_slots]
        count = len(png_files)
    final_cols = grid_size_x
    final_rows = grid_size_y
    print(f"Custom Grid Toggle Active: Using a custom {final_cols}x{final_rows} layout.")

if count == 0:
    print("No PNG files found in", folder_path)
else:
    # Set matching render resolution and aspect ratios
    bpy.context.scene.render.resolution_x = final_cols * sprite_resolution
    bpy.context.scene.render.resolution_y = final_rows * sprite_resolution
    bpy.context.scene.render.resolution_percentage = 100
    bpy.context.scene.render.film_transparent = True
    bpy.context.scene.render.image_settings.file_format = 'PNG'
    bpy.context.scene.render.image_settings.color_mode = 'RGBA'

    # Compute spacing and size relative to horizontal constraints
    spacing = grid_total_size_x / final_cols
    plane_scale = spacing / 2.0

    # Grid centering math transforms
    offset_x = (final_cols - 1) * spacing / 2.0
    offset_z = (final_rows - 1) * spacing / 2.0

    loaded_images = []
    for index, file in enumerate(png_files):
        filepath = os.path.join(folder_path, file)
        img = bpy.data.images.load(filepath)
        loaded_images.append(img)

        row = index // final_cols
        col = index % final_cols
        x = col * spacing - offset_x
        z = -row * spacing + offset_z

        bpy.ops.mesh.primitive_plane_add(location=(x, 0, z))
        obj = bpy.context.active_object
        obj.name = img.name
        obj.rotation_euler.x = math.radians(90)
        obj.scale = (plane_scale, plane_scale, plane_scale)

        mat = bpy.data.materials.new(name=f"Mat_{img.name}")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        output_node = nodes.new("ShaderNodeOutputMaterial")
        tex_node = nodes.new("ShaderNodeTexImage")
        tex_node.image = img
        tex_node.interpolation = 'Closest'  # Prevents edge-bleeding
        
        emission_node = nodes.new("ShaderNodeEmission")
        emission_node.inputs["Strength"].default_value = 1.0
        transparent_node = nodes.new("ShaderNodeBsdfTransparent")
        mix_shader_node = nodes.new("ShaderNodeMixShader")

        links.new(tex_node.outputs["Color"], emission_node.inputs["Color"])
        links.new(tex_node.outputs["Alpha"], mix_shader_node.inputs["Fac"])
        links.new(transparent_node.outputs["BSDF"], mix_shader_node.inputs[1])
        links.new(emission_node.outputs["Emission"], mix_shader_node.inputs[2])
        links.new(mix_shader_node.outputs["Shader"], output_node.inputs["Surface"])

        mat.blend_method = 'CLIP'
        mat.alpha_threshold = 0.5
        if hasattr(mat, "shadow_method"):
            mat.shadow_method = 'CLIP'

        obj.data.materials.append(mat)

        for coll in obj.users_collection:
            coll.objects.unlink(obj)
        collection.objects.link(obj)

    print(f"Done. Placed {count} planes into the grid.")

    # Camera framing adjustment block
    for obj in list(bpy.data.objects):
        if obj.type == 'CAMERA':
            cam_data = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if cam_data.users == 0:
                bpy.data.cameras.remove(cam_data)

    cam_data = bpy.data.cameras.new("GridCamera")
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = grid_total_size_x

    cam_obj = bpy.data.objects.new("GridCamera", cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)

    # Calculate proportional backing depth
    cam_distance = grid_total_size_x * 3.0
    
    # Calculate perfect vertical centering bias for rectangular dimensions
    vertical_offset = 0.0
    if final_rows != final_cols:
        vertical_offset = ((final_cols - final_rows) * spacing) / 2.0
    
    cam_obj.location = (0.0, -cam_distance, -vertical_offset)

    grid_center = mathutils.Vector((0.0, 0.0, -vertical_offset))
    direction = grid_center - cam_obj.location
    cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

    bpy.context.scene.camera = cam_obj
    print(f"Camera 'GridCamera' successfully adjusted to match aspect ratios.")
