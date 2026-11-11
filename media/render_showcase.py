"""VoxHub CM4 showcase animation - Blender scene, animation and render script (headless).

    blender -b -P render_showcase.py -- --work <dir> --out <frames dir> [--start N --end N] [--still T out.png]
                                        [--samples N] [--scale PCT] [--threads N] [--save scene.blend]

<work> is prepared by build_showcase.sh and holds
    pcb.glb          hardware/outputs/voxhub_pcb.step          (KiCad board export: placement of every part)
    enclosure.glb    enclosure/voxhub_assembly.step            (shell, base, speaker)
    models/*.glb     hardware/3dmodels/**/*.step               (coloured part models)
    tex/board_*.png  board surface textures from the KiCad layer plots (make_pcb_texture.py)

Timeline (60 fps, 21 s = 1260 frames):
     0.0 -  2.5 s   closed device on a studio floor, slow camera move
     2.5 -  4.2 s   the device lifts off, the base plate drops away
     4.1 -  5.7 s   the upper half turns over (it is assembled upside down: the PCB hangs under the top plate)
     5.7 -  7.1 s   PCB and speaker lift out of the shell
     6.9 -  8.6 s   CM4 with heat sink and the connectors separate from the PCB
     8.6 - 13.6 s   slow orbit around the exploded PCB
    13.6 - 16.8 s   everything reassembles
    16.8 - 21.0 s   turntable shot of the closed device, "VoxHub" title fades in
"""
import bpy, bmesh, sys, os, math, glob, re, colorsys
from mathutils import Vector, Matrix

FPS = 60
DURATION = 21.0
MM = 0.001

# --------------------------------------------------------------------------------------- arguments
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def arg(name, default=None, cast=str):
    return cast(argv[argv.index(name) + 1]) if name in argv else default
WORK = os.path.abspath(arg("--work", "work"))
OUT = os.path.abspath(arg("--out", os.path.join(WORK, "frames")))
START, END = arg("--start", 1, int), arg("--end", int(DURATION * FPS), int)
SAMPLES = arg("--samples", 4, int)
SCALE = arg("--scale", 100, int)
THREADS = arg("--threads", 0, int)
STILL = (float(argv[argv.index("--still") + 1]), argv[argv.index("--still") + 2]) if "--still" in argv else None
SAVE = arg("--save")
STEP = arg("--step", 1, int)
SHEET = arg("--stills")                 # "t1,t2,..." -> <out>/still_<t>.png (for checking the choreography)

# --------------------------------------------------------------------------------------- helpers
def F(t):
    return 1 + t * FPS

