#!/usr/bin/env bash
# Regenerate the complete hardware package from code.
#
#   hardware/build.sh [all|sch|pcb|route|outputs]
#
# Needs: docker (KiCad 9 image), python3, zip, Java >= 21 + freerouting-2.0.1.jar for the "route" step.
#   KICAD_IMAGE   docker image with KiCad 9 (default kicad/kicad:9.0)
#   FREEROUTING   path to freerouting jar (default ./freerouting-2.0.1.jar, see hardware/README.md)
#   SKIP_ROUTE=1  re-use the checked-in autorouter session gen/routed/voxhub.ses (reproducible result)
set -euo pipefail
HW="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "${HW}")"
IMG="${KICAD_IMAGE:-kicad/kicad:9.0}"
FR="${FREEROUTING:-${HW}/freerouting-2.0.1.jar}"
STEP="${1:-all}"
case "${STEP}" in all|outputs) command -v zip > /dev/null || { echo "missing tool: zip" >&2; exit 1; } ;; esac
if [ "${KICAD_NATIVE:-0}" = 1 ]; then
    command -v kicad-cli > /dev/null || { echo "KICAD_NATIVE=1 needs kicad-cli (KiCad 9) on the PATH" >&2; exit 1; }
    NATIVE_HOME="$(mktemp -d)"; trap 'rm -rf "${NATIVE_HOME}"' EXIT
    mkdir -p "${NATIVE_HOME}/bin" "${NATIVE_HOME}/.config/kicad/9.0"
    cp /usr/share/kicad/template/fp-lib-table /usr/share/kicad/template/sym-lib-table "${NATIVE_HOME}/.config/kicad/9.0/"
    for py in "${KICAD_PYTHON:-}" python3 python3.12 python3.11; do
        [ -n "${py}" ] && "${py}" -c "import pcbnew, numpy, shapely" 2> /dev/null && { ln -s "$(command -v "${py}")" "${NATIVE_HOME}/bin/python3"; break; }
    done
    [ -e "${NATIVE_HOME}/bin/python3" ] || { echo "no python3 that can import pcbnew, numpy and shapely (set KICAD_PYTHON)" >&2; exit 1; }
    kc() {
        local cmd="${*//\/work\/hardware/${HW}}"
        (cd "${HW}" && HOME="${NATIVE_HOME}" PATH="${NATIVE_HOME}/bin:${PATH}" bash -c "${cmd//\/work\//${ROOT}/}")
    }
else
kc() {   # run a command inside the KiCad container, repo mounted at /work
    docker run --rm -u 0 -e HOME=/tmp/kihome -v "${ROOT}:/work" -w /work/hardware "${IMG}" bash -c \
        "mkdir -p /tmp/kihome/.config/kicad/9.0 && cp /usr/share/kicad/template/fp-lib-table /usr/share/kicad/template/sym-lib-table /tmp/kihome/.config/kicad/9.0/ && { python3 -c 'import shapely' 2> /dev/null || pip3 install -q --break-system-packages shapely; } && $*"
}
fi
OUT="${HW}/outputs"; mkdir -p "${OUT}" "${HW}/gen/work"

