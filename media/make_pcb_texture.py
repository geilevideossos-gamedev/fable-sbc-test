#!/usr/bin/env python3
"""Board surface textures for the showcase render, composed from KiCad layer plots.

usage: make_pcb_texture.py <repo root> <out dir> [px per mm]

The STEP export of the board is a plain green slab.  This script plots copper, solder mask, silkscreen
and the outline of both sides with kicad-cli (KiCad 10 in the Docker image voxhub-kicad:10.0, as in
hardware/build.sh), rasterises them with PyMuPDF and composes what the bare board looks like: green mask
over FR-4, lighter green over copper, gold (ENIG) where the mask is open, white silkscreen.

Writes board_F.png / board_B.png (colour) and board_F_metal.png / board_B_metal.png (1 = exposed gold).
Pixel (0, 0) is the board corner x = 0, y = 0 (KiCad coordinates, y pointing down).
"""
import os, subprocess, sys
import shutil
import numpy as np
import fitz                      # PyMuPDF
from PIL import Image

W_MM, H_MM = 100.0, 74.0         # board size (hardware/gen/build_pcb.py)
LAYERS = ["F.Cu", "F.Mask", "F.SilkS", "B.Cu", "B.Mask", "B.SilkS", "Edge.Cuts"]
IMG = os.environ.get("KICAD_IMAGE") or "voxhub-kicad:10.0"


def plot(root, work):
    os.makedirs(work, exist_ok=True)
    export = ("kicad-cli pcb export svg --mode-multi --layers %s --black-and-white --page-size-mode 2 "
              "--exclude-drawing-sheet --drill-shape-opt 2 -o %%s voxhub.kicad_pcb" % ",".join(LAYERS))
    if os.environ.get("KICAD_NATIVE") == "1":
        version = subprocess.run(["kicad-cli", "version"], check=True, capture_output=True, text=True).stdout.strip()
        if not version.startswith("10."):
            raise SystemExit("KICAD_NATIVE=1 needs KiCad 10, kicad-cli on the PATH is " + version)
        home = os.path.join(work, "kihome")
        cfg = os.path.join(home, ".config", "kicad", "10.0")
        os.makedirs(cfg, exist_ok=True)
        for t in ("fp-lib-table", "sym-lib-table"):
            shutil.copyfile(os.path.join("/usr/share/kicad/template", t), os.path.join(cfg, t))
        subprocess.run(["bash", "-c", export % (work + "/")], check=True, stdout=subprocess.DEVNULL,
                       cwd=os.path.join(root, "hardware"), env=dict(os.environ, HOME=home))
        return
    if not os.environ.get("KICAD_IMAGE"):
        quiet = dict(stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if subprocess.run(["docker", "image", "inspect", IMG], **quiet).returncode != 0:
            subprocess.run(["docker", "build", "-t", IMG, os.path.join(root, "hardware", "docker")], check=True)
    cmd = ("mkdir -p /tmp/kihome/.config/kicad/10.0 && cp /usr/share/kicad/template/fp-lib-table "
           "/usr/share/kicad/template/sym-lib-table /tmp/kihome/.config/kicad/10.0/ && "
           + export % "/plots/" + " && chown -R %d:%d /plots" % (os.getuid(), os.getgid()))
    subprocess.run(["docker", "run", "--rm", "-u", "0", "-e", "HOME=/tmp/kihome", "-v", root + ":/work:ro",
                    "-v", work + ":/plots", "-w", "/work/hardware", IMG, "bash", "-c", cmd],
                   check=True, stdout=subprocess.DEVNULL)


def raster(svg, ppmm):
    """SVG layer plot -> boolean array (True = ink), cropped to the 100 x 74 mm board."""
    doc = fitz.open(svg)
    page = doc[0]
    w_mm, h_mm = page.rect.width * 25.4 / 72, page.rect.height * 25.4 / 72
    # KiCad 10 makes the page the bounding box of the board outline, so pixel (0, 0) is the board corner
    if abs(w_mm - W_MM) > 0.1 or abs(h_mm - H_MM) > 0.1:
        raise SystemExit("%s: the page is %.3f x %.3f mm, not the %g x %g mm board" % (svg, w_mm, h_mm, W_MM, H_MM))
    zoom = ppmm * 25.4 / 72
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), colorspace=fitz.csGRAY, alpha=False)
    a = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width)
    a = a[:int(round(H_MM * ppmm)), :int(round(W_MM * ppmm))]
    out = np.zeros((int(round(H_MM * ppmm)), int(round(W_MM * ppmm))), bool)
    out[:a.shape[0], :a.shape[1]] = a < 128
    return out


def compose(cu, mask, silk, ppmm):
    h, w = cu.shape
    rgb = np.zeros((h, w, 3), np.float32)
    green_fr4, green_cu = np.array([0.020, 0.150, 0.075]), np.array([0.045, 0.290, 0.130])
    gold, fr4, white = np.array([0.86, 0.70, 0.33]), np.array([0.50, 0.43, 0.24]), np.array([0.93, 0.93, 0.90])
    rgb[:] = green_fr4
    rgb[cu] = green_cu
    rgb[mask & ~cu] = fr4            # mask opening without copper
    rgb[mask & cu] = gold            # exposed pads
    rgb[silk & ~mask] = white
    # a hint of weave / unevenness so that large mask areas do not look like flat paint
    yy, xx = np.mgrid[0:h, 0:w]
    weave = 0.012 * (np.sin(xx * 2 * np.pi / (0.45 * ppmm)) * np.sin(yy * 2 * np.pi / (0.45 * ppmm)))
    rgb += (weave[..., None] * (~(mask & cu))[..., None]).astype(np.float32)
    metal = (mask & cu)
    return np.clip(rgb, 0, 1), metal


def main(root, out, ppmm=32.0):
    root, out = os.path.abspath(root), os.path.abspath(out)
    work = os.path.join(out, "plots")
    plot(root, work)
    lay = {}
    for name in LAYERS:
        f = os.path.join(work, "voxhub-%s.svg" % name.replace(".", "_").replace("SilkS", "Silkscreen"))
        lay[name] = raster(f, ppmm)
    for side in "FB":
        rgb, metal = compose(lay[side + ".Cu"], lay[side + ".Mask"], lay[side + ".SilkS"], ppmm)
        Image.fromarray((rgb ** (1 / 2.2) * 255).astype(np.uint8)).save(os.path.join(out, "board_%s.png" % side))
        Image.fromarray((metal * 255).astype(np.uint8)).save(os.path.join(out, "board_%s_metal.png" % side))
    print("textures written to", out, "(%d x %d px)" % (int(W_MM * ppmm), int(H_MM * ppmm)))


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 else 32.0)
