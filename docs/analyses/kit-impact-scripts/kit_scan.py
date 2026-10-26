"""Kit impact facts for a project's transcripts, read in time order.

A transcript file is not in time order: after a compact boundary it replays the preserved tail of
the old conversation with the old timestamps, and a fork starts with a copy of its parent. So all
records are merged, deduplicated by uuid (assistant records also by message id), sorted by timestamp,
and a segment is the interval between two boundaries.

Usage: kit_scan.py <project-dir> [<project-dir>...]  -> one JSON object on stdout.
Relative prices, input token = 1: cache read 0.1, cache write 1.25, output 5.
"""
import glob, json, os, re, sys, collections

READ, WRITE, OUT = 0.1, 1.25, 5.0
WINDOW, AFTER = 15, 30
TRIVIAL = re.compile(r"^(git (status|diff|log|branch|show|rev-parse)|ls|pwd|cat |head |date|echo |which )")
CATS = [
    ("lint feedback after an edit", re.compile(r"left this in")),
    ("formatter changed the file", re.compile(r"hook modified")),
    ("prose tells", re.compile(r"Banned prose tells")),
    ("context warning", re.compile(r"Context at [\d,]+ tokens")),
    ("suppression reason", re.compile(r"writes a suppression")),
    ("test log line", re.compile(r"The last test run")),
    ("heredoc nudge", re.compile(r"Python heredoc")),
]

def blocks(m):
    c = m.get("content")
    return c if isinstance(c, list) else []

def text_of(c):
    if isinstance(c, str):
        return c
    return " ".join(b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text")

def rlen(c):
    if isinstance(c, str):
        return len(c)
    if isinstance(c, list):
        return sum(len(b.get("text", "")) for b in c if isinstance(b, dict))
    return 0

def ctx(u):
    return u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0) + u.get("cache_creation_input_tokens", 0)

def units(u):
    return (u.get("input_tokens", 0) + READ * u.get("cache_read_input_tokens", 0)
            + WRITE * u.get("cache_creation_input_tokens", 0) + OUT * u.get("output_tokens", 0))

def load(d):
    recs, seen_u, seen_m = [], set(), set()
    for fi, f in enumerate(sorted(glob.glob(os.path.join(d, "*.jsonl")))):
        for ri, l in enumerate(open(f)):
            try:
                r = json.loads(l)
            except Exception:
                continue
            ts = r.get("timestamp")
            if not ts or r.get("uuid") in seen_u:
                continue
            seen_u.add(r.get("uuid"))
            recs.append((ts, fi, ri, r))
    recs.sort(key=lambda t: t[:3])
    out = []
    tools_of = {}
    seen_t = set()
    for ts, _, _, r in recs:
        if r.get("type") == "assistant":
            mid = r["message"].get("id") or r.get("uuid")
            for b in blocks(r["message"]):
                if b.get("type") == "tool_use" and b["id"] not in seen_t:
                    seen_t.add(b["id"])
                    tools_of.setdefault(mid, []).append(b)
    for ts, _, _, r in recs:
        if r.get("type") == "assistant":
            mid = r["message"].get("id") or r.get("uuid")
            r["_first"] = mid not in seen_m
            r["_tools"] = tools_of.get(mid, []) if r["_first"] else []
            seen_m.add(mid)
        out.append(r)
    return out

def kind_of(t):
    s = t.strip()
    if not s:
        return "empty"
    if "<command-name>/compact" in s[:120]:
        return "compact"
    if "handoff" in s[:120] and "<command-" in s[:60]:
        return "handoff"
    if "<command-name>/clear" in s[:80] or s.startswith("<local-command"):
        return "local"
    if s.startswith("<task-notification") or s.startswith("<system"):
        return "automatic"
    if s.startswith("[Request interrupted"):
        return "interrupt"
    return "ask"