sch() {
    kc "KICAD_SYM_DIR=/usr/share/kicad/symbols python3 gen/design.py . && python3 gen/make_footprints.py voxhub.pretty \
        && kicad-cli sch erc --severity-all --exit-code-violations --format report -o outputs/erc.rpt voxhub.kicad_sch \
        && mkdir -p gen/work && kicad-cli sch export netlist --format kicadsexpr -o gen/work/voxhub.net voxhub.kicad_sch \
        && kicad-cli sch export pdf -o outputs/voxhub_schematic.pdf voxhub.kicad_sch"
}
pcb() {
    kc "python3 gen/build_pcb.py place gen/work/voxhub.net /work/hardware && python3 gen/build_pcb.py dsn /work/hardware --planes"
}
route() {
    # 1) autoroute the signals (Freerouting), 2) import + pour planes, 3) complete/repair with the
    #    patch router until KiCad's DRC is clean.
    if [ "${SKIP_ROUTE:-0}" = 1 ] && [ -s "${HW}/gen/routed/voxhub.ses" ]; then
        echo "re-using gen/routed/voxhub.ses"
    else
        # Freerouting 2.0.1 sometimes routes the board and then leaves an EMPTY session file behind (seen twice on a busy
        # machine, the passes in its log were identical to a good run).  The result is deterministic, so simply try again.
        # Each run gets its own temp directory: Freerouting keeps a freerouting.json there and re-reads it next time.
        local frtmp try
        for try in 1 2 3; do
            frtmp="$(mktemp -d)"
            (cd "${HW}/gen/work" && rm -f voxhub.ses && java -Djava.awt.headless=true -Djava.io.tmpdir="${frtmp}" -jar "${FR}" \
                -de voxhub.dsn -do voxhub.ses --router.job_timeout=00:20:00 -mt 1 --gui.enabled=false -da) || true
            rm -rf "${frtmp}"
            if grep -q "(wire" "${HW}/gen/work/voxhub.ses" 2>/dev/null; then break; fi
            echo "Freerouting wrote no routed session (attempt ${try} of 3)" >&2
        done
        grep -q "(wire" "${HW}/gen/work/voxhub.ses" 2>/dev/null || { echo "no autorouter session - giving up" >&2; exit 1; }
        mkdir -p "${HW}/gen/routed" && cp "${HW}/gen/work/voxhub.ses" "${HW}/gen/routed/voxhub.ses"
    fi
    grep -q "(wire" "${HW}/gen/routed/voxhub.ses" || { echo "gen/routed/voxhub.ses contains no routing" >&2; exit 1; }
    cp "${HW}/gen/routed/voxhub.ses" "${HW}/gen/work/voxhub.ses"
    # always start from a fresh placement so that this step is repeatable
    kc "python3 gen/build_pcb.py place gen/work/voxhub.net /work/hardware && python3 gen/build_pcb.py finish /work/hardware \
        && gen/postroute.sh /work/hardware 30"
}
outputs() {
    # the final DRC gates everything below: no Gerbers from a board with violations
    kc "kicad-cli pcb drc --schematic-parity --severity-all --exit-code-violations --format report -o outputs/drc.rpt voxhub.kicad_pcb \
        && rm -rf outputs/gerbers && mkdir -p outputs/gerbers \
        && kicad-cli pcb export gerbers -o outputs/gerbers/ --layers F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts --subtract-soldermask --no-x2 --no-netlist voxhub.kicad_pcb \
        && kicad-cli pcb export drill -o outputs/gerbers/ --format excellon --excellon-separate-th --excellon-zeros-format decimal --excellon-oval-format alternate --generate-map --map-format gerberx2 --drill-origin absolute voxhub.kicad_pcb \
        && kicad-cli pcb export pos -o outputs/voxhub_pos.csv --format csv --units mm --side both --exclude-dnp voxhub.kicad_pcb \
        && kicad-cli pcb export dxf -o outputs/voxhub_outline.dxf --layers Edge.Cuts,User.Drawings,F.CrtYd,B.CrtYd --output-units mm --mode-single voxhub.kicad_pcb \
        && kicad-cli pcb export pdf -o outputs/pcb_layers --layers F.Cu,In1.Cu,In2.Cu,B.Cu,F.SilkS,B.SilkS,F.Fab,B.Fab,Edge.Cuts --mode-multipage voxhub.kicad_pcb \
        && kicad-cli pcb export step -o outputs/voxhub_pcb.step --subst-models --no-dnp --force voxhub.kicad_pcb \
        && kicad-cli pcb render -o outputs/render_top.png --side top --width 2000 --height 1500 --quality high voxhub.kicad_pcb \
        && kicad-cli pcb render -o outputs/render_bottom.png --side bottom --width 2000 --height 1500 --quality high voxhub.kicad_pcb \
        && kicad-cli pcb render -o outputs/render_iso.png --rotate '-55,0,25' --zoom 0.9 --width 2000 --height 1500 --quality high voxhub.kicad_pcb"
    # track / via statistics incl. the USB pair lengths ("stats" fails if a pair is not matched or cannot be traced),
    # and the DRC once more with the waived checks switched on (the project file is put back in any case)
    kc "set -o pipefail; python3 gen/build_pcb.py stats /work/hardware | grep -v '^\$' > outputs/routing_stats.txt; rc=\$?; \
        python3 -c \"import json; d = json.load(open('gen/project_settings.json')); s = d['board']['design_settings']['rule_severities']; \
[s.__setitem__(k, 'warning') for k in ('footprint_type_mismatch', 'lib_footprint_mismatch')]; \
json.dump(d, open('voxhub.kicad_pro', 'w'), indent=2)\" \
        && kicad-cli pcb drc --schematic-parity --severity-all --format report -o outputs/drc_waived_checks_enabled.rpt voxhub.kicad_pcb || rc=1; \
        cp gen/project_settings.json voxhub.kicad_pro; cat outputs/routing_stats.txt; exit \$rc"
    kc "python3 gen/check_power.py voxhub.kicad_pcb outputs/power_paths.txt && python3 gen/check_df40.py voxhub.kicad_pcb outputs/df40_strips.txt \
        && python3 gen/check_vias.py voxhub.kicad_pcb outputs/via_in_pad.txt"
    python3 "${HW}/gen/make_bom.py" "${HW}/gen/model_netlist.json" "${OUT}"
    (cd "${OUT}" && rm -f voxhub_gerbers.zip && zip -q -r voxhub_gerbers.zip gerbers)
    mkdir -p "${ROOT}/fab/jlcpcb"
    (cd "${OUT}/gerbers" && rm -f "${ROOT}/fab/jlcpcb/gerbers.zip" && zip -q "${ROOT}/fab/jlcpcb/gerbers.zip" $(ls | grep -v -E 'gbrjob$|drl_map'))
    kc "python3 gen/make_jlc.py voxhub.kicad_pcb gen/sourcing_jlc.json gen/jlc_footprints.json /work/fab/jlcpcb"
}
case "${STEP}" in
    sch) sch ;; pcb) pcb ;; route) route ;; outputs) outputs ;;
    all) sch; pcb; route; outputs ;;
    *) echo "usage: $0 [all|sch|pcb|route|outputs]"; exit 2 ;;
esac
