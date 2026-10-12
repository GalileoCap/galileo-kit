"""The bundled rewrite recipes: ast-grep rules to copy, retarget and run."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

DIRECTORY = Path(__file__).resolve().parent / "recipes"
"""Where the rule files and ``index.toml`` are installed."""


@dataclass(frozen=True, slots=True)
class Recipe:
    """A bundled rewrite template: an ast-grep rule to copy and retarget."""

    name: str
    """The rule's id, and its file's stem."""
    purpose: str
    """One line: what the recipe is for, from ``index.toml``."""
    path: Path
    """The rule file, absolute."""


class UnknownRecipeError(LookupError):
    """A name no bundled recipe has; carries the names that exist."""

    name: str
    known: tuple[str, ...]

    def __init__(self, name: str, known: Sequence[str]) -> None:
        """Name the recipe asked for and every one that exists."""
        super().__init__(f"unknown recipe '{name}'; known: {', '.join(known)}")
        self.name = name
        self.known = tuple(known)


def bundled() -> list[Recipe]:
    """Every recipe this package ships, sorted by name.

    Raises:
        LookupError: a rule file has no purpose in ``index.toml`` — a
            packaging mistake, never a consumer's.

    """
    purposes = tomllib.loads((DIRECTORY / "index.toml").read_text(encoding="utf-8"))
    recipes: list[Recipe] = []
    for path in sorted(DIRECTORY.glob("*.yml")):
        if path.stem not in purposes:
            msg = f"{path.name} has no one-line purpose in index.toml"
            raise LookupError(msg)
        purpose: str = purposes[path.stem]
        recipes.append(Recipe(name=path.stem, purpose=purpose, path=path))
    return recipes


def find(name: str) -> Recipe:
    """Return the recipe called ``name``.

    Raises:
        UnknownRecipeError: no bundled recipe has that name.

    """
    recipes = bundled()
    for recipe in recipes:
        if recipe.name == name:
            return recipe
    raise UnknownRecipeError(name, [recipe.name for recipe in recipes])
