# Sprite Sheet Maker

A Blender Python script that automatically imports valid PNG images from a folder, arranges them into a centered sprite grid, creates materials for each sprite, and configures an orthographic camera for rendering the completed sprite sheet.

## Features

* Automatically detects valid PNG files using their actual PNG header
* Imports all detected sprites from a selected folder
* Creates a dedicated `LoadedSprites` collection
* Removes previously generated sprite objects and materials before rebuilding
* Supports automatic square grid generation
* Supports manually configured rectangular grids
* Automatically calculates Blender render resolution from the grid size
* Uses nearest-neighbor texture interpolation to help prevent edge bleeding
* Creates transparent sprite materials with alpha clipping
* Uses emission materials so sprites are displayed without relying on scene lighting
* Automatically creates and positions an orthographic camera
* Centers sprites within the generated grid
* Enables transparent PNG rendering

## Requirements

* Blender with Python scripting support
* PNG sprite images

The script uses Blender's built-in Python API and does not require external Python packages.

## Setup

Open the script in Blender's **Scripting** workspace.

Set the folder containing your sprite images:

```python
folder_path = r"C:\Path\To\Your\Sprites"
```

For example:

```python
folder_path = r"C:\Users\User\Desktop\Sprites"
```

### Grid Configuration

The script supports two grid modes.

#### Automatic Square Grid

Set:

```python
use_custom_grid = False
```

The script automatically calculates a square grid large enough to contain the detected sprites.

#### Custom Grid

Set:

```python
use_custom_grid = True
grid_size_x = 3
grid_size_y = 3
```

This creates a 3 × 3 grid.

If more images are found than the custom grid can hold, the script truncates the image list to the available number of slots.

## Sprite Resolution

Each sprite cell defaults to:

```python
sprite_resolution = 128
```

This means each sprite occupies a 128 × 128 pixel area in the final render.

For example, a 4 × 4 grid produces:

```text
512 × 512 pixels
```

## Grid Size

The total horizontal grid width is controlled by:

```python
grid_total_size_x = 10.0
```

The script uses this value to calculate sprite spacing and automatically sets the orthographic camera scale.

## How It Works

The script performs the following process:

```text
Select sprite folder
       ↓
Find PNG files
       ↓
Verify PNG file headers
       ↓
Remove previous LoadedSprites collection
       ↓
Create new sprite collection
       ↓
Calculate grid dimensions
       ↓
Import sprite images
       ↓
Create planes and materials
       ↓
Arrange sprites in grid
       ↓
Configure render resolution
       ↓
Create orthographic camera
       ↓
Center camera on grid
       ↓
Ready for rendering
```

## Material Setup

Each imported sprite receives its own material.

The material uses:

* Image Texture
* Emission
* Transparent BSDF
* Mix Shader
* Alpha clipping

Textures use:

```python
tex_node.interpolation = 'Closest'
```

to preserve sharp sprite edges and reduce texture bleeding between pixels.

## Output

The script creates a Blender scene containing:

```text
LoadedSprites/
├── Sprite 1
├── Sprite 2
├── Sprite 3
└── ...
```

It also creates an orthographic camera named:

```text
GridCamera
```

The Blender scene is configured to render the sprite grid as a transparent PNG.

## Notes

The script currently expects the folder path to be configured manually through `folder_path`.

The generated collection and camera are rebuilt each time the script runs, making it convenient to regenerate the sprite sheet after changing the source images or grid settings.

## Example

Given 8 sprite images and:

```python
use_custom_grid = False
sprite_resolution = 128
```

the script automatically determines an appropriate square grid and creates a Blender scene ready to render.



## Author

Alexander Troshin