def import_glb(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    return [o for o in bpy.data.objects if o not in before]

def new_empty(name, loc=(0, 0, 0), parent=None):
    e = bpy.data.objects.new(name, None)
    e.empty_display_size = 0.01
    bpy.context.scene.collection.objects.link(e)
    e.location = loc
    if parent is not None:
        e.parent = parent
    return e

def reparent(obj, parent):
    """Parent obj to parent, keeping its world transform."""
    bpy.context.view_layer.update()
    mw = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_parent_inverse = parent.matrix_world.inverted()
    obj.matrix_world = mw

def base_name(n):
    return re.sub(r"\.\d{3}$", "", n)

def bbox(mesh):
    xs = [v.co for v in mesh.vertices]
    lo = Vector((min(v.x for v in xs), min(v.y for v in xs), min(v.z for v in xs)))
    hi = Vector((max(v.x for v in xs), max(v.y for v in xs), max(v.z for v in xs)))
    return lo, hi

def key(obj, path, values, index=-1):
    """Insert keyframes.  values: (time s, value) or (time s, value, interpolation, easing) - the interpolation
    applies to the segment that starts at this key."""
    frames = {}
    for kv in values:
        t, v = kv[0], kv[1]
        if index >= 0:
            cur = list(getattr(obj, path)); cur[index] = v; setattr(obj, path, cur)
        else:
            setattr(obj, path, v)
        obj.keyframe_insert(path, index=index, frame=F(t))
        frames[round(F(t), 3)] = kv[2:] if len(kv) > 2 else ("BEZIER", "AUTO")
    for fc in obj.animation_data.action.fcurves:
        if fc.data_path == path and (index < 0 or fc.array_index == index):
            for kp in fc.keyframe_points:
                opt = frames.get(round(kp.co.x, 3))
                if opt is None: continue
                kp.interpolation, kp.easing = opt
                kp.handle_left_type = kp.handle_right_type = "AUTO_CLAMPED"
            fc.update()

# --------------------------------------------------------------------------------------- materials
def principled(name, color, rough=0.5, metal=0.0, spec=0.5, coat=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if "Specular IOR Level" in b.inputs: b.inputs["Specular IOR Level"].default_value = spec
    if coat and "Coat Weight" in b.inputs:
        b.inputs["Coat Weight"].default_value = coat; b.inputs["Coat Roughness"].default_value = 0.15
    return m

def tune_imported_material(m):
    """Part models only carry a colour.  Decide from the colour what the surface is made of."""
    if not m.use_nodes: return
    b = m.node_tree.nodes.get("Principled BSDF")
    if b is None: return
    r, g, bl, _ = b.inputs["Base Color"].default_value
    h, s, v = colorsys.rgb_to_hsv(r, g, bl)
    gold = 0.08 < h < 0.17 and s > 0.35 and v > 0.55
    grey_metal = s < 0.12 and 0.45 < v < 0.88
    if gold:
        b.inputs["Metallic"].default_value = 1.0; b.inputs["Roughness"].default_value = 0.28
    elif grey_metal:
        b.inputs["Metallic"].default_value = 1.0; b.inputs["Roughness"].default_value = 0.32
        b.inputs["Base Color"].default_value = (min(1, r * 1.08), min(1, g * 1.08), min(1, bl * 1.08), 1)
    elif v < 0.2:
        b.inputs["Metallic"].default_value = 0.0; b.inputs["Roughness"].default_value = 0.42
    else:
        b.inputs["Metallic"].default_value = 0.0; b.inputs["Roughness"].default_value = 0.5
    m.use_backface_culling = False

def board_material(tex):
    """Solder mask / copper / silkscreen from the KiCad plots, mapped by object coordinates (board = STEP frame)."""
    m = bpy.data.materials.new("board"); m.use_nodes = True
    nt = m.node_tree; N = nt.nodes; L = nt.links
    bsdf = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping")
    # STEP frame (m): x = 0.100 .. 0.200, y = -0.134 .. -0.060  ->  u, v = 0 .. 1 (image row 0 = board y 0)
    mp.inputs["Scale"].default_value = (1 / 0.100, 1 / 0.074, 1.0)
    mp.inputs["Location"].default_value = (-1.0, 0.134 / 0.074, 0.0)
    L.new(tc.outputs["Object"], mp.inputs["Vector"])
    def img(fn, noncolor=False):
        n = N.new("ShaderNodeTexImage")
        n.image = bpy.data.images.load(os.path.join(tex, fn))
        n.extension = "EXTEND"; n.interpolation = "Cubic"
        if noncolor: n.image.colorspace_settings.name = "Non-Color"
        L.new(mp.outputs["Vector"], n.inputs["Vector"])
        return n
    cf, cb, mf, mb = img("board_F.png"), img("board_B.png"), img("board_F_metal.png", True), img("board_B_metal.png", True)
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Normal"], sep.inputs["Vector"])
    def gt(sign):
        mt = N.new("ShaderNodeMath"); mt.operation = "GREATER_THAN"; mt.inputs[1].default_value = 0.5
        if sign < 0:
            neg = N.new("ShaderNodeMath"); neg.operation = "MULTIPLY"; neg.inputs[1].default_value = -1.0
            L.new(sep.outputs["Z"], neg.inputs[0]); L.new(neg.outputs[0], mt.inputs[0])
        else:
            L.new(sep.outputs["Z"], mt.inputs[0])
        return mt
    top, bot = gt(+1), gt(-1)
    def mix(fac, a, b, color=True):
        n = N.new("ShaderNodeMix"); n.data_type = "RGBA" if color else "FLOAT"
        L.new(fac, n.inputs["Factor"])
        ia, ib = (n.inputs[6], n.inputs[7]) if color else (n.inputs[2], n.inputs[3])
        if isinstance(a, tuple): ia.default_value = a
        elif isinstance(a, float): ia.default_value = a
        else: L.new(a, ia)
        if isinstance(b, float): ib.default_value = b
        else: L.new(b, ib)
        return n.outputs[2] if color else n.outputs[0]
    edge = (0.42, 0.36, 0.20, 1.0)
    col = mix(bot.outputs[0], mix(top.outputs[0], edge, cf.outputs["Color"]), cb.outputs["Color"])
    met = mix(bot.outputs[0], mix(top.outputs[0], 0.0, mf.outputs["Color"], False), mb.outputs["Color"], False)
    hsv = N.new("ShaderNodeHueSaturation"); hsv.inputs["Saturation"].default_value = 1.15; hsv.inputs["Value"].default_value = 0.62
    L.new(col, hsv.inputs["Color"])
    L.new(hsv.outputs["Color"], bsdf.inputs["Base Color"])
    L.new(met, bsdf.inputs["Metallic"])
    rough = N.new("ShaderNodeMapRange"); rough.inputs["To Min"].default_value = 0.34; rough.inputs["To Max"].default_value = 0.24
    L.new(met, rough.inputs["Value"]); L.new(rough.outputs[0], bsdf.inputs["Roughness"])
    return m

def speaker_material():
    """Speaker solid from the enclosure assembly: black basket, zinc-plated yoke (split by height, device frame)."""
    m = bpy.data.materials.new("speaker"); m.use_nodes = True
    nt = m.node_tree; N = nt.nodes; L = nt.links
    bsdf = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs["Vector"])
    lt = N.new("ShaderNodeMath"); lt.operation = "LESS_THAN"; lt.inputs[1].default_value = (4.0 - 11.25) * MM
    L.new(sep.outputs["Z"], lt.inputs[0])
    mixc = N.new("ShaderNodeMix"); mixc.data_type = "RGBA"
    mixc.inputs[6].default_value = (0.02, 0.02, 0.022, 1); mixc.inputs[7].default_value = (0.72, 0.73, 0.75, 1)
    L.new(lt.outputs[0], mixc.inputs["Factor"]); L.new(mixc.outputs[2], bsdf.inputs["Base Color"])
    L.new(lt.outputs[0], bsdf.inputs["Metallic"])
    bsdf.inputs["Roughness"].default_value = 0.38
    return m

# --------------------------------------------------------------------------------------- scene
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.fps = FPS
scene.frame_start, scene.frame_end = 1, int(DURATION * FPS)
scene.unit_settings.scale_length = 1.0

# ---- part models (coloured STEP -> GLB): one joined mesh per model, in the model's own frame
MODELS = {}
for path in sorted(glob.glob(os.path.join(WORK, "models", "*.glb"))):
    objs = import_glb(path)
    names = [o.name for o in objs]
    meshes = [o for o in objs if o.type == "MESH"]
    if not meshes:
        continue
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes: o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    for o in meshes:                                    # bake node transforms into the mesh data
        o.data = o.data.copy()
    bpy.context.view_layer.update()
    if len(meshes) > 1:
        bpy.ops.object.join()
    j = bpy.context.view_layer.objects.active
    mw = j.matrix_world.copy()
    j.data.transform(mw)
    j.data.name = "MODEL_" + os.path.splitext(os.path.basename(path))[0]
    j.data.use_fake_user = True
    MODELS[os.path.splitext(os.path.basename(path))[0]] = j.data
    for n in names:
        if n in bpy.data.objects:
            bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)
