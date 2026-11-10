"""Schematic-as-code helper: builds KiCad 9 .kicad_sch files from Python.

Every pin of every placed symbol must be given a net (or "NC"); the helper
draws a short wire stub from the pin and attaches a global label or a power
symbol.  The resulting schematic is fully label-connected, which makes it easy
to generate and to diff, and KiCad's own ERC/netlister remain the source of
truth (the PCB is built from the netlist exported by kicad-cli).
"""
import copy, math, os, uuid, hashlib
from sexpr import parse, dump, find, first, Sym

S = Sym
KICAD_SYM_DIR = os.environ.get("KICAD_SYM_DIR", "/usr/share/kicad/symbols")
NS = uuid.UUID("6f1d3c0e-5b1a-4f0e-9a51-0c0ffee0cafe")
PROJECT = "voxhub"

def uid(*parts):
    """Deterministic UUIDs so regenerated files diff cleanly."""
    return str(uuid.uuid5(NS, "/".join(str(p) for p in parts)))

def snap(v):
    return round(round(v / 1.27) * 1.27, 4)

def g(v):  # snap to 0.01 mm
    return round(v + 0.0, 4)

# ---------------------------------------------------------------- symbols --
class SymLib:
    def __init__(self):
        self._files = {}
        self.project = {}      # name -> s-expr (flattened), written to voxhub.kicad_sym
        self.meta = {}         # name -> dict(pins=..., props=...)

    def _file(self, lib):
        if lib not in self._files:
            t = parse(open(os.path.join(KICAD_SYM_DIR, lib + ".kicad_sym")).read())
            self._files[lib] = {s[1]: s for s in find(t, "symbol")}
        return self._files[lib]

    def _flatten(self, lib, name):
        s = copy.deepcopy(self._file(lib)[name])
        ext = first(s, "extends")
        if not ext:
            return s
        parent = self._flatten(lib, ext[1])
        pname = parent[1]
        out = [S("symbol"), name]
        child_props = {p[1]: p for p in find(s, "property")}
        seen = set()
        for c in parent[2:]:
            if isinstance(c, list) and c[0] == "property":
                seen.add(c[1])
                out.append(child_props.get(c[1], c))
            elif isinstance(c, list) and c[0] == "symbol":
                c = copy.deepcopy(c)
                c[1] = name + c[1][len(pname):]
                out.append(c)
            else:
                out.append(c)
        for k, p in child_props.items():
            if k not in seen:
                out.append(p)
        return out

    def use(self, libid, alias=None, pin_types=None, footprint=None):
        """Copy a stock symbol into the project library (optionally patched)."""
        lib, name = libid.split(":")
        alias = alias or name
        if alias in self.project:
            return alias
        s = self._flatten(lib, name)
        if alias != name:
            s[1] = alias
            for c in s:
                if isinstance(c, list) and c[0] == "symbol":
                    c[1] = alias + c[1][len(name):]
        if pin_types:
            for sub in find(s, "symbol"):
                for p in find(sub, "pin"):
                    num = first(p, "number")[1]
                    if num in pin_types:
                        p[1] = S(pin_types[num])
        if footprint:
            for p in find(s, "property"):
                if p[1] == "Footprint":
                    p[2] = footprint
        self.add(alias, s)
        return alias

    def add(self, name, s):
        self.project[name] = s
        pins = []
        for sub in find(s, "symbol"):
            unit = int(sub[1].rsplit("_", 2)[1])
            for p in find(sub, "pin"):
                at = first(p, "at")
                pins.append(dict(unit=unit, type=str(p[1]), x=float(at[1]), y=float(at[2]),
                                 a=int(float(at[3])) if len(at) > 3 else 0,
                                 name=first(p, "name")[1], num=first(p, "number")[1],
                                 length=float(first(p, "length")[1])))
        props = {p[1]: p for p in find(s, "property")}
        self.meta[name] = dict(pins=pins, props=props, power=first(s, "power") is not None)

    def box(self, name, left, right, ref="U", footprint="", datasheet="", descr="",
            width=None, pitch=2.54, value=None, top=(), bottom=()):
        """Create a rectangular symbol. left/right: list of (num, name, type) or None (gap)."""
        rows = max(len(left), len(right))
        maxl = max([len(p[1]) for p in left if p] + [1])
        maxr = max([len(p[1]) for p in right if p] + [1])
        w = width or max(20.32, math.ceil(((maxl + maxr) * 1.0 + 6) / 2.54) * 2.54)
        hw = w / 2
        hw = math.ceil(hw / 2.54) * 2.54
        h = (rows - 1) * pitch
        top_y = math.ceil((h / 2) / 2.54) * 2.54
        ef = [S("effects"), [S("font"), [S("size"), 1.27, 1.27]]]
        def prop(k, v, x, y, hide=False, just=None):
            e = copy.deepcopy(ef)
            if just: e.append([S("justify"), S(just)])
            if hide: e.append([S("hide"), S("yes")])
            return [S("property"), k, v, [S("at"), x, y, 0], e]
        s = [S("symbol"), name, [S("exclude_from_sim"), S("no")], [S("in_bom"), S("yes")], [S("on_board"), S("yes")],
             prop("Reference", ref, -hw, top_y + 5.08, just="left"),
             prop("Value", value or name, -hw, top_y + 2.794, just="left"),
             prop("Footprint", footprint, 0, 0, hide=True),
             prop("Datasheet", datasheet, 0, 0, hide=True),
             prop("Description", descr, 0, 0, hide=True)]
        body = [S("symbol"), name + "_0_1",
                [S("rectangle"), [S("start"), -hw, top_y + 2.54], [S("end"), hw, top_y - h - 2.54],
                 [S("stroke"), [S("width"), 0.254], [S("type"), S("default")]],
                 [S("fill"), [S("type"), S("background")]]]]
        pins = [S("symbol"), name + "_1_1"]
        def pin(p, x, y, a):
            num, nm, ty = p
            pins.append([S("pin"), S(ty), S("line"), [S("at"), x, y, a], [S("length"), 2.54],
                         [S("name"), nm, copy.deepcopy(ef)], [S("number"), str(num), copy.deepcopy(ef)]])
        for i, p in enumerate(left):
            if p: pin(p, -hw - 2.54, top_y - i * pitch, 0)
        for i, p in enumerate(right):
            if p: pin(p, hw + 2.54, top_y - i * pitch, 180)
        s += [body, pins]
        self.add(name, s)
        return name

    def write(self, path):
        t = [S("kicad_symbol_lib"), [S("version"), 20241209], [S("generator"), "voxhub_gen"],
             [S("generator_version"), "9.0"]] + [self.project[k] for k in sorted(self.project)]
        open(path, "w").write(dump(t) + "\n")

