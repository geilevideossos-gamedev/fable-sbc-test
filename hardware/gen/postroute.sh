#!/usr/bin/env bash
# Runs inside the KiCad container: complete + repair the autorouted board until DRC is clean,
# then re-route the USB 2.0 pairs and length-match them with serpentines (several net orders are tried,
# the best matched result is kept).
#   postroute.sh <hardware dir> [max rounds]
set -u
HW="$1"; MAX="${2:-30}"
cd "$HW"
RPT=gen/work/drc_iter.rpt
BAD="clearance|shorting_items|tracks_crossing|hole_clearance|hole_to_hole|copper_edge_clearance|track_dangling|via_dangling|items_not_allowed|solder_mask_bridge|track_width"

settle() {      # iterate DRC -> repair -> patch until clean; returns 0 when clean
    local i unc err
    for i in $(seq 1 "$1"); do
        kicad-cli pcb drc --schematic-parity --severity-all --format report -o "$RPT" voxhub.kicad_pcb >/dev/null 2>&1
        unc=$(grep -c "^\[unconnected_items\]" "$RPT")
        err=$(grep -c -E "^\[($BAD)\]" "$RPT")
        echo "  round $i: unconnected=$unc repairable_violations=$err"
        if [ "$unc" = 0 ] && [ "$err" = 0 ]; then return 0; fi
        if [ "$err" != 0 ]; then python3 gen/build_pcb.py repair "$HW" "$RPT" 2>&1 | grep "^repair"; fi
        python3 gen/build_pcb.py patch "$HW" 2>&1 | grep -E "FAILED|^patch"
    done
    return 1
}
max_skew()   { python3 gen/build_pcb.py stats "$HW" 2>/dev/null | grep -v "^worst" | grep -o "skew [0-9.]*" | awk '{ if ($2 > m) m = $2 } END { print m + 0 }'; }
max_cudiff() { python3 gen/build_pcb.py stats "$HW" 2>/dev/null | grep -o "copper-diff [0-9.]*" | awk '{ if ($2 > m) m = $2 } END { print m + 0 }'; }

if [ "${USB_ONLY:-0}" = 1 ] && [ -s gen/work/base.kicad_pcb ]; then
    echo "== USB_ONLY: re-using gen/work/base.kicad_pcb"
else
    echo "== completing the autorouted board"
    settle "$MAX" || { echo "could not reach a clean board"; exit 1; }
    cp voxhub.kicad_pcb gen/work/base.kicad_pcb
fi
best=""; bestscore=999
for v in 0 1 2 3 4 5; do
    echo "== USB re-route, net order variant $v"
    cp gen/work/base.kicad_pcb voxhub.kicad_pcb
    python3 gen/build_pcb.py patch "$HW" --reroute-usb --variant "$v" 2>&1 | grep -E "FAILED|^patch"
    if ! settle 12; then echo "  variant $v: not clean, discarded"; continue; fi
    # serpentine length matching of the shorter line of each pair; a DRC-driven repair may undo a
    # meander, so tune -> settle is repeated until the pairs stay matched
    ok=1
    for r in 1 2 3; do
        python3 gen/build_pcb.py tune "$HW" 2>&1 | grep "^tune" | sed 's/^/  /'
        if ! settle 12; then ok=0; break; fi
        s=$(max_skew)
        if awk "BEGIN { exit !($s <= 0.30) }"; then break; fi
    done
    if [ "$ok" = 0 ]; then echo "  variant $v: not clean after length matching, discarded"; continue; fi
    s=$(max_skew); c=$(max_cudiff)
    score=$(awk "BEGIN { print ($s > $c) ? $s : $c }")
    echo "  variant $v: clean, worst USB pair skew $s mm (pad to pad), copper difference $c mm"
    if awk "BEGIN { exit !($score < $bestscore) }"; then bestscore=$score; best=$v; cp voxhub.kicad_pcb gen/work/best.kicad_pcb; fi
    if awk "BEGIN { exit !($score <= 2.0) }"; then break; fi      # comfortably inside the 3.8 mm guideline
done
if [ -n "$best" ]; then
    cp gen/work/best.kicad_pcb voxhub.kicad_pcb; echo "== kept USB variant $best (worst of skew / copper difference: $bestscore mm)"
else
    cp gen/work/base.kicad_pcb voxhub.kicad_pcb; echo "== no clean USB re-route found, keeping the autorouter's USB tracks"
fi
cp gen/project_settings.json voxhub.kicad_pro
if awk "BEGIN { exit !($bestscore > 3.8) }"; then echo "USB pair skew above 3.8 mm"; exit 1; fi
echo "clean"