for m in bpy.data.materials:
    tune_imported_material(m)

# ---- board with all parts (KiCad STEP export).  STEP frame -> device frame: x - 100, -y - 60, -z (mm)
pcb_objs = import_glb(os.path.join(WORK, "pcb.glb"))
ALIGN = Matrix.Translation((-0.100, -0.060, 0.0)) @ Matrix.Rotation(math.pi, 4, "X")
bpy.context.view_layer.update()
for o in pcb_objs:
    if o.parent is None:
        o.matrix_world = ALIGN @ o.matrix_world
bpy.context.view_layer.update()
pcb_objs = [o for o in pcb_objs]

fallback = {
    "ic": principled("fb_ic", (0.03, 0.03, 0.032), 0.4), "metal": principled("fb_metal", (0.82, 0.82, 0.84), 0.3, 1.0),
    "cap": principled("fb_cap", (0.50, 0.36, 0.22), 0.5), "res": principled("fb_res", (0.06, 0.06, 0.07), 0.45),
    "white": principled("fb_white", (0.9, 0.9, 0.86), 0.45),
}
def fallback_for(ref, model):
    if ref.startswith(("J", "H", "Y", "MK", "TP")): return fallback["metal"]
    if ref.startswith("C"): return fallback["cap"]
    if ref.startswith("R"): return fallback["res"]
    if "LED" in model: return fallback["white"]
    return fallback["ic"]

