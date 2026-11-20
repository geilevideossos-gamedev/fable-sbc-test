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

def _compact(node):
    if not isinstance(node, list):
        return _atom(node)
    return "(" + " ".join(_compact(c) for c in node) + ")"

_WS = " \t\n\r"

def prettify(src):
    out = []
    n = len(src)
    depth = 0
    last = ""
    in_quote = has_space = multi = in_xy = False
    column = 0
    backslashes = 0
    i = 0
    while i < n:
        c = src[i]
        if c in _WS and not in_quote:
            j = i
            while j < n and src[j] in _WS:
                j += 1
            nxt = src[j] if j < n else ""
            if not has_space and depth > 0 and last != "(" and nxt != ")" and nxt != "(":
                if in_xy or column < 72:
                    out.append(" "); column += 1
                else:
                    out.append("\n" + "\t" * depth); column = depth; multi = True
                has_space = True
        else:
            has_space = False
            if c == "(" and not in_quote:
                is_xy = src.startswith("(xy ", i)
                if not out:
                    out.append("("); column += 1
                elif in_xy and is_xy and column < 99:
                    out.append(" ("); column += 2
                else:
                    out.append("\n" + "\t" * depth + "("); column = depth + 1
                in_xy = is_xy
                depth += 1
            elif c == ")" and not in_quote:
                if depth > 0:
                    depth -= 1
                if last == ")" or multi:
                    out.append("\n" + "\t" * depth + ")"); column = depth + 1; multi = False
                else:
                    out.append(")"); column += 1
            else:
                if c == "\\":
                    backslashes += 1
                elif c == '"' and backslashes % 2 == 0:
                    in_quote = not in_quote
                if c != "\\":
                    backslashes = 0
                out.append(c); column += 1
            last = c
        i += 1
    return "".join(out) + "\n"

def dump(node):
    return prettify(_compact(node))

def find(node, key):
    return [c for c in node if isinstance(c, list) and c and c[0] == key]

def first(node, key, default=None):
    for c in node:
        if isinstance(c, list) and c and c[0] == key:
            return c
    return default
