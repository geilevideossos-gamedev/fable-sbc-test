#!/usr/bin/env bash
# Runs inside the KiCad container: complete + repair the autorouted board until DRC is clean.
#   postroute.sh <hardware dir> [max rounds]
set -u
HW="$1"; MAX="${2:-30}"
cd "$HW"
RPT=gen/work/drc_iter.rpt
BAD="clearance|shorting_items|tracks_crossing|hole_clearance|hole_to_hole|copper_edge_clearance|track_dangling|via_dangling|items_not_allowed|solder_mask_bridge|track_width"

settle() {      # iterate DRC -> repair -> patch until clean; returns 0 when clean
    local i unc err sig seen=""
    for i in $(seq 1 "$1"); do
        rm -f "$RPT"
        kicad-cli pcb drc --schematic-parity --severity-all --format report -o "$RPT" voxhub.kicad_pcb >/dev/null 2>&1
        [ -s "$RPT" ] || { echo "  DRC did not run"; return 1; }      # never judge by the report of an earlier round
        unc=$(grep -c "^\[unconnected_items\]" "$RPT")
        err=$(grep -c -E "^\[($BAD)\]" "$RPT")
        echo "  round $i: unconnected=$unc repairable_violations=$err"
        if [ "$unc" = 0 ] && [ "$err" = 0 ]; then return 0; fi
        # the loop is deterministic: the very same list of violations a second time means it will not get any further
        # (equal counts alone do not: the repair often removes one item per round for many rounds and then converges)
        sig=$(grep -E "^\[|^ +@\(" "$RPT" | sort | cksum | cut -d" " -f1)
        case " $seen " in *" $sig "*) echo "  no progress - giving up on this attempt"; return 1 ;; esac
        seen="$seen $sig"
        if [ "$err" != 0 ]; then python3 gen/build_pcb.py repair "$HW" "$RPT" 2>&1 | grep "^repair"; fi
        python3 gen/build_pcb.py patch "$HW" 2>&1 | grep -E "FAILED|^patch"
    done
    return 1
}
echo "== completing the autorouted board"
settle "$MAX" || { echo "could not reach a clean board"; exit 1; }
cp gen/project_settings.json voxhub.kicad_pro
python3 gen/build_pcb.py stats "$HW" > /dev/null || { echo "USB pairs not matched or not traceable pad to pad"; exit 1; }
echo "clean"
