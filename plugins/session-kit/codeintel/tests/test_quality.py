"""The quality gates against a planted package: copies, substitutions, long files."""

from __future__ import annotations

import json
import tomllib
from typing import TYPE_CHECKING

import pytest

from session_codeintel import facts, fallbacks, quality
from session_codeintel.cli import main

if TYPE_CHECKING:
    from pathlib import Path

CORE = '''\
"""Alpha's core."""

MAX = 3


def refuse(reason: str) -> None:
    """Refuse."""
    raise ValueError(reason)


def _pk() -> int:
    return 1


def load(x: dict[str, str]) -> str:
    """Read with a default."""
    return x.get("k", "d")
'''

ROUTES = '''\
"""Alpha over HTTP."""

from . import core


def _refuse(reason: str) -> None:
    core.refuse(reason)


def _pk() -> int:
    return 1


def shape(v: str | None) -> str:
    """Or-fallback."""
    return v or ""


def pick(o: object) -> int:
    """Getattr fallback."""
    return getattr(o, "n", 0)


def tick() -> None:
    """Broad except."""
    try:
        shape(None)
    except Exception:
        pass


def read(d: dict[str, int]) -> int:
    """Except returning a literal."""
    try:
        return d["k"]
    except KeyError:
        return 0


def fill(x: str | None) -> str:
    """If-none statement."""
    if x is None:
        x = "d"
    return x


def tern(x: str | None) -> str:
    """If-none ternary."""
    return x if x is not None else ""


def logic(flag: bool) -> int:
    """An or in test position is logic, not a fallback."""
    if flag or True:
        return 1
    return 2


def lookup(session: dict[str, int], run_id: str) -> int | None:
    """A lookup by key substitutes nothing."""
    return session.get(run_id, run_id)


def prop(x: str | None) -> int | None:
    """Propagating an absence is not substituting one."""
    return None if x is None else len(x)


def label(d: dict[str, str], k: str) -> str:
    """An f-string default is still a substitute."""
    return d.get(k, f"{k} missing")


def typed(v: object) -> str:
    """isinstance is a presence test."""
    return v if isinstance(v, str) else ""


def untyped(v: object) -> str:
    """A negated one."""
    return "" if not isinstance(v, str) else v


def both(v: object) -> str:
    """isinstance and truthiness together are one presence test."""
    return v if isinstance(v, str) and v else "d"


def dispatch(v: object) -> str:
    """Two literal branches are a choice, not a substitution."""
    return "int" if isinstance(v, int) else "other"
'''

BETA = '''\
"""Beta: the other system."""

from typing import Protocol


def three_a(x: int) -> int:
    """Three statements."""
    y = x + 1
    z = y * 2
    return z


def three_b(x: int) -> int:
    """The same three statements under another name."""
    y = x + 1
    z = y * 2
    return z


def two_a(x: int) -> int:
    """Two statements."""
    y = x + 1
    return y


def two_b(x: int) -> int:
    """Two statements again: too short to call a copy."""
    y = x + 1
    return y


class Speaker(Protocol):
    """A protocol."""

    def speak(self) -> str:
        """Speak."""
        ...


class A:
    """One speaker."""

    def speak(self) -> str:
        """Speak."""
        return "x"


class B:
    """Another speaker with the same body: protocol members are not copies."""

    def speak(self) -> str:
        """Speak."""
        return "x"
'''

TEST_ALPHA = '''\
"""Tests for alpha: a fixture substitutes by design, and a copied body is still a copy."""


def test_max(d: dict[str, str]) -> None:
    """A fallback in a test is not judged."""
    assert d.get("k", "d") == "d"


def three_a(x: int) -> int:
    """Beta's three statements, copied into a test helper."""
    y = x + 1
    z = y * 2
    return z
'''