def collapse(e):
    """A part whose model is a STEP assembly arrives as an empty with one mesh per solid: join them into one object."""
    meshes = [c for c in e.children_recursive if c.type == "MESH"]
    if not meshes:
        return None
    name, parent, mw = e.name, e.parent, e.matrix_world.copy()
    doomed = [c.name for c in e.children_recursive if c.type != "MESH"] + [e.name]
    bpy.ops.object.select_all(action="DESELECT")
    for c in meshes:
        c.data = c.data.copy(); c.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    j = bpy.context.view_layer.objects.active
    j.data.transform(mw.inverted() @ j.matrix_world)
    j.parent = parent; j.matrix_parent_inverse = Matrix.Identity(4)
    if parent is not None:
        j.matrix_parent_inverse = parent.matrix_world.inverted()
    j.matrix_world = mw
    for n in doomed:
        if n in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)
    j.name = name
    return j

pcb_root = next(o for o in pcb_objs if o.parent is None)
MODEL_BOX = {k: bbox(v) for k, v in MODELS.items()}
board = None
parts = {}            # reference -> object
n_swapped = 0
for o in list(pcb_root.children):
    if o.type == "EMPTY":
        o = collapse(o)
        if o is None: continue
    model = base_name(o.data.name)
    if model.lower().endswith("_pcb"):
        board = o
        continue
    ref = base_name(o.name)
    parts[ref] = o
    lo, hi = bbox(o.data)
    def fits(k):
        lo2, hi2 = MODEL_BOX[k]
        return (lo - lo2).length < 0.25 * MM and (hi - hi2).length < 0.25 * MM
    cand = [model] if model in MODELS and fits(model) else [k for k in sorted(MODELS) if fits(k)]
    if cand:
        o.data = MODELS[cand[0]]; n_swapped += 1
    else:
        o.data.materials.clear(); o.data.materials.append(fallback_for(ref, model))
print("showcase: %d parts on the board, %d with coloured models" % (len(parts), n_swapped))
board.data.materials.clear(); board.data.materials.append(board_material(os.path.join(WORK, "tex")))

# ---- enclosure assembly: shell, base, speaker (its PCB stand-ins are dropped)
enc = {base_name(o.name): o for o in import_glb(os.path.join(WORK, "enclosure.glb")) if o.type == "MESH"}
for n in ("pcb", "components"):
    if n in enc: bpy.data.objects.remove(enc.pop(n), do_unlink=True)
shell, base, speaker = enc["shell"], enc["base"], enc["speaker"]
for o, mat in ((shell, principled("shell", (0.80, 0.80, 0.775), 0.40, 0.0, 0.5)),
               (base, principled("base", (0.035, 0.036, 0.04), 0.46, 0.0, 0.5)),
               (speaker, speaker_material())):
    o.data.materials.clear(); o.data.materials.append(mat)

# ---- hierarchy (device frame, metres: PCB bare side = z 0, top plate above, parts hang below)
CX, CY = 30.8 * MM, 37.0 * MM                       # centre of the enclosure footprint
Z_BOTTOM, Z_TOP = -22.0 * MM, 6.0 * MM
DEVICE = new_empty("DEVICE")
TURN = new_empty("TURN", loc=(CX, CY, 0.0)); reparent(TURN, DEVICE)                 # turntable axis = device centre
BASEG = new_empty("BASE", loc=(CX, CY, 0.0)); reparent(BASEG, TURN)
UPPER = new_empty("UPPER", loc=(CX, CY, -8.0 * MM)); reparent(UPPER, TURN)          # pivot of the turn-over
PCBG = new_empty("PCB", loc=(CX, CY, 0.0)); reparent(PCBG, UPPER)
SPKG = new_empty("SPEAKER", loc=(CX, CY, 0.0)); reparent(SPKG, UPPER)
reparent(base, BASEG); reparent(shell, UPPER); reparent(speaker, SPKG); reparent(board, PCBG)
GROUPS = {"CM4": ["J2", "J3"], "USBA": ["J6"], "USBC": ["J1"], "SD": ["J4"], "JST": ["J7"]}
SUB = {}
for g in GROUPS:
    SUB[g] = new_empty(g, loc=(CX, CY, 0.0)); reparent(SUB[g], PCBG)
