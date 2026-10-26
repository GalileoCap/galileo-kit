"""What a restart is made of, from the api-request records of the first request after each compaction.

For every compact boundary the first main-loop request after it is read back: its usage gives the
total context and what was read from the cache (the tools and system prompt, the same at every
restart), and its blobs give the messages by source. The messages' share of the usage is split by
characters, which assumes one density of characters per token across the sources.

Usage: restart_sources.py <project-dir>...   (one JSON object per project on stdout)
Run it with python3 -I.
"""
import glob, json, os, re, statistics as st, sys

SECTIONS = [
    ("restored files", r"^Called the \w+ tool with the following input"),
    ("invoked skills", r"^The following skills were invoked EARLIER"),
    ("deferred tools", r"^The following deferred tools are now available"),
    ("agent listing", r"^Available agent types for the Agent tool"),
    ("skill listing", r"^The following skills are available for use with the Skill tool"),
    ("mcp instructions", r"^# MCP Server Instructions"),
    ("environment", r"^# Environment"),
]


def text_of(content):
    if isinstance(content, str):
        return [content]
    return [b.get("text", json.dumps(b)) for b in content]


def split_system(text):
    """The system-role message's text cut at its section markers: {source: chars}."""
    marks = []
    for name, rx in SECTIONS:
        for m in re.finditer(rx, text, re.M):
            marks.append((m.start(), name))
    marks.sort()
    out = {}
    if not marks or marks[0][0] > 0:
        out["system other"] = (marks[0][0] if marks else len(text))
    for i, (pos, name) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(text)
        out[name] = out.get(name, 0) + end - pos
    return out


def split_reminder(text):
    """The first user reminder: the rule files by their 'Contents of' headings."""
    marks = [(m.start(), m.group(1)) for m in re.finditer(r"^Contents of (\S+)", text, re.M)]
    out = {}
    head = marks[0][0] if marks else len(text)
    out["reminder preamble"] = head
    for i, (pos, path) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(text)
        if "CLAUDE.local.md" in path:
            name = "CLAUDE.local.md"
        elif path.startswith(os.path.expanduser("~/.claude")) or "/.claude/CLAUDE.md" in path:
            name = "global rules"
        elif "/rules/" in path:
            name = "project rules"
        else:
            name = "project CLAUDE.md"
        out[name] = out.get(name, 0) + end - pos
    return out


def classify_user(text):
    if text.startswith("This session is being continued"):
        return {"summary": len(text)}
    if text.startswith("<system-reminder>") and "Contents of" in text[:600]:
        return split_reminder(text)
    if text.startswith("<system-reminder>") and "gitStatus" in text[:1200]:
        return {"git status and email": len(text)}
    if text.startswith("<local-command") or text.startswith("<command-name>"):
        return {"compact command echo": len(text)}
    if "plugin sent a message" in text[:60]:
        return {"continue prompt": len(text)}
    return {"user other": len(text)}


def skill_sizes(text):
    """The re-attached skills of a system message, by name: {name: chars}."""
    i = text.find("The following skills were invoked EARLIER")
    if i < 0:
        return {}
    j = text.find("The following deferred tools", i)
    parts = re.split(r"^### Skill: ", text[i:j if j > 0 else len(text)], flags=re.M)[1:]
    return {p.split("\n", 1)[0]: len(p) for p in parts}


def kit_listing_chars(text):
    """The characters of the skill listing's session-kit entries."""
    i = text.find("The following skills are available for use with the Skill tool")
    if i < 0:
        return 0
    j = text.find("# MCP Server Instructions", i)
    entries = re.split(r"\n(?=- [\w:.-]+: )", text[i:j if j > 0 else len(text)])[1:]
    return sum(len(e) for e in entries if e.startswith("- session-kit:"))


def reads_after(recs, j, requests=15):
    """The Read calls of the first `requests` responses after record j, as (request number, path)."""
    out, ids = [], []
    for x in recs[j + 1:]:
        if x.get("type") != "assistant":
            continue
        mid = x["message"].get("id")
        if mid not in ids:
            ids.append(mid)
        if len(ids) > requests:
            break
        content = x["message"]["content"]
        for b in content if isinstance(content, list) else []:
            if b.get("type") == "tool_use" and b["name"] == "Read":
                out.append((ids.index(mid), b["input"].get("file_path")))
    return out


def scan(d):
    files = sorted(glob.glob(os.path.join(d, "*.jsonl")))
    blobs, shapes = {}, {}
    for f in files:
        for l in open(f):
            if '"api-request-blob"' in l[:40]:
                r = json.loads(l)
                blobs[r["hash"]] = r["message"]
            elif '"api-request-shape"' in l[:40]:
                r = json.loads(l)
                shapes[r["shapeHash"]] = r["shape"]
    rows, seen = [], set()
    for f in files:
        recs = [json.loads(l) for l in open(f)]
        for b, r in enumerate(recs):
            if r.get("subtype") != "compact_boundary" or r["uuid"] in seen:
                continue
            seen.add(r["uuid"])
            req = next((x for x in recs[b + 1:] if x.get("type") == "api-request"), None)
            if req is None or req["keep"] != 0 or any(t not in blobs for t in req["tail"]):
                continue
            j = recs.index(req)
            ans = next((x for x in recs[j + 1:] if x.get("type") == "assistant" and x["message"].get("usage")), None)
            if ans is None:
                continue
            u = ans["message"]["usage"]
            read, wrote, plain = u.get("cache_read_input_tokens", 0), u.get("cache_creation_input_tokens", 0), u.get("input_tokens", 0)
            chars = {}
            restored = []
            skills, listing_kit = {}, 0
            for h in req["tail"]:
                m = blobs[h]
                for t in text_of(m["content"]):
                    parts = split_system(t) if m["role"] == "system" else classify_user(t) if m["role"] == "user" else {"assistant echo": len(t)}
                    for k, v in parts.items():
                        chars[k] = chars.get(k, 0) + v
                    if m["role"] == "system":
                        restored += re.findall(r'^Called the Read tool with the following input: \{"file_path":"([^"]+)"', t, re.M)
                        skills.update(skill_sizes(t))
                        listing_kit += kit_listing_chars(t)
            shape = shapes.get(req["shapeHash"], {})
            tools = shape.get("tools", [])
            rows.append(dict(
                file=os.path.basename(f)[:8], ts=r["timestamp"], total=read + wrote + plain, read=read, wrote=wrote,
                pre=r["compactMetadata"]["preTokens"], chars=chars, restored=restored,
                skills=skills, listing_kit=listing_kit,
                tools_chars=len(json.dumps(tools, ensure_ascii=False)), system_chars=len(json.dumps(shape.get("system", []), ensure_ascii=False)),
                tool_sizes={t.get("name"): len(json.dumps(t, ensure_ascii=False)) for t in tools},
                follow=reads_after(recs, j),
            ))
    return rows