LEDGER = """\
[[duplicates]]
members = ["src/pkg/alpha/core.py:_pk", "src/pkg/alpha/http/routes.py:_pk"]
home = "src/pkg/alpha/core.py"
disposition = "move"
why = "one primary key factory"

[[duplicates]]
members = ["src/pkg/beta.py:three_a", "src/pkg/beta.py:three_b", "tests/test_alpha.py:three_a"]
home = "src/pkg/beta.py"
disposition = "move"
why = "one of them"

[[fallbacks]]
site = "src/pkg/alpha/core.py"
where = "load"
form = "get"
code = "x.get('k', 'd')"
class = "declared"
disposition = "keep"
why = "a documented default"

[[fallbacks]]
site = "src/pkg/alpha/http/routes.py"
where = "shape"
form = "or"
code = "v or ''"
class = "silent"
disposition = "raised"
why = "planted"

[[fallbacks]]
site = "src/pkg/alpha/http/routes.py"
where = "pick"
form = "getattr"
code = "getattr(o, 'n', 0)"
class = "silent"
disposition = "raised"
why = "planted"

[[fallbacks]]
site = "src/pkg/alpha/http/routes.py"
where = "tick"
form = "broad-except"
code = "except Exception"
class = "spoken"
disposition = "keep"
why = "planted"

[[fallbacks]]
site = "src/pkg/alpha/http/routes.py"
where = "read"
form = "except-returns"
code = "except KeyError: return 0"
class = "silent"
disposition = "raised"
why = "planted"

[[fallbacks]]
site = "src/pkg/alpha/http/routes.py"
where = "fill"
form = "if-none"
code = "if x is None: x = 'd'"
class = "declared"
disposition = "keep"
why = "planted"

[[fallbacks]]
site = "src/pkg/alpha/http/routes.py"
where = "tern"
form = "if-none"
code = "x if x is not None else ''"
class = "silent"
disposition = "raised"
why = "planted"

[[fallbacks]]
site = "src/pkg/alpha/http/routes.py"
where = "label"
form = "get"
code = "d.get(k, f'{k} missing')"
class = "declared"
disposition = "keep"
why = "planted"

[[fallbacks]]
site = "src/pkg/alpha/http/routes.py"
where = "typed"
form = "if-none"
code = "v if isinstance(v, str) else ''"
class = "silent"
disposition = "raised"
why = "planted"

[[fallbacks]]
site = "src/pkg/alpha/http/routes.py"
where = "untyped"
form = "if-none"
code = "'' if not isinstance(v, str) else v"
class = "silent"
disposition = "raised"
why = "planted"

[[fallbacks]]
site = "src/pkg/alpha/http/routes.py"
where = "both"
form = "if-none"
code = "v if isinstance(v, str) and v else 'd'"
class = "silent"
disposition = "raised"
why = "planted"
"""

FILES = {
    "src/pkg/__init__.py": '"""The fixture package."""\n',
    "src/pkg/alpha/__init__.py": '"""Alpha."""\n',
    "src/pkg/alpha/core.py": CORE,
    "src/pkg/alpha/http/__init__.py": '"""Alpha over HTTP."""\n',
    "src/pkg/alpha/http/routes.py": ROUTES,
    "src/pkg/beta.py": BETA,
    "tests/__init__.py": '"""Tests."""\n',
    "tests/test_alpha.py": TEST_ALPHA,
}
PLANTED_SITES = 11
PLANTED_FAMILIES = 2


def build(root: Path, *, ledger: bool = True, extra: dict[str, str] | None = None) -> Path:
    """Write the planted package under the root and return it."""
    files = dict(FILES)
    if ledger:
        files["quality-ledger.toml"] = LEDGER
    files.update(extra or {})
    for relative, content in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return root


def settings_with(root: Path, block: dict[str, object]) -> None:
    """Write the settings file with the given quality block."""
    path = root / ".claude" / "claude-kit.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"quality": block}), encoding="utf-8")


def modules_of(root: Path) -> list[facts.Module]:
    """Read the root's modules by its settings."""
    return facts.scan(root, quality.read_settings(root).areas)


def families_of(root: Path) -> list[quality.Family]:
    """Find the root's duplicate families."""
    return quality.families(modules_of(root))


def sites_of(root: Path) -> list[fallbacks.Site]:
    """Find the root's fallback sites outside its tests."""
    return [
        site
        for module in modules_of(root)
        if not module.is_test
        for site in fallbacks.sites(module)
    ]


def test_the_planted_copies_are_found_and_nothing_else(tmp_path: Path) -> None:
    """Same name at any length, other names at three statements, protocols out, tests read."""
    found = families_of(build(tmp_path))
    assert [family.members for family in found] == [
        ("src/pkg/alpha/core.py:_pk", "src/pkg/alpha/http/routes.py:_pk"),
        ("src/pkg/beta.py:three_a", "src/pkg/beta.py:three_b", "tests/test_alpha.py:three_a"),
    ]