POWER_UP = {"+5V", "+3V3", "VBUS"}        # drawn with arrow-up power symbols
POWER_DOWN = {"GND"}

# ----------------------------------------------------------------- sheets --
class Sheet:
    def __init__(self, design, name, filename, title, page, paper="A3"):
        self.d, self.name, self.filename, self.title, self.page, self.paper = design, name, filename, title, page, paper
        self.uuid = uid("sheet", name)
        self.items = []
        self.used = set()
        self._pts = set()
        self._npwr = 0
        self.is_root = False

    @property
    def path(self):
        return "/" + self.d.root.uuid + ("" if self.is_root else "/" + self.uuid)

    # -- primitives
    def wire(self, x1, y1, x2, y2):
        self.items.append([S("wire"), [S("pts"), [S("xy"), g(x1), g(y1)], [S("xy"), g(x2), g(y2)]],
                           [S("stroke"), [S("width"), 0], [S("type"), S("default")]],
                           [S("uuid"), uid(self.name, "w", x1, y1, x2, y2)]])

    def nc(self, x, y):
        self.items.append([S("no_connect"), [S("at"), g(x), g(y)], [S("uuid"), uid(self.name, "nc", x, y)]])

    def text(self, s, x, y, size=1.8, bold=False):
        font = [S("font"), [S("size"), size, size]]
        if bold: font.append([S("bold"), S("yes")])
        self.items.append([S("text"), s, [S("exclude_from_sim"), S("no")], [S("at"), g(x), g(y), 0],
                           [S("effects"), font, [S("justify"), S("left"), S("bottom")]],
                           [S("uuid"), uid(self.name, "t", s, x, y)]])

    def box(self, x1, y1, x2, y2, title=None):
        self.items.append([S("rectangle"), [S("start"), g(x1), g(y1)], [S("end"), g(x2), g(y2)],
                           [S("stroke"), [S("width"), 0.15], [S("type"), S("dash")]],
                           [S("fill"), [S("type"), S("none")]], [S("uuid"), uid(self.name, "box", x1, y1, x2, y2)]])
        if title:
            self.text(title, x1 + 1.5, y1 + 4.2, size=2.2, bold=True)

    def label(self, net, x, y, ang):
        just = {0: "left", 180: "right", 90: "left", 270: "right"}[ang]
        self.items.append([S("global_label"), net, [S("shape"), S("passive")], [S("at"), g(x), g(y), ang],
                           [S("fields_autoplaced"), S("yes")],
                           [S("effects"), [S("font"), [S("size"), 1.27, 1.27]], [S("justify"), S(just)]],
                           [S("uuid"), uid(self.name, "gl", net, x, y)],
                           [S("property"), "Intersheetrefs", "${INTERSHEET_REFS}", [S("at"), g(x), g(y), 0],
                            [S("effects"), [S("font"), [S("size"), 1.27, 1.27]], [S("hide"), S("yes")]]]])
        self.d.nets_used.add(net)

    def _power(self, net, x, y, direction):
        """direction: unit vector (screen coords) pointing away from the pin."""
        name = self.d.lib.use("power:" + ("PWR_FLAG" if net == "PWR_FLAG" else net))
        up = net in POWER_UP or net == "PWR_FLAG"
        dx, dy = direction
        if up:
            rot = {(0, -1): 0, (-1, 0): 90, (0, 1): 180, (1, 0): 270}[(dx, dy)]
        else:
            rot = {(0, 1): 0, (1, 0): 90, (0, -1): 180, (-1, 0): 270}[(dx, dy)]
        self._npwr += 1
        ref = "#PWR%s%02d" % (self.page, self._npwr) if net != "PWR_FLAG" else "#FLG%s%02d" % (self.page, self._npwr)
        self._emit_symbol(name, ref, net, x, y, rot, {}, hide_ref=True, power=True)

    # -- symbols
    @staticmethod
    def _xf(px, py, rot):
        vx, vy = px, -py
        for _ in range((rot // 90) % 4):
            vx, vy = vy, -vx
        return vx, vy

    def _emit_symbol(self, name, ref, value, x, y, rot, fields, unit=1, dnp=False, hide_ref=False,
                     power=False, footprint=None, in_bom=True, textpos=None, hide_value=False):
        meta = self.d.lib.meta[name]
        self.used.add(name)
        u = uid(self.name, "sym", ref, unit)
        ef = lambda hide=False, just=None: [S("effects"), [S("font"), [S("size"), 1.27, 1.27]]] + \
            ([[S("justify"), S(just)]] if just else []) + ([[S("hide"), S("yes")]] if hide else [])
        def lp(k):
            p = meta["props"].get(k)
            if not p: return (0, 0)
            at = first(p, "at")
            return float(at[1]), float(at[2])
        rx, ry = self._xf(*lp("Reference"), rot); vx, vy = self._xf(*lp("Value"), rot)
        rj = vj = None
        if textpos:
            (rx, ry, rj), (vx, vy, vj) = textpos
        if power:
            vx, vy = self._xf(0, 3.8 if (value in POWER_UP or value == "PWR_FLAG") else -3.8, rot)
            if rot in (90, 270): vx *= 1.6
        fp = footprint if footprint is not None else (first(meta["props"].get("Footprint", [0, 0, ""]), "x") or meta["props"].get("Footprint", [0, 0, ""]))[2] if False else (footprint if footprint is not None else (meta["props"]["Footprint"][2] if "Footprint" in meta["props"] else ""))
        ds = meta["props"]["Datasheet"][2] if "Datasheet" in meta["props"] else ""
        desc = meta["props"]["Description"][2] if "Description" in meta["props"] else ""
        sym = [S("symbol"), [S("lib_id"), PROJECT + ":" + name], [S("at"), g(x), g(y), rot], [S("unit"), unit],
               [S("exclude_from_sim"), S("no")], [S("in_bom"), S("yes" if (in_bom and not power) else "no")],
               [S("on_board"), S("yes")], [S("dnp"), S("yes" if dnp else "no")], [S("uuid"), u],
               [S("property"), "Reference", ref, [S("at"), g(x + rx), g(y + ry), 0], ef(hide_ref, rj)],
               [S("property"), "Value", value, [S("at"), g(x + vx), g(y + vy), 0], ef(hide_value, vj)],
               [S("property"), "Footprint", fp, [S("at"), g(x), g(y), 0], ef(True)],
               [S("property"), "Datasheet", ds, [S("at"), g(x), g(y), 0], ef(True)],
               [S("property"), "Description", desc, [S("at"), g(x), g(y), 0], ef(True)]]
        for k, v in fields.items():
            sym.append([S("property"), k, v, [S("at"), g(x), g(y), 0], ef(True)])
        nums = []
        for p in meta["pins"]:
            if p["unit"] in (0, unit) and p["num"] not in nums:
                nums.append(p["num"])
                sym.append([S("pin"), p["num"], [S("uuid"), uid(u, "pin", p["num"])]])
        sym.append([S("instances"), [S("project"), PROJECT,
                    [S("path"), self.path, [S("reference"), ref], [S("unit"), unit]]]])
        self.items.append(sym)
        return u

    def place(self, name, ref, value, x, y, nets, rot=0, footprint=None, fields=None, unit=1,
              dnp=False, stub=2.54, textpos=None, in_bom=True, hide_value=False):
        """nets: {pin number or pin name: net | 'NC'}; every pin must be covered."""
        meta = self.d.lib.meta[name]
        fields = dict(fields or {})
        x, y = snap(x), snap(y)
        self._emit_symbol(name, ref, value, x, y, rot, fields, unit=unit, dnp=dnp, footprint=footprint,
                          textpos=textpos, in_bom=in_bom, hide_value=hide_value)
        if ref in self.d.components and unit == 1:
            raise ValueError("duplicate reference " + ref)
        comp = self.d.components.setdefault(ref, dict(ref=ref, value=value, sheet=self.name, pins={},
                                                      footprint=footprint if footprint is not None else meta["props"].get("Footprint", [0, 0, ""])[2],
                                                      fields=fields, dnp=dnp, in_bom=in_bom))
        for p in meta["pins"]:
            if p["unit"] not in (0, unit):
                continue
            key = p["num"] if p["num"] in nets else (p["name"] if p["name"] in nets else None)
            if key is None:
                if p["type"] == "no_connect":
                    continue
                raise KeyError(f"{ref} ({name}): pin {p['num']} '{p['name']}' has no net assigned")
            net = nets[key]
            px, py = self._xf(p["x"], p["y"], rot)
            px, py = x + px, y + py
            a = math.radians(p["a"])
            ox, oy = self._xf(-round(math.cos(a)), -round(math.sin(a)), rot)
            if net == "NC":
                if (g(px), g(py)) not in self._pts:
                    self.nc(px, py); self._pts.add((g(px), g(py)))
                continue
            comp["pins"][p["num"]] = net
            if (g(px), g(py), net) in self._pts:
                continue
            self._pts.add((g(px), g(py), net))
            ex, ey = px + ox * stub, py + oy * stub
            self.wire(px, py, ex, ey)
            if net in POWER_UP or net in POWER_DOWN:
                self._power(net, ex, ey, (int(ox), int(oy)))
            else:
                ang = {(-1, 0): 180, (1, 0): 0, (0, -1): 90, (0, 1): 270}[(int(ox), int(oy))]
                self.label(net, ex, ey, ang)

    def flag(self, net, x, y):
        """PWR_FLAG attached to a net (tells ERC the net is driven)."""
        x, y = snap(x), snap(y)
        self.wire(x, y, x, y - 2.54)
        self._power("PWR_FLAG", x, y - 2.54, (0, -1))
        if net in POWER_UP or net in POWER_DOWN:
            self.wire(x, y, x + 5.08, y)
            self._power(net, x + 5.08, y, (0, -1) if net in POWER_UP else (0, 1))
        else:
            self.label(net, x, y, 0)

    # -- output
    def render(self, extra=()):
        lib = [S("lib_symbols")]
        for n in sorted(self.used):
            s = copy.deepcopy(self.d.lib.project[n])
            s[1] = PROJECT + ":" + n
            lib.append(s)
        t = [S("kicad_sch"), [S("version"), 20250114], [S("generator"), "eeschema"], [S("generator_version"), "9.0"],
             [S("uuid"), self.d.root.uuid if self.is_root else self.uuid], [S("paper"), self.paper],
             [S("title_block"), [S("title"), self.title], [S("date"), self.d.date], [S("rev"), self.d.rev],
              [S("company"), self.d.company], [S("comment"), 1, "Generated by hardware/gen - do not edit by hand"]],
             lib] + self.items + list(extra)
        if self.is_root:
            t.append([S("sheet_instances"), [S("path"), "/", [S("page"), "1"]]])
        t.append([S("embedded_fonts"), S("no")])
        return dump(t) + "\n"


class Design:
    def __init__(self, title, rev, date, company):
        self.lib = SymLib()
        self.title, self.rev, self.date, self.company = title, rev, date, company
        self.components = {}
        self.nets_used = set()
        self.sheets = []
        self.root = Sheet(self, "root", PROJECT + ".kicad_sch", title, 1)
        self.root.is_root = True
        self.root.uuid = uid("root")

    def sheet(self, name, title):
        s = Sheet(self, name, name + ".kicad_sch", title, len(self.sheets) + 2)
        self.sheets.append(s)
        return s

    def write(self, outdir):
        extra = []
        for i, s in enumerate(self.sheets):
            x, y, w, h = 30 + (i % 3) * 75, 60 + (i // 3) * 45, 55, 25
            ef = [S("effects"), [S("font"), [S("size"), 1.6, 1.6]], [S("justify"), S("left"), S("bottom")]]
            extra.append([S("sheet"), [S("at"), x, y], [S("size"), w, h], [S("exclude_from_sim"), S("no")],
                          [S("in_bom"), S("yes")], [S("on_board"), S("yes")], [S("dnp"), S("no")],
                          [S("fields_autoplaced"), S("yes")],
                          [S("stroke"), [S("width"), 0.2], [S("type"), S("solid")]],
                          [S("fill"), [S("color"), 255, 255, 220, 1.0]], [S("uuid"), s.uuid],
                          [S("property"), "Sheetname", s.title, [S("at"), x, y - 0.8, 0], ef],
                          [S("property"), "Sheetfile", s.filename, [S("at"), x, y + h + 3.0, 0], copy.deepcopy(ef)],
                          [S("instances"), [S("project"), PROJECT,
                           [S("path"), "/" + self.root.uuid, [S("page"), str(s.page)]]]]])
            open(os.path.join(outdir, s.filename), "w").write(s.render())
        open(os.path.join(outdir, self.root.filename), "w").write(self.root.render(extra))
        self.lib.write(os.path.join(outdir, PROJECT + ".kicad_sym"))
