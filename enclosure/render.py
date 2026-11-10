#!/usr/bin/env python3
"""Render preview images of the enclosure + PCB assembly (off-screen VTK).
usage: xvfb-run -a python3 render.py [outdir]"""
import os, sys
import cadquery as cq
import vtk
import voxhub_enclosure as E

def actor(shape, rgb, opacity=1.0):
    verts, tris = shape.val().tessellate(0.05, 0.3)
    pts = vtk.vtkPoints(); cells = vtk.vtkCellArray()
    for v in verts: pts.InsertNextPoint(v.x, v.y, v.z)
    for t in tris:
        cells.InsertNextCell(3)
        for i in t: cells.InsertCellPoint(i)
    pd = vtk.vtkPolyData(); pd.SetPoints(pts); pd.SetPolys(cells)
    n = vtk.vtkPolyDataNormals(); n.SetInputData(pd); n.SetFeatureAngle(40); n.SplittingOn(); n.Update()
    m = vtk.vtkPolyDataMapper(); m.SetInputConnection(n.GetOutputPort())
    a = vtk.vtkActor(); a.SetMapper(m)
    p = a.GetProperty(); p.SetColor(*rgb); p.SetOpacity(opacity); p.SetSpecular(0.25); p.SetSpecularPower(20); p.SetAmbient(0.35); p.BackfaceCullingOff()
    return a

def shot(actors, path, pos, focal, up=(0, 0, 1), size=(1600, 1100), parallel=None, clip=None):
    ren = vtk.vtkRenderer(); ren.SetBackground(1, 1, 1)
    for a in actors:
        if clip is not None:
            pl = vtk.vtkPlane(); pl.SetOrigin(*clip[0]); pl.SetNormal(*clip[1]); a.GetMapper().AddClippingPlane(pl)
        ren.AddActor(a)
    win = vtk.vtkRenderWindow(); win.SetOffScreenRendering(1); win.SetSize(*size); win.AddRenderer(ren); win.SetMultiSamples(8)
    cam = ren.GetActiveCamera(); cam.SetPosition(*pos); cam.SetFocalPoint(*focal); cam.SetViewUp(*up)
    if parallel: cam.ParallelProjectionOn()
    ren.ResetCamera(); cam.Zoom(1.35 if not parallel else 1.2); ren.ResetCameraClippingRange()
    win.Render()
    w2i = vtk.vtkWindowToImageFilter(); w2i.SetInput(win); w2i.Update()
    wr = vtk.vtkPNGWriter(); wr.SetFileName(path); wr.SetInputConnection(w2i.GetOutputPort()); wr.Write()
    for a in actors: a.GetMapper().RemoveAllClippingPlanes()

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(E.HERE, "renders")
    os.makedirs(out, exist_ok=True)
    shell, base = E.make_shell(), E.make_base()
    pcb, parts, spk = E.make_pcb_assembly()
    LED_Y = E.LEDS[0][1] if E.LEDS else 71.2
    cx, cy, cz = (E.X0 + E.X1) / 2, (E.Y0 + E.Y1) / 2, (E.Z_TOP_OUT + E.Z_BOTTOM) / 2
    A = dict(shell=actor(shell, (0.92, 0.92, 0.94)), base=actor(base, (0.30, 0.30, 0.33)), pcb=actor(pcb, (0.05, 0.42, 0.20)),
             parts=actor(parts, (0.72, 0.72, 0.75)), spk=actor(spk, (0.15, 0.15, 0.16)))
    # 1 closed device, seen from the rear (connector side)
    shot([A["shell"], A["base"], A["pcb"], A["parts"], A["spk"]], os.path.join(out, "enclosure_rear.png"), (cx + 60, -260, 170), (cx, cy, cz))
    # 2 closed device from the front/top (grille, mic ports, mute slider)
    shot([A["shell"], A["base"]], os.path.join(out, "enclosure_front.png"), (cx - 80, 300, 200), (cx, cy, cz))
    # 3 base removed, looking up into the shell at the PCB assembly
    shot([A["shell"], A["pcb"], A["parts"], A["spk"]], os.path.join(out, "enclosure_open_bottom.png"), (cx + 70, -150, -300), (cx, cy, cz), up=(0, -1, 0))
    # 4 cross-section through the microphone / LED row and through the CM4
    shot(list(A.values()), os.path.join(out, "section_front_row.png"), (cx, -400, cz + 60), (cx, 71.0, cz), clip=((0, LED_Y, 0), (0, 1, 0)), parallel=True)
    shot(list(A.values()), os.path.join(out, "section_cm4.png"), (cx, -400, cz + 60), (cx, 48.0, cz), clip=((0, 48.0, 0), (0, 1, 0)), parallel=True)
    # 5 transparent top view: PCB inside the shell
    A["shell"].GetProperty().SetOpacity(0.35)
    shot([A["shell"], A["pcb"], A["parts"], A["spk"], A["base"]], os.path.join(out, "fit_top_transparent.png"), (cx, cy - 1, 400), (cx, cy, 0), up=(0, -1, 0), parallel=True)
    print("renders written to", out)