@pytest.mark.parametrize(
    ("where", "form", "code"),
    [
        ("load", "get", "x.get('k', 'd')"),
        ("shape", "or", "v or ''"),
        ("pick", "getattr", "getattr(o, 'n', 0)"),
        ("tick", "broad-except", "except Exception"),
        ("read", "except-returns", "except KeyError: return 0"),
        ("fill", "if-none", "if x is None: x = 'd'"),
        ("tern", "if-none", "x if x is not None else ''"),
        ("label", "get", "d.get(k, f'{k} missing')"),
        ("typed", "if-none", "v if isinstance(v, str) else ''"),
        ("untyped", "if-none", "'' if not isinstance(v, str) else v"),
        ("both", "if-none", "v if isinstance(v, str) and v else 'd'"),
    ],
)
def test_each_planted_form_is_found_once(tmp_path: Path, where: str, form: str, code: str) -> None:
    """One site per plant, keyed by the enclosing function, the form and the code."""
    matches = [s for s in sites_of(build(tmp_path)) if s.key.where == where]
    assert [(s.key.form, s.key.code) for s in matches] == [(form, code)]


@pytest.mark.parametrize("where", ["logic", "lookup", "prop", "dispatch", "test_max"])
def test_logic_lookups_propagation_and_tests_are_not_fallbacks(tmp_path: Path, where: str) -> None:
    """An or in test position, a lookup by key, a carried None, a two-literal choice, a test."""
    assert [s for s in sites_of(build(tmp_path)) if s.key.where == where] == []


def test_the_whole_plant_is_exactly_eleven_sites(tmp_path: Path) -> None:
    """The finder sees the eleven plants and invents nothing."""
    assert len(sites_of(build(tmp_path))) == PLANTED_SITES


def test_a_complete_ledger_passes_and_the_ratchet_holds_both_ways(tmp_path: Path) -> None:
    """A doubled site needs a count, and a removed site or copy makes its row stale."""
    root = build(tmp_path)
    settings = quality.read_settings(root)
    assert quality.check(root, settings).clean
    routes = root / "src/pkg/alpha/http/routes.py"
    text = routes.read_text(encoding="utf-8")
    routes.write_text(text.replace('return v or ""', 'w = v or ""\n    return v or ""'))
    report = quality.check(root, settings)
    assert [(s.key.where, found, known) for s, found, known in report.fallbacks.new] == [
        ("shape", 2, 1)
    ]
    routes.write_text(text.replace('return v or ""', "return v"), encoding="utf-8")
    report = quality.check(root, settings)
    assert [(row.where, found) for row, found in report.fallbacks.stale] == [("shape", 0)]
    routes.write_text(text.replace("def _pk() -> int:\n    return 1\n", ""), encoding="utf-8")
    report = quality.check(root, settings)
    assert report.duplicates.new == ()
    assert [row.members[0] for row in report.duplicates.stale] == ["src/pkg/alpha/core.py:_pk"]
    assert any(line.startswith("stale duplicate row") for line in quality.lines(report))


def test_a_new_copy_fails_the_gate_by_name(tmp_path: Path) -> None:
    """A copy the ledger does not know is reported with every member."""
    root = build(tmp_path)
    (root / "src/pkg/alpha/extra.py").write_text(
        '"""Extra."""\n\n\ndef _pk() -> int:\n    return 1\n', encoding="utf-8"
    )
    report = quality.check(root, quality.read_settings(root))
    assert len(report.duplicates.new) == 1
    assert "src/pkg/alpha/extra.py:_pk" in report.duplicates.new[0].members
    assert quality.lines(report)[0].startswith("new duplicate (1 statement)")


def test_protocols_read_from_another_root_are_excluded_too(tmp_path: Path) -> None:
    """A method a Protocol outside the areas declares is not a copy when two classes have it."""
    root = build(tmp_path)
    sibling = tmp_path / "sibling" / "src" / "lib"
    sibling.mkdir(parents=True)
    (sibling / "kit.py").write_text(
        '"""Kit."""\n\nfrom typing import Protocol\n\n\nclass Kit(Protocol):\n'
        '    """Kit."""\n\n    def close(self) -> None:\n        """Close."""\n        ...\n',
        encoding="utf-8",
    )
    (root / "src/pkg/alpha/extra.py").write_text(
        '"""Extra."""\n\n\nclass A:\n    """A."""\n\n    def close(self) -> None:\n'
        '        """Close."""\n        return None\n\n\nclass B:\n    """B."""\n\n'
        '    def close(self) -> None:\n        """Close."""\n        return None\n',
        encoding="utf-8",
    )
    settings_with(root, {"areas": [{"path": "src"}, {"path": "tests"}]})
    report = quality.check(root, quality.read_settings(root))
    assert any("close" in f.members[0] for f in report.duplicates.new)
    settings_with(
        root, {"areas": [{"path": "src"}, {"path": "tests"}], "protocols_from": ["sibling"]}
    )
    report = quality.check(root, quality.read_settings(root))
    assert not any("close" in f.members[0] for f in report.duplicates.new)


