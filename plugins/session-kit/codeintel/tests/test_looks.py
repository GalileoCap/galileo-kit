"""The looks check: a class string written twice is found, an allowance holds its files."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from session_codeintel.cli import main
from session_codeintel.looks import Allowance, Settings, check, read_settings, scan
from tests.tools import tree

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

PAGE = 'const A = () => <p className="space-y-1 text-sm">a</p>\n'
TONE = "text-muted-foreground text-sm"


def test_every_way_a_class_string_is_written_is_a_site_and_one_class_is_no_look(
    tmp_path: Path,
) -> None:
    """A class prop, cn, a conditional, a template and a looks file are read, classes sorted."""
    tree(
        tmp_path,
        {
            "src/a.tsx": 'const A = () => <p className="text-sm text-muted-foreground">a</p>\n',
            "src/b.tsx": (
                "const B = ({ c, x }) => (\n"
                "  <div className={cn('flex gap-2', c)}>\n"
                "    <div className={x ? 'gap-2 flex' : 'grid'} />\n"
                '    <Card contentClassName="flex gap-2" />\n'
                "    <span className={`text-muted-foreground text-sm`} />\n"
                "    <span className={`text-sm ${x}`} />\n"
                '    <i className="only-one" />\n'
                "  </div>\n"
                ")\n"
            ),
            "src/lib/link-looks.ts": "export const looks = { a: 'underline underline-offset-4' }\n",
            "src/c.ts": "export const k = cn('underline-offset-4 underline')\n",
        },
    )
    sites = scan(tmp_path, Settings())
    assert [(s.file, s.line, s.look) for s in sites] == [
        ("src/a.tsx", 1, TONE),
        ("src/b.tsx", 2, "flex gap-2"),
        ("src/b.tsx", 3, "flex gap-2"),
        ("src/b.tsx", 4, "flex gap-2"),
        ("src/b.tsx", 5, TONE),
        ("src/c.ts", 1, "underline underline-offset-4"),
        ("src/lib/link-looks.ts", 1, "underline underline-offset-4"),
    ]
    report = check(sites, Settings())
    assert [(r.look, r.places) for r in report.repeats] == [
        (TONE, ("src/a.tsx:1", "src/b.tsx:5")),
        ("flex gap-2", ("src/b.tsx:2", "src/b.tsx:3", "src/b.tsx:4")),
        ("underline underline-offset-4", ("src/c.ts:1", "src/lib/link-looks.ts:1")),
    ]


def test_text_that_is_not_a_class_string_and_a_skipped_directory_are_left_alone(
    tmp_path: Path,
) -> None:
    """A label, a title and a plain record are no look, and shadcn's primitives are skipped."""
    tree(
        tmp_path,
        {
            "src/a.tsx": (
                'const A = () => <p aria-label="Force pause" title={"Force pause"}>'
                '{"Force pause"}</p>\n'
            ),
            "src/c.ts": "export const labels = { pause: 'Force pause' }\n",
            "src/components/ui/button.tsx": PAGE,
            "src/d.tsx": PAGE,
        },
    )
    assert [s.file for s in scan(tmp_path, Settings())] == ["src/d.tsx"]


def test_an_allowed_look_is_not_a_repeat_and_its_entry_drifts_with_its_files(
    tmp_path: Path,
) -> None:
    """An allowance in the settings exempts the look while it stays in the files it lists."""
    tree(tmp_path, {"src/a.tsx": PAGE, "src/b.tsx": PAGE})
    held = Settings(allowed=(Allowance("text-sm space-y-1", ("src/a.tsx", "src/b.tsx")),))
    assert check(scan(tmp_path, held), held).clean
    tree(tmp_path, {"src/c.tsx": PAGE})
    spread = check(scan(tmp_path, held), held)
    assert [(d.look, d.listed, d.found) for d in spread.drifts] == [
        ("space-y-1 text-sm", ("src/a.tsx", "src/b.tsx"), ("src/a.tsx", "src/b.tsx", "src/c.tsx"))
    ]
    tree(tmp_path, {"src/b.tsx": 'const B = () => <p className="text-sm">b</p>\n'})
    tree(tmp_path, {"src/c.tsx": "export {}\n"})
    assert [d.found for d in check(scan(tmp_path, held), held).drifts] == [("src/a.tsx",)]


def test_the_command_reads_the_settings_and_exits_1_on_a_repeat(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """``looks ROOT`` reads src, skip and allowed from the settings, prints the places, exits 1."""
    allowance = {"look": "a b", "files": ["frontend/src/x.tsx", "frontend/src/y.tsx"]}
    settings = {
        "looks": {"src": "frontend/src", "skip": ["frontend/src/vendor"], "allowed": [allowance]}
    }
    x_page = 'const X = () => <p className="a b">x</p>\nconst X2 = () => <p className="c d">x</p>\n'
    y_page = 'const Y = () => <p className="b a">y</p>\nconst Y2 = () => <p className="d c">y</p>\n'
    tree(
        tmp_path,
        {
            ".claude/claude-kit.json": json.dumps(settings),
            "frontend/src/x.tsx": x_page,
            "frontend/src/y.tsx": y_page,
            "frontend/src/vendor/v.tsx": 'const V = () => <p className="e f">v</p>\n',
        },
    )
    read = read_settings(tmp_path)
    assert read.src == "frontend/src"
    assert read.skip == ("frontend/src/vendor",)
    assert read.allowed == (Allowance("a b", ("frontend/src/x.tsx", "frontend/src/y.tsx")),)
    assert main(["looks", str(tmp_path)]) == 1
    out = capsys.readouterr().out.splitlines()
    assert out[:3] == [
        '"c d" is written in 2 places:',
        "  frontend/src/x.tsx:2",
        "  frontend/src/y.tsx:2",
    ]
    assert out[-1] == "Each look belongs to one component or one *-looks.ts entry."
    tree(tmp_path, {"frontend/src/y.tsx": 'const Y = () => <p className="b a">y</p>\n'})
    assert main(["looks", str(tmp_path)]) == 0
    assert capsys.readouterr().out.strip() == "3 class strings, none written twice"