for ref, o in parts.items():
    grp = next((g for g, refs in GROUPS.items() if ref in refs), None)
    reparent(o, SUB[grp] if grp else PCBG)
for o in list(bpy.data.objects):                    # empties left over from the imports
    if o.type == "EMPTY" and o.parent is None and o is not DEVICE and not o.children:
        bpy.data.objects.remove(o, do_unlink=True)
DEVICE.location = (-CX, -CY, -Z_BOTTOM)             # device centred on the world origin, standing on the floor
bpy.context.view_layer.update()

# --------------------------------------------------------------------------------------- animation
T_LIFT, T_DROP, T_FLIP0, T_FLIP1 = 2.5, 2.9, 4.1, 5.7
T_OUT0, T_OUT1, T_SEP0, T_SEP1 = 5.7, 7.1, 6.9, 8.6
T_ORB0, T_ORB1 = 8.6, 13.6
T_RE0, T_RE1, T_RE2, T_RE3, T_END_RE = 13.6, 14.5, 15.4, 16.3, 16.8
LIFT = 62 * MM                                         # hover height of the upper half while it is open

# whole upper half: rises, turns over, comes back
uz = UPPER.location.z
key(UPPER, "location", [(0, uz), (T_LIFT, uz), (T_LIFT + 1.2, uz + LIFT), (T_FLIP1, uz + LIFT - 24 * MM), (T_OUT1, uz + LIFT - 34 * MM),
                        (T_RE2, uz + LIFT - 34 * MM), (T_RE3, uz + LIFT - 8 * MM), (T_END_RE, uz)], index=2)
key(UPPER, "rotation_euler", [(0, 0.0), (T_FLIP0, 0.0), (T_FLIP1, math.pi), (T_RE2 - 0.1, math.pi), (T_RE3, 0.0)], index=0)
# base plate: goes up with the device, then drops back to the floor and waits there
key(BASEG, "location", [(0, 0.0), (T_LIFT, 0.0), (T_DROP + 0.25, 30 * MM), (T_DROP + 0.5, 34 * MM, "BOUNCE", "EASE_OUT"),
                        (T_DROP + 1.25, 0.0), (T_END_RE, 0.0)], index=2)
# PCB and speaker leave the shell through its open side (local -z; after the flip that is "up")
key(PCBG, "location", [(0, 0.0), (T_OUT0, 0.0), (T_OUT1, -54 * MM), (T_RE1, -54 * MM), (T_RE2, 0.0)], index=2)
key(SPKG, "location", [(0, 0.0), (T_OUT0 + 0.2, 0.0), (T_OUT1 + 0.2, -30 * MM), (T_RE1, -30 * MM), (T_RE2, 0.0)], index=2)
sx0 = SPKG.location.x
key(SPKG, "location", [(0, sx0), (T_OUT0 + 0.2, sx0), (T_OUT1 + 0.2, sx0 - 14 * MM), (T_RE1, sx0 - 14 * MM), (T_RE2, sx0)], index=0)
# parts leave the PCB one after the other
SEP = {"CM4": (0.0, -34 * MM, 0.0), "USBA": (0.2, -15 * MM, -20 * MM), "USBC": (0.35, -20 * MM, -16 * MM),
       "SD": (0.5, -12 * MM, -14 * MM), "JST": (0.65, -16 * MM, 0.0)}
for g, (delay, dz, dy) in SEP.items():
    e = SUB[g]
    t0, t1 = T_SEP0 + delay, T_SEP0 + delay + 1.0
    r0, r1 = T_RE0 + (0.65 - delay) * 0.5, T_RE0 + (0.65 - delay) * 0.5 + 0.75
    key(e, "location", [(0, 0.0), (t0, 0.0), (t1, dz), (r0, dz), (r1, 0.0)], index=2)
    if dy:
        y0 = e.location.y
        key(e, "location", [(0, y0), (t0, y0), (t1, y0 + dy), (r0, y0 + dy), (r1, y0)], index=1)
# turntable at the end
key(TURN, "rotation_euler", [(0, 0.0), (T_END_RE - 0.3, 0.0), (DURATION + 0.6, math.radians(-300))], index=2)

