#!/usr/bin/env python3
"""Convert STEP assemblies to binary glTF (GLB) for Blender, keeping the assembly tree, names and colours.

usage: step_to_glb.py <in.step> <out.glb> [linear deflection mm] [angular deflection rad]

Uses the OpenCascade XCAF reader / glTF writer that ships with CadQuery (pip install cadquery).
The GLB is written in metres with glTF's Y-up convention; Blender's importer turns that back into the
STEP axes (Z up), so one STEP millimetre becomes 0.001 Blender units.
"""
import sys
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString, TCollection_AsciiString
from OCP.XCAFDoc import XCAFDoc_DocumentTool
from OCP.TDF import TDF_LabelSequence
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.RWGltf import RWGltf_CafWriter
from OCP.RWMesh import RWMesh_CoordinateSystem
from OCP.TColStd import TColStd_IndexedDataMapOfStringString
from OCP.Message import Message_ProgressRange
from OCP.IFSelect import IFSelect_RetDone


def convert(src, dst, lin=0.05, ang=0.35):
    doc = TDocStd_Document(TCollection_ExtendedString("XmlOcaf"))
    reader = STEPCAFControl_Reader()
    reader.SetColorMode(True); reader.SetNameMode(True); reader.SetLayerMode(True)
    if reader.ReadFile(src) != IFSelect_RetDone:
        raise SystemExit("cannot read " + src)
    reader.Transfer(doc)
    tool = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    free = TDF_LabelSequence(); tool.GetFreeShapes(free)
    for i in range(1, free.Length() + 1):
        BRepMesh_IncrementalMesh(tool.GetShape_s(free.Value(i)), lin, False, ang, True)
    writer = RWGltf_CafWriter(TCollection_AsciiString(dst), True)
    conv = writer.ChangeCoordinateSystemConverter()            # STEP: millimetres, Z up  ->  glTF: metres, Y up
    conv.SetInputLengthUnit(0.001); conv.SetInputCoordinateSystem(RWMesh_CoordinateSystem.RWMesh_CoordinateSystem_Zup)
    conv.SetOutputLengthUnit(1.0); conv.SetOutputCoordinateSystem(RWMesh_CoordinateSystem.RWMesh_CoordinateSystem_glTF)
    if not writer.Perform(doc, TColStd_IndexedDataMapOfStringString(), Message_ProgressRange()):
        raise SystemExit("glTF export failed for " + src)
    print("%s -> %s (%d root shape(s))" % (src, dst, free.Length()))


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    convert(sys.argv[1], sys.argv[2], *(float(a) for a in sys.argv[3:5]))
