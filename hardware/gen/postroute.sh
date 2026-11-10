#!/usr/bin/env bash
# Runs inside the KiCad container: complete + repair the autorouted board until DRC is clean.
#   postroute.sh <hardware dir> [max rounds]
set -u
HW="$1"; MAX="${2:-25}"
cd "$HW"
RPT=gen/work/drc_iter.rpt
for i in $(seq 1 "$MAX"); do
    kicad-cli pcb drc --schematic-parity --severity-all --format report -o "$RPT" voxhub.kicad_pcb >/dev/null 2>&1
    unc=$(grep -c "^\[unconnected_items\]" "$RPT")
    err=$(grep -c -E "^\[(clearance|shorting_items|tracks_crossing|hole_clearance|hole_to_hole|copper_edge_clearance|track_dangling|via_dangling|items_not_allowed|solder_mask_bridge|track_width)\]" "$RPT")
    echo "round $i: unconnected=$unc repairable_violations=$err"
    if [ "$unc" = 0 ] && [ "$err" = 0 ]; then echo "clean"; exit 0; fi
    if [ "$err" != 0 ]; then
        python3 gen/build_pcb.py repair "$HW" "$RPT" 2>&1 | grep "^repair"
    fi
    python3 gen/build_pcb.py patch "$HW" 2>&1 | grep -E "FAILED|joined|^patch"
done
exit 1