# --------------------------------------------------------------------------------------- studio
world = bpy.data.worlds.new("studio"); scene.world = world; world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.75, 0.78, 0.84, 1.0); bg.inputs["Strength"].default_value = 0.35

bm = bmesh.new()
bmesh.ops.create_circle(bm, cap_ends=True, segments=96, radius=6.0)
floor_me = bpy.data.meshes.new("floor"); bm.to_mesh(floor_me); bm.free()
floor = bpy.data.objects.new("floor", floor_me); scene.collection.objects.link(floor)
floor.data.materials.append(principled("floor", (0.30, 0.31, 0.33), 0.50, 0.0, 0.4))

def area(name, loc, size, power, target=(0, 0, 0.03), color=(1, 1, 1), spread=math.radians(150)):
    d = bpy.data.lights.new(name, "AREA"); d.shape = "RECTANGLE"; d.size, d.size_y = size
    d.energy = power; d.color = color
    if hasattr(d, "spread"): d.spread = spread
    o = bpy.data.objects.new(name, d); scene.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return o
area("top", (0.05, 0.05, 1.15), (1.5, 1.5), 34)
area("key", (-0.75, 0.80, 0.75), (0.9, 0.7), 44, color=(1.0, 0.98, 0.95))
area("fill", (0.95, 0.25, 0.45), (0.8, 0.6), 13, color=(0.94, 0.97, 1.0))
area("rim", (0.25, -1.0, 0.65), (1.1, 0.5), 30)

# camera rig: pivot (target point, azimuth) -> elevation -> camera at distance
PIVOT = new_empty("CAM_PIVOT"); ELEV = new_empty("CAM_ELEV", parent=PIVOT)
cam_d = bpy.data.cameras.new("cam"); cam_d.lens = 62; cam_d.sensor_width = 36; cam_d.clip_start = 0.01; cam_d.clip_end = 30
cam = bpy.data.objects.new("camera", cam_d); scene.collection.objects.link(cam); cam.parent = ELEV
cam.rotation_euler = (math.pi / 2, 0, 0)
scene.camera = cam
R = math.radians
#          t      az    el   dist   target z
CAM = [(0.0,    152,  27,  0.455, 0.016),
       (T_LIFT, 140,  25,  0.42,  0.018),
       (3.9,    130,  21,  0.54,  0.046),
       (T_FLIP1, 120, 20,  0.60,  0.056),
       (T_SEP1, 100,  24,  0.66,  0.070),
       (11.1,   -10,  30,  0.65,  0.072),
       (T_ORB1, -118, 23,  0.66,  0.070),
       (T_RE2,  -172, 22,  0.58,  0.052),
       (T_END_RE, -205, 25, 0.50, -0.010),
       (DURATION + 0.6, -211, 24, 0.50, -0.014)]
key(PIVOT, "rotation_euler", [(t, R(az)) for t, az, el, d, z in CAM], index=2)
key(ELEV, "rotation_euler", [(t, -R(el)) for t, az, el, d, z in CAM], index=0)
key(cam, "location", [(t, -d) for t, az, el, d, z in CAM], index=1)
key(PIVOT, "location", [(t, z) for t, az, el, d, z in CAM], index=2)

# --------------------------------------------------------------------------------------- title overlay
def font():
    for cand in glob.glob(os.path.join(bpy.utils.resource_path("LOCAL"), "datafiles", "fonts", "Inter*")):
        try:
            return bpy.data.fonts.load(cand)
        except Exception:
            pass
    return None
