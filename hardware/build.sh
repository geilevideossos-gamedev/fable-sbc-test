#!/usr/bin/env bash
# Regenerate the complete hardware package from code.
#
#   hardware/build.sh [all|sch|pcb|route|outputs]
#
# Needs: docker (KiCad 9 image), python3, Java >= 21 + freerouting-2.0.1.jar for the "route" step.
#   KICAD_IMAGE   docker image with KiCad 9 (default kicad/kicad:9.0)
#   FREEROUTING   path to freerouting jar (default ./freerouting-2.0.1.jar, see hardware/README.md)
#   SKIP_ROUTE=1  re-use the checked-in autorouter session gen/routed/voxhub.ses (reproducible result)
set -euo pipefail
HW="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "${HW}")"
IMG="${KICAD_IMAGE:-kicad/kicad:9.0}"
FR="${FREEROUTING:-${HW}/freerouting-2.0.1.jar}"
STEP="${1:-all}"
kc() {   # run a command inside the KiCad container, repo mounted at /work
    docker run --rm -u 0 -e HOME=/tmp/kihome -v "${ROOT}:/work" -w /work/hardware "${IMG}" bash -c \
        "mkdir -p /tmp/kihome/.config/kicad/9.0 && cp /usr/share/kicad/template/fp-lib-table /usr/share/kicad/template/sym-lib-table /tmp/kihome/.config/kicad/9.0/ && $*"
}
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
    #    patch router until KiCad's DRC is clean, 4) add the local power pours.
    if [ "${SKIP_ROUTE:-0}" = 1 ] && [ -s "${HW}/gen/routed/voxhub.ses" ]; then
        echo "re-using gen/routed/voxhub.ses"
    else
        (cd "${HW}/gen/work" && java -Djava.awt.headless=true -jar "${FR}" -de voxhub.dsn -do voxhub.ses \
            --router.job_timeout=00:06:00 -mt 1 --gui.enabled=false -da)
        mkdir -p "${HW}/gen/routed" && cp "${HW}/gen/work/voxhub.ses" "${HW}/gen/routed/voxhub.ses"
    fi
    cp "${HW}/gen/routed/voxhub.ses" "${HW}/gen/work/voxhub.ses"
    # always start from a fresh placement so that this step is repeatable
    kc "python3 gen/build_pcb.py place gen/work/voxhub.net /work/hardware && python3 gen/build_pcb.py finish /work/hardware \
        && gen/postroute.sh /work/hardware 30 && python3 gen/build_pcb.py pours /work/hardware"
}
outputs() {
    kc "kicad-cli pcb drc --schematic-parity --severity-all --exit-code-violations --format report -o outputs/drc.rpt voxhub.kicad_pcb; \
        rm -rf outputs/gerbers && mkdir -p outputs/gerbers \
        && kicad-cli pcb export gerbers -o outputs/gerbers/ --layers F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts --subtract-soldermask --no-protel-ext voxhub.kicad_pcb \
        && kicad-cli pcb export drill -o outputs/gerbers/ --format excellon --excellon-separate-th --generate-map --map-format gerberx2 --drill-origin absolute voxhub.kicad_pcb \
        && kicad-cli pcb export pos -o outputs/voxhub_pos.csv --format csv --units mm --side both --exclude-dnp voxhub.kicad_pcb \
        && kicad-cli pcb export dxf -o outputs/voxhub_outline.dxf --layers Edge.Cuts,User.Drawings,F.CrtYd,B.CrtYd --output-units mm --mode-single voxhub.kicad_pcb \
        && kicad-cli pcb export pdf -o outputs/pcb_layers --layers F.Cu,In1.Cu,In2.Cu,B.Cu,F.SilkS,B.SilkS,F.Fab,B.Fab,Edge.Cuts --mode-multipage voxhub.kicad_pcb \
        && kicad-cli pcb export step -o outputs/voxhub_pcb.step --subst-models --no-dnp --force voxhub.kicad_pcb \
        && kicad-cli pcb render -o outputs/render_top.png --side top --width 2000 --height 1500 --quality high voxhub.kicad_pcb \
        && kicad-cli pcb render -o outputs/render_bottom.png --side bottom --width 2000 --height 1500 --quality high voxhub.kicad_pcb \
        && kicad-cli pcb render -o outputs/render_iso.png --rotate '-55,0,25' --zoom 0.9 --width 2000 --height 1500 --quality high voxhub.kicad_pcb"
    # track / via statistics incl. the USB pair lengths, and the DRC once more with the waived checks switched on
    kc "python3 gen/build_pcb.py stats /work/hardware 2>/dev/null | grep -v '^$' > outputs/routing_stats.txt; \
        python3 -c \"import json; d = json.load(open('gen/project_settings.json')); s = d['board']['design_settings']['rule_severities']; \
[s.__setitem__(k, 'warning') for k in ('silk_edge_clearance', 'silk_over_copper', 'silk_overlap', 'footprint_type_mismatch', 'lib_footprint_mismatch')]; \
json.dump(d, open('voxhub.kicad_pro', 'w'), indent=2)\" \
        && kicad-cli pcb drc --schematic-parity --severity-all --format report -o outputs/drc_waived_checks_enabled.rpt voxhub.kicad_pcb; \
        cp gen/project_settings.json voxhub.kicad_pro"
    python3 "${HW}/gen/make_bom.py" "${HW}/gen/model_netlist.json" "${OUT}"
    (cd "${OUT}" && rm -f voxhub_gerbers.zip && zip -q -r voxhub_gerbers.zip gerbers)
}
case "${STEP}" in
    sch) sch ;; pcb) pcb ;; route) route ;; outputs) outputs ;;
    all) sch; pcb; route; outputs ;;
    *) echo "usage: $0 [all|sch|pcb|route|outputs]"; exit 2 ;;
esac
