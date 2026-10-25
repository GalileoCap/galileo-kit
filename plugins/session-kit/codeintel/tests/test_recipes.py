"""The bundled recipes: findable by name, and each one correct as a rewrite."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from session_codeintel.cli import main
from session_codeintel.recipes import UnknownRecipeError, bundled, find

AST_GREP = Path(sys.executable).parent / "ast-grep"
"""The pinned binary this package's environment installs — never PATH's."""


def rewrite(recipe: Path, source: str, tmp_path: Path) -> str:
    """Run one recipe over one file, rewriting in place; the file's new text."""
    target = tmp_path / "target.py"
    target.write_text(source)
    subprocess.run(  # noqa: S603  (decisions.md, 1)
        [str(AST_GREP), "scan", "-r", str(recipe), "-U", str(target)],
        check=True,
        capture_output=True,
    )
    return target.read_text()


def test_every_recipe_is_listed_with_a_purpose_and_an_existing_file() -> None:
    """Every bundled recipe has a name, a one-line purpose and its rule file."""
    recipes = bundled()
    assert [r.name for r in recipes] == sorted(r.name for r in recipes)
    assert "api-migration-await-call" in {r.name for r in recipes}
    for recipe in recipes:
        assert recipe.purpose.strip()
        assert "\n" not in recipe.purpose
        assert recipe.path.is_absolute()
        assert recipe.path.is_file()
        assert recipe.path.stem == recipe.name


def test_an_unknown_name_is_refused_with_the_names_that_exist() -> None:
    """A name no recipe has is refused, and the refusal names the ones that exist."""
    with pytest.raises(UnknownRecipeError) as caught:
        find("no-such-recipe")
    assert caught.value.name == "no-such-recipe"
    assert "api-migration-await-call" in caught.value.known


def test_the_cli_lists_paths_and_refuses(capsys: pytest.CaptureFixture[str]) -> None:
    """``recipes list`` and ``recipes path`` answer; an unknown name exits 2 on stderr."""
    assert main(["recipes", "list"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert any(line.startswith("api-migration-await-call\t") for line in lines)

    assert main(["recipes", "path", "api-migration-await-call"]) == 0
    assert Path(capsys.readouterr().out.strip()) == find("api-migration-await-call").path

    assert main(["recipes", "path", "no-such-recipe"]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "no-such-recipe" in captured.err
    assert "api-migration-await-call" in captured.err


class TestApiMigrationAwaitCall:
    """The await-call template: its first documented bug class, and idempotence."""

    def test_a_bare_call_is_awaited(self, tmp_path: Path) -> None:
        """A call that was sync and is now async gains its ``await``."""
        recipe = find("api-migration-await-call").path
        out = rewrite(recipe, "async def f(h):\n    return h.store.history(1)\n", tmp_path)
        assert "return await h.store.history(1)" in out

    def test_the_whole_attribute_chain_is_matched_never_its_middle(self, tmp_path: Path) -> None:
        """The ``await`` goes before the whole chain, never inside it."""
        recipe = find("api-migration-await-call").path
        source = "async def f(harness):\n    x = harness.store.history(1)\n"
        out = rewrite(recipe, source, tmp_path)
        assert "x = await harness.store.history(1)" in out
        assert "harness.await" not in out

    def test_a_rerun_over_a_half_converted_file_awaits_nothing_twice(
        self,
        tmp_path: Path,
    ) -> None:
        """Running the recipe again changes nothing: no ``await await``."""
        recipe = find("api-migration-await-call").path
        source = "async def f(h):\n    a = await h.store.history(1)\n    b = h.store.history(2)\n"
        once = rewrite(recipe, source, tmp_path)
        twice = rewrite(recipe, once, tmp_path)
        assert once == twice
        assert "await await" not in twice
        assert "b = await h.store.history(2)" in twice