FONT = font()
title_mat = bpy.data.materials.new("title"); title_mat.use_nodes = True
nt = title_mat.node_tree; nt.nodes.remove(nt.nodes["Principled BSDF"])
em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1); em.inputs["Strength"].default_value = arg("--title-strength", 9.0, float)
tr = nt.nodes.new("ShaderNodeBsdfTransparent"); mx = nt.nodes.new("ShaderNodeMixShader")
val = nt.nodes.new("ShaderNodeValue"); val.name = "alpha"; val.outputs[0].default_value = 0.0
nt.links.new(val.outputs[0], mx.inputs[0]); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2])
nt.links.new(mx.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
if hasattr(title_mat, "surface_render_method"): title_mat.surface_render_method = "BLENDED"
T_TITLE = 17.4
for t, a in ((0, 0.0), (T_TITLE, 0.0), (T_TITLE + 1.1, 1.0), (DURATION + 0.6, 1.0)):
    val.outputs[0].default_value = a
    val.outputs[0].keyframe_insert("default_value", frame=F(t))
def text(body, size, x, y, spacing=1.0, slide=0.0):
    c = bpy.data.curves.new(body, "FONT"); c.body = body; c.size = size; c.align_x = "LEFT"; c.space_character = spacing
    if FONT: c.font = FONT
    o = bpy.data.objects.new("title_" + body[:6], c); scene.collection.objects.link(o)
    o.parent = cam; o.location = (x, y, -0.30); o.data.materials.append(title_mat)
    for attr in ("visible_shadow", "visible_diffuse", "visible_glossy", "visible_transmission"):
        setattr(o, attr, False)
    o.hide_render = True; o.keyframe_insert("hide_render", frame=F(T_TITLE) - 2)
    o.hide_render = False; o.keyframe_insert("hide_render", frame=F(T_TITLE) - 1)
    if slide:
        key(o, "location", [(T_TITLE, x - slide), (T_TITLE + 1.3, x)], index=0)
    return o
# 0.30 m in front of a 62 mm lens the frame is 174 x 98 mm
text("VoxHub", 0.0170, -0.0745, -0.0305, 1.02, slide=0.004)
text("Home Assistant voice hub  ·  Raspberry Pi CM4  ·  open hardware", 0.00385, -0.0738, -0.0372, 1.06, slide=0.006)

# --------------------------------------------------------------------------------------- render settings
r = scene.render
r.engine = "CYCLES"
r.resolution_x, r.resolution_y, r.resolution_percentage = 1920, 1080, SCALE
r.film_transparent = False
r.use_persistent_data = True
r.image_settings.file_format = "PNG"; r.image_settings.color_mode = "RGB"; r.image_settings.compression = 20
if THREADS:
    r.threads_mode = "FIXED"; r.threads = THREADS
c = scene.cycles
c.device = "CPU"
c.samples = SAMPLES
c.use_adaptive_sampling = SAMPLES >= 16; c.adaptive_threshold = 0.03; c.adaptive_min_samples = 8
c.use_animated_seed = False                     # the same noise pattern in every frame keeps the denoised result calm
c.use_denoising = True; c.denoiser = "OPENIMAGEDENOISE"
try:
    c.denoising_input_passes = "RGB_ALBEDO_NORMAL"; c.denoising_prefilter = "FAST"
    c.denoising_quality = "HIGH" if SAMPLES >= 16 else "BALANCED"
except Exception:
    pass
# CPU-only render farm of one: few samples + OpenImageDenoise, short light paths, no light tree (4 lights only)
if SAMPLES >= 16:
    c.max_bounces = 6; c.diffuse_bounces = 3; c.glossy_bounces = 4
else:
    c.max_bounces = 3; c.diffuse_bounces = 1; c.glossy_bounces = 2
c.transmission_bounces = 0; c.transparent_max_bounces = 4
c.caustics_reflective = False; c.caustics_refractive = False
c.sample_clamp_indirect = 4.0
c.use_light_tree = False
scene.view_settings.view_transform = "AgX"
try:
    scene.view_settings.look = "AgX - Medium High Contrast"
except Exception:
    pass
scene.view_settings.exposure = arg("--exposure", -2.2, float)

if SAVE:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(SAVE))

if SHEET:
    os.makedirs(OUT, exist_ok=True)
    for t in (float(x) for x in SHEET.split(",")):
        scene.frame_set(int(round(F(t))))
        r.filepath = os.path.join(OUT, "still_%05.2f.png" % t)
        bpy.ops.render.render(write_still=True)
elif STILL:
    t, path = STILL
    scene.frame_set(int(round(F(t))))
    r.filepath = os.path.abspath(path)
    bpy.ops.render.render(write_still=True)
else:
    os.makedirs(OUT, exist_ok=True)
    for f in range(START, END + 1, STEP):
        path = os.path.join(OUT, "f%05d.png" % f)
        if os.path.exists(path) and os.path.getsize(path) > 1000:
            continue                                        # resume support
        scene.frame_set(f)
        r.filepath = path
        bpy.ops.render.render(write_still=True)
        print("showcase: frame %d done" % f, flush=True)