def test_a_file_over_its_cap_is_named_with_the_overage(tmp_path: Path) -> None:
    """The cap counts code lines, a long entry raises or lifts it, a missing file drifts."""
    root = build(tmp_path)
    settings_with(root, {"max_code_lines": 20})
    report = quality.check(root, quality.read_settings(root))
    assert [(o.path, o.lines, o.cap) for o in report.length] == [
        ("src/pkg/alpha/http/routes.py", 43, 20),
        ("src/pkg/beta.py", 24, 20),
    ]
    assert "src/pkg/alpha/http/routes.py: 43 code lines, 23 over its cap of 20" in quality.lines(
        report
    )
    settings_with(
        root,
        {
            "max_code_lines": 20,
            "long": [
                {"file": "src/pkg/alpha/http/routes.py", "cap": 60, "reason": "the plants"},
                {"file": "src/pkg/beta.py", "reason": "a registry that only grows"},
                {"file": "src/pkg/gone.py", "cap": 30, "reason": "gone"},
            ],
        },
    )
    report = quality.check(root, quality.read_settings(root))
    assert report.length == ()
    assert report.drift == ("src/pkg/gone.py",)
    assert "the long entry for src/pkg/gone.py names a file that is not there" in quality.lines(
        report
    )


def test_a_row_that_cannot_be_read_is_refused_never_skipped(tmp_path: Path) -> None:
    """A misspelt disposition, an unknown key, and a dead class each refuse the ledger whole."""
    root = build(tmp_path)
    path = root / "quality-ledger.toml"
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace('"raised"', '"rased"', 1), encoding="utf-8")
    with pytest.raises(quality.LedgerError, match="rased"):
        quality.read_ledger(root, quality.read_settings(root))
    path.write_text(text.replace('why = "planted"', 'why = "planted"\nhome = "x"', 1))
    with pytest.raises(quality.LedgerError, match="home"):
        quality.read_ledger(root, quality.read_settings(root))
    path.write_text(text.replace('class = "silent"', 'class = "dead"', 1), encoding="utf-8")
    with pytest.raises(quality.LedgerError, match="dead"):
        quality.read_ledger(root, quality.read_settings(root))


def test_skeleton_rows_are_valid_toml_with_the_judgement_blank(tmp_path: Path) -> None:
    """What --report prints can be pasted into the ledger and filled in."""
    root = build(tmp_path, ledger=False)
    report = quality.check(root, quality.read_settings(root))
    rows = tomllib.loads(quality.skeleton(report))
    assert len(rows["duplicates"]) == PLANTED_FAMILIES
    assert rows["duplicates"][0]["disposition"] == "move"
    assert len(rows["fallbacks"]) == PLANTED_SITES
    assert {row["class"] for row in rows["fallbacks"]} == {""}
    assert rows["fallbacks"][0]["site"] == "src/pkg/alpha/core.py"


def test_the_command_reports_and_exits_by_the_verdict(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Clean is one line and 0, a problem its lines and 1, --report rows and 0, a bad ledger 2."""
    root = build(tmp_path)
    assert main(["quality", str(root)]) == 0
    assert capsys.readouterr().out == (
        "8 modules: no duplicate, every fallback judged (11 rows), every file under its cap\n"
    )
    for name in ("extra", "extra2"):
        (root / f"src/pkg/alpha/{name}.py").write_text(
            '"""Extra."""\n\n\ndef _x() -> int:\n    return 2\n', encoding="utf-8"
        )
    assert main(["quality", str(root)]) == 1
    out = capsys.readouterr().out
    assert out.startswith("new duplicate (1 statement)")
    assert out.endswith("1 problem\n")
    assert main(["quality", str(root), "--report"]) == 0
    assert tomllib.loads(capsys.readouterr().out)["duplicates"][0]["home"] == ""
    path = root / "quality-ledger.toml"
    path.write_text(path.read_text(encoding="utf-8").replace('"raised"', '"rased"', 1))
    assert main(["quality", str(root)]) == 2
    assert capsys.readouterr().err.startswith("quality-ledger.toml: ")
