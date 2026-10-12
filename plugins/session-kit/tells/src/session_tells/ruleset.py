"""Every rule the tells gate reads: the English table and the translated trees' tables."""

from __future__ import annotations

from session_tells import rules, rules_translated

BANNED: tuple[rules.Rule, ...] = rules.BANNED + rules_translated.BANNED
RATIONED: tuple[rules.Rule, ...] = rules.RATIONED + rules_translated.RATIONED
RULES: tuple[rules.Rule, ...] = BANNED + RATIONED
