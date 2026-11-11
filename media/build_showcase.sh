#!/usr/bin/env bash
# Build the VoxHub showcase animation from the STEP files of this repository.
#
#   media/build_showcase.sh [work dir]          (default: media/work, not tracked by git)
#
# Needs: python3 with cadquery + pymupdf + pillow + numpy, Docker with kicad/kicad:9.0 (board textures),
#        Blender >= 4.2 (BLENDER=/path/to/blender), ffmpeg.
# Environment: SAMPLES (default 4, Cycles samples per pixel before denoising), THREADS, FRAMES="start end"
#
# Steps: 1. STEP -> GLB (board with all parts, enclosure assembly, every part model)
#        2. board surface textures from the KiCad layer plots
#        3. Blender (headless, Cycles on the CPU): 1260 frames 1920x1080 + one still of the exploded view
#        4. ffmpeg: H.264, 60 fps
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; ROOT="$(dirname "${HERE}")"
WORK="$(mkdir -p "${1:-${HERE}/work}" && cd "${1:-${HERE}/work}" && pwd)"
BLENDER="${BLENDER:-blender}"; SAMPLES="${SAMPLES:-4}"; THREADS="${THREADS:-0}"
read -r F0 F1 <<< "${FRAMES:-1 1260}"

echo "== 1/4 STEP -> GLB"
mkdir -p "${WORK}/models" "${WORK}/tex" "${WORK}/frames"
python3 "${HERE}/step_to_glb.py" "${ROOT}/hardware/outputs/voxhub_pcb.step" "${WORK}/pcb.glb" 0.03 0.3
python3 "${HERE}/step_to_glb.py" "${ROOT}/enclosure/voxhub_assembly.step" "${WORK}/enclosure.glb" 0.03 0.25
find "${ROOT}/hardware/3dmodels" -name '*.step' | sort | while read -r f; do
    python3 "${HERE}/step_to_glb.py" "${f}" "${WORK}/models/$(basename "${f%.step}").glb" 0.02 0.25 > /dev/null
done
echo "== 2/4 board textures"
python3 "${HERE}/make_pcb_texture.py" "${ROOT}" "${WORK}/tex" 32
echo "== 3/4 render (frames ${F0}..${F1}, ${SAMPLES} samples)"
"${BLENDER}" -b -P "${HERE}/render_showcase.py" -- --work "${WORK}" --out "${WORK}/frames" --start "${F0}" --end "${F1}" \
    --samples "${SAMPLES}" --threads "${THREADS}" | grep --line-buffered "showcase:"
"${BLENDER}" -b -P "${HERE}/render_showcase.py" -- --work "${WORK}" --still 10.4 "${HERE}/voxhub_exploded.png" --samples 96 \
    --threads "${THREADS}" | grep "showcase:" || true
echo "== 4/4 encode"
ffmpeg -y -loglevel error -framerate 60 -start_number 1 -i "${WORK}/frames/f%05d.png" -c:v libx264 -preset slow -crf 17 \
    -pix_fmt yuv420p -movflags +faststart -r 60 "${HERE}/voxhub_showcase.mp4"
ls -la "${HERE}/voxhub_showcase.mp4" "${HERE}/voxhub_exploded.png"
