# Showcase animation

| File | What |
|---|---|
| `voxhub_showcase.mp4` | product animation, 1920 x 1080, 60 fps, 21 s (H.264) |
| `voxhub_exploded.png` | still of the exploded view (96 samples) |
| `render_showcase.py` | the Blender script: imports the models, builds materials, studio, camera path, animation and title, renders |
| `step_to_glb.py` | STEP -> GLB with OpenCascade (assembly tree, names and colours are kept) |
| `make_pcb_texture.py` | board surface textures (copper, solder mask, pads, silkscreen) from KiCad layer plots |
| `build_showcase.sh` | runs everything: conversion, textures, render, ffmpeg |

![exploded view](voxhub_exploded.png)

Status: `voxhub_exploded.png` shows the final board. `voxhub_showcase.mp4` was rendered a few hours earlier, before the
review moved 19 small parts (two ESD parts, capacitors at the buck regulator, a few resistors and LEDs) and re-routed the
board; at video scale the difference is not discernible, and the frames that show the PCB are being re-rendered (see
TODO.md).

## What you see

| Time | Shot |
|---|---|
| 0.0 - 2.5 s | closed device on a studio floor, soft area lights, slow camera move |
| 2.5 - 4.2 s | the device lifts off, the base plate drops away |
| 4.1 - 5.7 s | the upper half turns over - the PCB hangs component side down under the top plate, exactly as it is assembled |
| 5.7 - 7.1 s | PCB and speaker lift out of the shell |
| 6.9 - 8.6 s | CM4 with heat sink, stacked USB-A, USB-C, microSD socket and speaker header separate from the PCB |
| 8.6 - 13.6 s | slow orbit around the exploded PCB |
| 13.6 - 16.8 s | everything reassembles |
| 16.8 - 21.0 s | turntable shot of the closed device, "VoxHub" title |

## Where the geometry comes from

Only STEP files that the hardware and enclosure builds of this repository produce:

- `hardware/outputs/voxhub_pcb.step` - KiCad's export of the assembled board: position and reference of every part;
- `hardware/3dmodels/**/*.step` - the part models (KiCad library models and the coloured stand-ins written by
  `hardware/gen/make_3dmodels.py`). KiCad's board export drops model colours, so the script takes the geometry of each
  part from its own model file and only the placement from the board export;
- `enclosure/voxhub_assembly.step` - shell, base plate and speaker in their assembled position.

The board itself is a plain slab in STEP. Its copper, solder mask and silkscreen are a texture that
`make_pcb_texture.py` composes from KiCad's layer plots of the same board file, so traces and pads are the real layout.

## Rebuilding

```bash
pip install cadquery pymupdf pillow numpy
sudo apt install ffmpeg
docker pull kicad/kicad:9.0
BLENDER=/path/to/blender-4.5/blender media/build_showcase.sh      # frames go to media/work (not tracked)
```

Blender 4.2 to 4.5 is required (tested with 4.5.16 LTS; Blender 5 changed the animation API and the script refuses to
start there). Blender runs headless (`blender -b -P render_showcase.py -- ...`), Cycles on the CPU: 4 samples per pixel +
OpenImageDenoise, fixed noise seed, 3 bounces, no motion blur. Measured on 4 cores: about 11 s per frame, 3 h 10 min for
the 1260 frames (the committed video). The script always renders on the CPU (`cycles.device = "CPU"`), so raising
`SAMPLES` raises the render time proportionally. `render_showcase.py --stills 0,5,10 --scale 25` renders quick checks of
single moments, `--still <t> out.png` one frame, `--start / --end` a frame range. Finished frames are skipped (a frame
counts as finished when the PNG ends with its IEND chunk), so an interrupted render can simply be restarted;
`build_showcase.sh` refuses to encode while a frame is missing.

The MP4 is H.264 High, yuv420p, converted with the BT.709 matrix and tagged as such (limited range), `+faststart`.
