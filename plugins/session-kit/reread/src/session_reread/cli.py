"""session-reread: which sections of the Markdown files a session changed to read again, and how.

Writes a page, prints a summary per file and the page's path. With no files, every Markdown file
that differs from the baseline, untracked ones included.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from session_reread.baseline import Baseline, find, git, prompts, transcript
from session_reread.page import FileReport, page, summary
from session_reread.sections import compare

OUT = Path.home() / ".claude" / "session-kit" / "reread"


def say(line: str) -> None:
    """Print a line of the command's output."""
    sys.stdout.write(f"{line}\n")


def changed_markdown(root: Path, ref: str) -> list[str]:
    """Return the Markdown files that differ from the ref, untracked ones included."""
    tracked = git(root, "diff", "--name-only", ref, "--", "*.md") or ""
    untracked = git(root, "ls-files", "--others", "--exclude-standard", "--", "*.md") or ""
    return sorted({p for p in (tracked + untracked).splitlines() if p.strip()})


def markdown_in(root: Path, given: list[str]) -> list[str]:
    """Return the files named, with each directory's Markdown files in its place."""
    paths: list[str] = []
    for name in given:
        p = Path(name).resolve()
        found = sorted(p.rglob("*.md")) if p.is_dir() else [p]
        paths.extend(str(f.relative_to(root)) for f in found)
    return paths


def reports_for(root: Path, ref: str, paths: list[str], threshold: float) -> list[FileReport]:
    """Return each changed file's verdicts, the unchanged files left out."""
    reports: list[FileReport] = []
    for path in paths:
        old = git(root, "show", f"{ref}:{path}") or ""
        file = root / path
        gone = not file.is_file()
        new = "" if gone else file.read_text(encoding="utf-8")
        if old != new:
            reports.append(FileReport(path, compare(old, new, threshold), gone))
    return reports


def parse(argv: list[str] | None) -> argparse.Namespace:
    """Read the command line."""
    parser = argparse.ArgumentParser(prog="session-reread", description=__doc__)
    parser.add_argument(
        "files", nargs="*", help="Markdown files or directories, by default every changed one"
    )
    parser.add_argument(
        "--since",
        help="the git ref you read, by default HEAD when your prompt opened the turn that "
        "last committed to the files",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.4,
        help="the share of a section's words changed above which it is rewritten (0.4)",
    )
    parser.add_argument("--out", help="where to write the page")
    parser.add_argument("--open", action="store_true", help="open the page in the default browser")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the command."""
    args = parse(argv)
    top = git(Path.cwd(), "rev-parse", "--show-toplevel")
    if top is None:
        sys.stderr.write("session-reread: not inside a git checkout\n")
        return 2
    root = Path(top.strip())
    given = markdown_in(root, args.files)
    if args.since:
        base = Baseline(args.since, f"{args.since}, as asked")
    else:
        found = transcript(root)
        base = find(root, given or ["*.md"], prompts(found) if found else [])
    if git(root, "rev-parse", "--verify", "--quiet", base.ref + "^{commit}") is None:
        sys.stderr.write(f"session-reread: {base.ref} is not a commit\n")
        return 2
    reports = reports_for(root, base.ref, given or changed_markdown(root, base.ref), args.threshold)
    say(f"Compared with {base.why}.")
    if not reports:
        say("No Markdown file changed.")
        return 0
    stamp = time.strftime("%Y%m%d-%H%M%S")
    out = (
        Path(args.out)
        if args.out
        else OUT / f"{re.sub(r'[^A-Za-z0-9]', '-', root.name)}-{stamp}.html"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page(reports, base.why, args.threshold), encoding="utf-8")
    say(summary(reports))
    say(str(out))
    opener = shutil.which("open")
    if args.open and opener:
        subprocess.run([opener, str(out)], check=False)  # noqa: S603  macOS open on the page just written
    return 0
