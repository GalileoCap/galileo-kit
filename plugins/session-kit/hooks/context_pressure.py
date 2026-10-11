from __future__ import annotations

"""Warn when the session's context is filling, so work can reach a safe
point before the owner compacts, and make the end of the turn say so.

Why it exists. A compaction that lands mid-run loses whatever was not
written down, and the research on long contexts says the failure mode
before that is worse than the compaction itself: quality degrades well
before any window limit, and the degradation shows up as *unreliability*
rather than as an error anybody notices. So the session needs to be told
it is getting heavy while it can still choose where to stop.

What it measures. The last assistant message in the transcript carries
the real number -- `input_tokens + cache_read_input_tokens +
cache_creation_input_tokens` is exactly what was sent. Nothing in the
hook payload, the environment or the transcript exposes the context
*limit*, so the denominator below is a constant that a model change edits.

Two events. After a tool call (PostToolUse) it warns, every STEP tokens
past the threshold. At the end of a turn (Stop, run with the argument
``stop``) it holds the stop once when the reply says nothing about
compacting, and asks for CLAUDE.local.md and one closing line. The warning
alone arrives in the middle of a turn, and a session deep in a long task
carried on past it and ended without telling the owner. The reader sees the
closing line, so the end of the turn is where it has to be made sure of.

What it does not do. It never blocks a tool call, and it holds a stop at
most once: a stop already held (``stop_hook_active``) goes through.
Anything unexpected exits silently. A monitor that breaks the session it
is monitoring is worse than no monitor.
"""

import json
import os
import re
import sys
import tempfile

# The model's context window, and the trigger at half of it. No API gives
# the window, so a session on a smaller one sets CLAUDE_KIT_CTX_WINDOW.
WINDOW = int(os.environ.get("CLAUDE_KIT_CTX_WINDOW", "1000000"))
THRESHOLD = float(os.environ.get("CLAUDE_KIT_CTX_THRESHOLD", "0.50"))

# How much further it has to climb before it says so again.
STEP = int(os.environ.get("CLAUDE_KIT_CTX_STEP", "25000"))

# Only the tail is read. A long session's transcript reaches tens of MB
# and this runs after every tool call.
TAIL_BYTES = 256 * 1024


# A reply that already speaks of compacting has said what the hold would ask.
SPOKEN = re.compile(r"\bcompact", re.IGNORECASE)


def tail(path: str) -> list[str]:
    """The transcript's last lines, as many as TAIL_BYTES holds."""
    try:
        size = os.path.getsize(path)
        with open(path, "rb") as fh:
            if size > TAIL_BYTES:
                fh.seek(size - TAIL_BYTES)
                fh.readline()  # discard the partial line
            return fh.read().decode("utf-8", "replace").splitlines()
    except OSError:
        return []


def last_reply(lines: list[str]) -> str:
    """The text of the most recent assistant message that has any."""
    for line in reversed(lines):
        try:
            entry = json.loads(line)
            if entry.get("type") != "assistant":
                continue
            blocks = entry["message"]["content"]
        except (ValueError, KeyError, TypeError, AttributeError):
            continue
        if isinstance(blocks, str):
            return blocks
        text = " ".join(
            b.get("text", "") for b in blocks if isinstance(b, dict) and b.get("type") == "text"
        )
        if text:
            return text
    return ""


def last_context_size(path: str) -> int | None:
    """Total input tokens of the most recent assistant message, or None."""
    lines = tail(path)
    for line in reversed(lines):
        try:
            usage = json.loads(line)["message"]["usage"]
        except (ValueError, KeyError, TypeError):
            continue
        total = sum(
            int(usage.get(k) or 0)
            for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")
        )
        if total:
            return total
    return None


def state_path(session_id: str) -> str:
    """Per project directory and session, so two sessions never share a file."""
    worktree = os.path.basename(os.environ.get("CLAUDE_PROJECT_DIR", "unknown")) or "unknown"
    safe = "".join(c for c in session_id if c.isalnum() or c in "-_")[:40] or "nosession"
    return os.path.join(tempfile.gettempdir(), f"claude-kit-ctx-{worktree}-{safe}.json")


def already_warned_at(path: str) -> int:
    try:
        with open(path, encoding="utf-8") as fh:
            return int(json.load(fh).get("warned_at", 0))
    except (OSError, ValueError, TypeError):
        return 0


def record(path: str, tokens: int) -> None:
    try:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"warned_at": tokens}, fh)
    except OSError:
        pass


def advice(pct: float) -> str:
    """What to do next, firmer as the context grows."""
    if pct >= 0.80:
        return (
            "Stop starting anything new. Commit or discard what is in the tree, "
            "write CLAUDE.local.md now, and end this turn saying you are ready to compact."
        )
    if pct >= 0.65:
        return (
            "End this turn at the next green commit, even with the task unfinished: "
            "write CLAUDE.local.md, reach a clean tree, and tell the user whether it "
            "is safe to compact. Start nothing new before that."
        )
    return (
        "Aim for a safe point: finish the step under the cursor, commit if it is "
        "green, write CLAUDE.local.md, then tell the user it is safe to compact."
    )


def hold(payload: dict[str, object]) -> None:
    """At the end of a turn over the threshold, hold the stop once for the line."""
    if payload.get("stop_hook_active"):
        return
    transcript = payload.get("transcript_path")
    if not isinstance(transcript, str) or not transcript:
        return
    tokens = last_context_size(transcript)
    if tokens is None or tokens < int(WINDOW * THRESHOLD):
        return
    if SPOKEN.search(last_reply(tail(transcript))):
        return
    reason = (
        f"Context at {tokens:,} tokens ({tokens / WINDOW:.0%} of {WINDOW:,}). Before "
        "ending this turn, write CLAUDE.local.md, then end your reply with one line "
        "for the user: that it is safe to compact now, or what is not safe yet and why."
    )
    json.dump({"decision": "block", "reason": reason}, sys.stdout)


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return
    if not isinstance(payload, dict):
        return
    if sys.argv[1:] == ["stop"]:
        hold(payload)
        return

    transcript = payload.get("transcript_path")
    if not transcript:
        return

    tokens = last_context_size(transcript)
    if tokens is None:
        return

    trigger = int(WINDOW * THRESHOLD)
    if tokens < trigger:
        return

    path = state_path(str(payload.get("session_id", "")))
    warned = already_warned_at(path)
    # A context smaller than the last warning has been compacted: warn afresh.
    if warned and warned <= tokens < warned + STEP:
        return

    pct = tokens / WINDOW
    record(path, tokens)

    msg = (
        f"Context at {tokens:,} tokens ({pct:.0%} of {WINDOW:,}). "
        f"{advice(pct)}"
    )
    json.dump(
        {
            "systemMessage": msg,
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": msg,
            },
        },
        sys.stdout,
    )


if __name__ == "__main__":
    main()
