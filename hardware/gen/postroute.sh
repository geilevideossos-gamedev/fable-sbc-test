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
# worst pad-to-pad skew of the three pairs (with 1.5 mm per via, and with vias counted as 0) and the worst copper that is
# not on a pad-to-pad path (stubs, loops) of the six lines.  A missing or non-numeric measurement counts as 999, never as 0.
usb_stat() { echo "$STATS" | grep -v "^worst" | grep -o "$1 [0-9.na]*" | sed "s/^$1 //" \
             | awk -v want="$2" '{ n++; if ($1 !~ /^[0-9.]+$/) bad = 1; else if ($1 + 0 > m) m = $1 + 0 } END { print (bad || n != want) ? 999 : m + 0 }'; }
measure()     { STATS=$(python3 gen/build_pcb.py stats "$HW" 2>/dev/null); }
max_skew()    { usb_stat "skew" 3; }
max_skew0()   { usb_stat "as 0:" 3; }
max_offpath() { usb_stat "off-path" 6; }

if [ "${USB_ONLY:-0}" = 1 ] && [ -s gen/work/base.kicad_pcb ]; then
    echo "== USB_ONLY: re-using gen/work/base.kicad_pcb"
else
    echo "== completing the autorouted board"
    settle "$MAX" || { echo "could not reach a clean board"; exit 1; }
    cp voxhub.kicad_pcb gen/work/base.kicad_pcb
fi
best=""; bestscore=999; bestskew=999
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
        measure; s=$(max_skew)
        if awk "BEGIN { exit !($s <= 0.30) }"; then break; fi
    done
    if [ "$ok" = 0 ]; then echo "  variant $v: not clean after length matching, discarded"; continue; fi
    measure; s=$(max_skew); s0=$(max_skew0); c=$(max_offpath)
    # the length of a via is an estimate, so a variant is judged by the worse of "1.5 mm per via" and "vias count 0"
    # (equal via counts on both lines of a pair make the two agree), and by copper off the path
    score=$(awk "BEGIN { m = $s; if ($s0 > m) m = $s0; if ($c > m) m = $c; print m }")
    echo "  variant $v: clean, worst USB pair skew $s mm (pad to pad), $s0 mm with vias counted as 0, off-path copper $c mm"
    if awk "BEGIN { exit !($score < $bestscore) }"; then
        bestscore=$score; bestskew=$(awk "BEGIN { print ($s > $s0) ? $s : $s0 }"); best=$v; cp voxhub.kicad_pcb gen/work/best.kicad_pcb
    fi
    if awk "BEGIN { exit !($score <= 0.5) }"; then break; fi      # matched whatever a via counts, and free of stubs
done
if [ -n "$best" ]; then
    cp gen/work/best.kicad_pcb voxhub.kicad_pcb; echo "== kept USB variant $best (worst skew $bestskew mm, score $bestscore mm)"
else
    cp gen/work/base.kicad_pcb voxhub.kicad_pcb; measure; bestskew=$(awk "BEGIN { a = $(max_skew); b = $(max_skew0); print (a > b) ? a : b }")
    echo "== no USB re-route variant reached a clean DRC, keeping the base routing (worst skew $bestskew mm)"
fi
cp gen/project_settings.json voxhub.kicad_pro
if awk "BEGIN { exit !($bestskew > 3.8) }"; then echo "USB pair skew above 3.8 mm (or not measurable)"; exit 1; fi
echo "clean"
