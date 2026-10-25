"""Count files, lines, code, comment and docstring lines per area of a snapshot."""
import ast, io, sys, tokenize
from pathlib import Path

AREAS = {
    "backend/src": ("backend/src", (".py",), ()),
    "backend/tests": ("backend/tests", (".py",), ()),
    "frontend/src (no ui/)": ("frontend/src", (".ts", ".tsx"), ("frontend/src/components/ui/",)),
    "frontend/e2e": ("frontend/e2e", (".ts", ".tsx"), ()),
    "frontend/scripts": ("frontend/scripts", (".ts",), ()),
    "lint rules+tests": ("lint", (".yml", ".yaml"), ()),
}

def py_counts(text):
    lines = text.splitlines()
    doc = set()
    try:
        tree = ast.parse(text)
    except SyntaxError:
        tree = None
    if tree:
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and node.body:
                first = node.body[0]
                if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
                    doc.update(range(first.lineno, first.end_lineno + 1))
    comment = set(); code = set()
    for tok in tokenize.generate_tokens(io.StringIO(text).readline):
        if tok.type == tokenize.COMMENT:
            comment.add(tok.start[0])
        elif tok.type not in (tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT, tokenize.ENDMARKER):
            for n in range(tok.start[0], tok.end[0] + 1):
                if n not in doc:
                    code.add(n)
    comment -= code
    return len(lines), len(code), len(comment), len(doc)

def ts_counts(text):
    lines = text.splitlines(); code = comment = 0; inblock = False
    for raw in lines:
        s = raw.strip()
        if not s: continue
        if inblock:
            comment += 1
            if "*/" in s: inblock = False
            continue
        if s.startswith("//"): comment += 1; continue
        if s.startswith("/*"):
            comment += 1
            if "*/" not in s: inblock = True
            continue
        code += 1
    return len(lines), code, comment, 0

def yml_counts(text):
    lines = text.splitlines()
    return len(lines), sum(1 for l in lines if l.strip() and not l.strip().startswith("#")), sum(1 for l in lines if l.strip().startswith("#")), 0

root = Path(sys.argv[1])
print(f"{'area':24} {'files':>5} {'lines':>7} {'code':>7} {'comment':>7} {'docstr':>7}")
for name, (base, exts, skip) in AREAS.items():
    tot = [0, 0, 0, 0]; files = 0
    for p in sorted((root / base).rglob("*")):
        rel = str(p.relative_to(root))
        if not p.is_file() or p.suffix not in exts or any(rel.startswith(x) for x in skip) or "node_modules" in rel:
            continue
        t = p.read_text()
        c = py_counts(t) if p.suffix == ".py" else yml_counts(t) if p.suffix in (".yml", ".yaml") else ts_counts(t)
        tot = [a + b for a, b in zip(tot, c)]; files += 1
    print(f"{name:24} {files:5} {tot[0]:7} {tot[1]:7} {tot[2]:7} {tot[3]:7}")