def scan(d):
    recs = load(d)
    results = {}
    for r in recs:
        if r.get("type") == "user" and isinstance(r["message"]["content"], list):
            for b in r["message"]["content"]:
                if b.get("type") == "tool_result":
                    results[b.get("tool_use_id")] = rlen(b.get("content"))
    bounds = [i for i, r in enumerate(recs) if r.get("subtype") == "compact_boundary"]
    reqs = [(i, r) for i, r in enumerate(recs) if r.get("type") == "assistant" and r["_first"] and (r["message"].get("usage") or {})]
    prompts = collections.Counter()
    inject = collections.defaultdict(lambda: [0, 0])
    lint = []
    handoff_prompt_at = {}
    for i, r in enumerate(recs):
        if r.get("type") == "user" and not r.get("isMeta") and not r.get("isCompactSummary"):
            c = r["message"]["content"]
            if isinstance(c, str) or not any(b.get("type") == "tool_result" for b in c if isinstance(b, dict)):
                prompts[kind_of(text_of(c))] += 1
        a = r.get("attachment")
        if isinstance(a, dict) and a.get("type") == "hook_additional_context":
            txt = a.get("content")
            txt = txt if isinstance(txt, str) else json.dumps(txt)
            cat = next((n for n, rx in CATS if rx.search(txt or "")), "other")
            inject[cat][0] += 1
            inject[cat][1] += len(txt or "")
            m = re.search(r"left this in (\S+?):", txt or "")
            if m:
                lint.append((i, m.group(1)))
    # lint feedback followed by an edit of the same file within the next five requests
    req_pos = [i for i, _ in reqs]
    fixed = fixed20 = 0
    for i, path in lint:
        for lim, name in ((5, "f5"), (20, "f20")):
            hit = False
            for p in [p for p in req_pos if p > i][:lim]:
                for b in recs[p].get("_tools", []):
                    if b.get("type") == "tool_use" and b["name"] in ("Edit", "Write") and b["input"].get("file_path") == path:
                        hit = True
            if name == "f5":
                fixed += hit
            else:
                fixed20 += hit
    comps = []
    prev = -1
    read_paths_seen = set()
    last_i = 0
    for k, bi in enumerate(bounds):
        nxt_b = bounds[k + 1] if k + 1 < len(bounds) else len(recs)
        before = recs[prev + 1:bi]
        after = recs[bi + 1:nxt_b]
        for x in recs[last_i:bi]:
            if x.get("type") == "assistant":
                for b in x.get("_tools", []):
                    if b.get("type") == "tool_use" and b["name"] == "Read":
                        read_paths_seen.add(b["input"].get("file_path", ""))
        last_i = bi
        handoff_text, handoff_at, clear_point, lastc, edits = "", None, False, -1, []
        warn_at = None
        for j, x in enumerate(before):
            if x.get("type") == "assistant":
                for b in x.get("_tools", []):
                    if b.get("type") != "tool_use":
                        continue
                    if b["name"].endswith("clear_point"):
                        clear_point = True
                    if b["name"] in ("Write", "Edit") and "CLAUDE.local.md" in b["input"].get("file_path", ""):
                        handoff_text = json.dumps(b["input"])
                        handoff_at = x["timestamp"]
                    elif b["name"] == "Bash" and "CLAUDE.local.md" in b["input"].get("command", "") and re.search(r">|tee|cp |mv ", b["input"].get("command", "")):
                        handoff_text = b["input"].get("command", "")
                        handoff_at = x["timestamp"]
                    elif b["name"] in ("Write", "Edit"):
                        edits.append(j)
                    if b["name"] == "Bash" and "git commit" in b["input"].get("command", ""):
                        lastc = j
            a = x.get("attachment")
            if isinstance(a, dict) and a.get("type") == "hook_additional_context" and warn_at is None:
                txt = a.get("content")
                txt = txt if isinstance(txt, str) else json.dumps(txt)
                if "Context at" in (txt or ""):
                    warn_at = j
            if x.get("type") == "user" and not x.get("isMeta"):
                c = x["message"]["content"]
                if (isinstance(c, str) or not any(b.get("type") == "tool_result" for b in c if isinstance(b, dict))) and kind_of(text_of(c)) == "handoff":
                    handoff_prompt_at[k] = x["timestamp"]
        prior_bash = set()
        for x in before:
            if x.get("type") == "assistant":
                for b in x.get("_tools", []):
                    if b.get("type") == "tool_use" and b["name"] == "Bash":
                        prior_bash.add(re.sub(r"\s+", " ", b["input"].get("command", "")).strip())
        areqs = [x for x in after if x.get("type") == "assistant" and x["_first"] and (x["message"].get("usage") or {})]
        asks = repeats = 0
        reads = []
        rep = []
        for n, x in enumerate(areqs):
            for b in x.get("_tools", []):
                if b.get("type") != "tool_use":
                    continue
                if n < AFTER:
                    if b["name"] == "AskUserQuestion":
                        asks += 1
                    if b["name"] == "Bash":
                        c = re.sub(r"\s+", " ", b["input"].get("command", "")).strip()
                        if c in prior_bash and not TRIVIAL.match(c) and c not in rep:
                            rep.append(c)
                if n < WINDOW and b["name"] == "Read":
                    p = b["input"].get("file_path", "")
                    base = os.path.basename(p)
                    reads.append(dict(path=base, chars=results.get(b["id"], 0), read_before=p in read_paths_seen,
                                      named=base in handoff_text or base == "CLAUDE.local.md"))
        summary = next((len(text_of(x["message"]["content"])) // 4 for x in recs[max(0, bi - 3):bi + 12] if x.get("isCompactSummary")), 0)
        seg_reads = []
        for n, x in enumerate(areqs):
            for b in x.get("_tools", []):
                if b.get("type") == "tool_use" and b["name"] == "Read":
                    p = b["input"].get("file_path", "")
                    seg_reads.append(dict(path=os.path.basename(p), chars=results.get(b["id"], 0), again=p in read_paths_seen, left=len(areqs) - n))
        fu = (areqs[0]["message"]["usage"] if areqs else {})
        meta = recs[bi]["compactMetadata"]
        comps.append(dict(
            ts=recs[bi]["timestamp"], pre=meta["preTokens"], dur=meta.get("durationMs", 0) // 1000, trigger=meta.get("trigger"),
            post=ctx(fu), post_written=fu.get("cache_creation_input_tokens", 0), post_read=fu.get("cache_read_input_tokens", 0),
            summary_tokens=summary, requests_before=sum(1 for x in before if x.get("type") == "assistant" and x["_first"]),
            requests_after=len(areqs), handoff=bool(handoff_text), clear_point=clear_point,
            edits_in_flight=sum(1 for j in edits if j > lastc), asks_after=asks, repeats_after=len(rep), repeat_cmds=[c[:80] for c in rep][:3],
            reads=reads, seg_reads=seg_reads, warned=warn_at is not None,
            warn_requests=(sum(1 for x in before[warn_at:] if x.get("type") == "assistant" and x["_first"]) if warn_at is not None else None),
            handoff_prompt_to_boundary_s=None,
        ))
        prev = bi
    # handoff prompt to boundary seconds
    import datetime
    def t(s):
        return datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))
    for k, c in enumerate(comps):
        if k in handoff_prompt_at:
            c["handoff_prompt_to_boundary_s"] = round((t(c["ts"]) - t(handoff_prompt_at[k])).total_seconds())
    series = [ctx(r["message"]["usage"]) for _, r in reqs]
    return dict(requests=len(reqs), units=sum(units(r["message"]["usage"]) for _, r in reqs),
                out_tokens=sum(r["message"]["usage"].get("output_tokens", 0) for _, r in reqs),
                prompts=dict(prompts), inject={k: v for k, v in inject.items()}, lint=dict(fires=len(lint), fixed_in_5=fixed, fixed_in_20=fixed20),
                comps=comps, series=series, first_request_ctx=series[0] if series else 0)

if __name__ == "__main__":
    dirs = sys.argv[1:]
    print(json.dumps(scan(dirs[0]) if len(dirs) == 1 else [scan(d) for d in dirs]))