TOOL_GROUPS = [
    ("Artifact tool", lambda n: n == "Artifact"),
    ("app MCP tools", lambda n: n.startswith("mcp__") and not n.startswith("mcp__session-kit__")),
    ("kit tools", lambda n: n.startswith("mcp__session-kit__")),
]
MESSAGE_GROUPS = {
    "kit": ["global rules", "CLAUDE.local.md", "compact command echo", "continue prompt"],
    "project": ["project CLAUDE.md", "project rules"],
    "compaction": ["summary", "restored files", "assistant echo", "user other", "system other"],
    "setup and app": ["skill listing", "deferred tools", "agent listing", "mcp instructions", "environment", "git status and email", "reminder preamble"],
}
KIT_SKILLS = ("session-kit:handoff", "session-kit:iterate")
MED = lambda v: round(st.median(v)) if v else 0


def groups(rows):
    """Tokens of a restart by who controls them: the prefix by tool group, the messages by source."""
    warm = [r for r in rows if r["read"] > 40000]
    prefix = MED([r["read"] for r in warm])
    out = {k: [] for k in ["tools: Artifact", "tools: app MCP", "tools: kit", "tools: engine built-in", "system prompt"]}
    for g in MESSAGE_GROUPS:
        out[f"messages: {g}"] = []
    out["messages: kit skills (handoff body, listing)"] = []
    out["messages: skills of the project and others"] = []
    for r in rows:
        density = (r["tools_chars"] + r["system_chars"]) / prefix
        sizes = r["tool_sizes"]
        grouped = {name: sum(v for n, v in sizes.items() if pick(n)) for name, pick in TOOL_GROUPS}
        out["tools: Artifact"].append(grouped["Artifact tool"] / density)
        out["tools: app MCP"].append(grouped["app MCP tools"] / density)
        out["tools: kit"].append(grouped["kit tools"] / density)
        out["tools: engine built-in"].append((sum(sizes.values()) - sum(grouped.values())) / density)
        out["system prompt"].append(r["system_chars"] / density)
        msg = r["total"] - prefix
        per_char = msg / sum(r["chars"].values())
        for g, keys in MESSAGE_GROUPS.items():
            out[f"messages: {g}"].append(per_char * sum(r["chars"].get(k, 0) for k in keys))
        kit_skill = sum(v for n, v in r["skills"].items() if n in KIT_SKILLS)
        out["messages: kit skills (handoff body, listing)"].append(per_char * (kit_skill + r["listing_kit"]))
        out["messages: skills of the project and others"].append(per_char * (r["chars"].get("invoked skills", 0) - kit_skill))
    return {k: MED(v) for k, v in out.items()}


def report(name, rows, kit=None):
    if not rows:
        print(name, "no restarts read")
        return
    print(f"== {name}: {len(rows)} restarts")
    print(f"   total context {MED([r['total'] for r in rows]):,}; cache read {MED([r['read'] for r in rows]):,}; written {MED([r['wrote'] for r in rows]):,}")
    print(f"   tools {MED([r['tools_chars'] for r in rows]):,} chars, system {MED([r['system_chars'] for r in rows]):,} chars")
    for k, v in groups(rows).items():
        print(f"   {k:48s} {v:>7,} tokens")
    restored = sum(len(set(r["restored"])) for r in rows)
    again = sum(len(set(r["restored"]) & {p for _, p in r["follow"]}) for r in rows)
    print(f"   restored files read again in the first 15 requests: {again} of {restored}")
    if kit:
        cost_per_1k(rows, kit)


def cost_per_1k(rows, kit):
    """What 1,000 tokens cost in the prefix and in the restart, as a share of the session's modeled cost."""
    k = json.load(open(kit))
    per_request = k["units"] / k["requests"]
    cs = k["comps"]
    carried = st.median(c["requests_after"] for c in cs)
    print(f"   a request costs {per_request / 1e3:.1f}k units; 1k tokens of prefix: {1000 * 0.1 * k['requests'] / k['units']:.2%} of the session; "
          f"1k tokens of restart messages: {1000 * (1.25 + 0.1 * carried) * len(cs) / k['units']:.2%} ({len(cs)} compactions, {carried:.0f} requests carried)")


if __name__ == "__main__":
    out = {}
    for arg in sys.argv[1:]:
        d, _, kit = arg.partition("=")
        name = os.path.basename(d.rstrip("/"))
        out[name] = scan(d)
        report(name, out[name], kit or None)
    json.dump(out, open(os.environ.get("RESTART_JSON", os.devnull), "w"))
