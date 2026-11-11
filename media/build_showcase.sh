#!/usr/bin/env bash
# Build the VoxHub showcase animation from the STEP files of this repository.
#
#   media/build_showcase.sh [work dir]          (default: media/work, not tracked by git)
#
# Needs: python3 with cadquery + pymupdf + pillow + numpy, Docker with kicad/kicad:9.0 (board textures),
#        Blender 4.2 - 4.5 (BLENDER=/path/to/blender; 5.x has a different animation API and is refused), ffmpeg.
# Environment: SAMPLES (default 4, Cycles samples per pixel before denoising), THREADS, FRAMES="start end"
#
# Steps: 1. STEP -> GLB (board with all parts, enclosure assembly, every part model)
#        2. board surface textures from the KiCad layer plots
#        3. Blender (headless, Cycles on the CPU): 1260 frames 1920x1080 + one still of the exploded view
#        4. ffmpeg: H.264, 60 fps, BT.709
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; ROOT="$(dirname "${HERE}")"
WORK="$(mkdir -p "${1:-${HERE}/work}" && cd "${1:-${HERE}/work}" && pwd)"
BLENDER="${BLENDER:-blender}"; SAMPLES="${SAMPLES:-4}"; THREADS="${THREADS:-0}"
read -r F0 F1 <<< "${FRAMES:-1 1260}"
for t in python3 docker ffmpeg "${BLENDER}"; do      # ffmpeg is only needed after hours of rendering: check everything first
    command -v "${t}" > /dev/null || { echo "missing tool: ${t}" >&2; exit 1; }
done

echo "== 1/4 STEP -> GLB"
mkdir -p "${WORK}/models" "${WORK}/tex" "${WORK}/frames"
# Finished frames are reused when a render is restarted - but only while the inputs are the same.  After a change to
# the board, the enclosure, a part model, these scripts or SAMPLES the old frames are thrown away.
FP="$( { cat "${ROOT}/hardware/voxhub.kicad_pcb" "${ROOT}/hardware/outputs/voxhub_pcb.step" "${ROOT}/enclosure/voxhub_assembly.step" \
             "${HERE}"/*.py "${HERE}/build_showcase.sh"; find "${ROOT}/hardware/3dmodels" -name '*.step' -print0 | sort -z | xargs -0 cat; \
         echo "${SAMPLES}"; } | sha256sum | cut -d' ' -f1)"
if [ "$(cat "${WORK}/frames/.inputs" 2>/dev/null || true)" != "${FP}" ]; then
    n="$(find "${WORK}/frames" -name 'f*.png' | wc -l)"
    [ "${n}" = 0 ] || echo "inputs changed since the last render: discarding ${n} old frames"
    rm -f "${WORK}/frames"/f*.png
    echo "${FP}" > "${WORK}/frames/.inputs"
fi
python3 "${HERE}/step_to_glb.py" "${ROOT}/hardware/outputs/voxhub_pcb.step" "${WORK}/pcb.glb" 0.03 0.3
python3 "${HERE}/step_to_glb.py" "${ROOT}/enclosure/voxhub_assembly.step" "${WORK}/enclosure.glb" 0.03 0.25
find "${ROOT}/hardware/3dmodels" -name '*.step' | sort | while read -r f; do
    python3 "${HERE}/step_to_glb.py" "${f}" "${WORK}/models/$(basename "${f%.step}").glb" 0.02 0.25 > /dev/null
done
echo "== 2/4 board textures"
python3 "${HERE}/make_pcb_texture.py" "${ROOT}" "${WORK}/tex" 32
echo "== 3/4 render (frames ${F0}..${F1}, ${SAMPLES} samples)"
# --python-exit-code: without it Blender returns 0 even if the script raised
"${BLENDER}" -b --python-exit-code 1 -P "${HERE}/render_showcase.py" -- --work "${WORK}" --out "${WORK}/frames" \
    --start "${F0}" --end "${F1}" --samples "${SAMPLES}" --threads "${THREADS}" | grep --line-buffered "showcase:"
"${BLENDER}" -b --python-exit-code 1 -P "${HERE}/render_showcase.py" -- --work "${WORK}" --still 10.4 "${HERE}/voxhub_exploded.png" \
    --samples 96 --threads "${THREADS}" | grep "showcase:"
echo "== 4/4 encode"
for f in $(seq "${F0}" "${F1}"); do
    [ -s "${WORK}/frames/$(printf 'f%05d.png' "${f}")" ] || { echo "missing frame ${f}" >&2; exit 1; }
done
# the PNGs are sRGB; convert with the BT.709 matrix and tag the stream, otherwise players guess (and HD players guess 709
# for data that swscale wrote as 601 by default - the board would come out too dark a green)
ffmpeg -y -loglevel error -framerate 60 -start_number "${F0}" -i "${WORK}/frames/f%05d.png" -c:v libx264 -preset slow -crf 17 \
    -vf scale=out_color_matrix=bt709:out_range=tv -pix_fmt yuv420p -colorspace bt709 -color_primaries bt709 -color_trc bt709 \
    -movflags +faststart -r 60 "${HERE}/voxhub_showcase.mp4"
ls -la "${HERE}/voxhub_showcase.mp4" "${HERE}/voxhub_exploded.png"
