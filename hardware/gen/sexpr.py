"""Minimal S-expression reader/writer for KiCad files."""
import re

class Sym(str):
    """Bare (unquoted) atom."""
    __slots__ = ()

_tok = re.compile(r'\s*(?:(\()|(\))|"((?:[^"\\]|\\.)*)"|([^\s()"]+))')

def parse(text):
    pos = 0
    stack = [[]]
    n = len(text)
    while True:
        m = _tok.match(text, pos)
        if not m:
            break
        pos = m.end()
        if m.group(1):
            stack.append([])
        elif m.group(2):
            done = stack.pop()
            stack[-1].append(done)
        elif m.group(3) is not None:
            stack[-1].append(m.group(3).replace('\\"', '"').replace('\\\\', '\\').replace('\\n', '\n'))
        else:
            stack[-1].append(Sym(m.group(4)))
        if pos >= n:
            break
    return stack[0][0]

def _atom(a):
    if isinstance(a, Sym):
        return str(a)
    if isinstance(a, bool):
        return "yes" if a else "no"
    if isinstance(a, float):
        s = ("%.6f" % a).rstrip("0").rstrip(".")
        return s if s not in ("-0", "") else "0"
    if isinstance(a, int):
        return str(a)
    return '"' + str(a).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'

def dump(node, indent=0):
    if not isinstance(node, list):
        return _atom(node)
    simple = all(not isinstance(c, list) for c in node)
    if simple:
        return "(" + " ".join(_atom(c) for c in node) + ")"
    flat = "(" + " ".join(dump(c) for c in node) + ")"
    if len(flat) < 100 and flat.count("(") < 6:
        return flat
    pad = "\t" * (indent + 1)
    out = ["(" + _atom(node[0])]
    i = 1
    while i < len(node) and not isinstance(node[i], list):
        out[0] += " " + _atom(node[i]); i += 1
    for c in node[i:]:
        out.append(pad + dump(c, indent + 1))
    return "\n".join(out) + "\n" + "\t" * indent + ")"

def find(node, key):
    return [c for c in node if isinstance(c, list) and c and c[0] == key]

def first(node, key, default=None):
    for c in node:
        if isinstance(c, list) and c and c[0] == key:
            return c
    return default
