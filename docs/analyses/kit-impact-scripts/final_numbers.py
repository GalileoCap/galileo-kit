"""Cost shares and the threshold replay, from kit_scan.py output files. Usage: final_numbers.py name=file ..."""
import json, statistics as st, sys
READ, WRITE, OUT = 0.1, 1.25, 5.0
for arg in sys.argv[1:]:
    name, f = arg.split("=")
    d = json.load(open(f)); cs = d["comps"]; N = len(cs); U = d["units"]
    summ = sum(c["pre"] * READ + c["summary_tokens"] * OUT for c in cs)
    restart = sum(c["post_written"] * WRITE for c in cs)
    carry = sum(c["summary_tokens"] * (WRITE + READ * c["requests_after"]) for c in cs)
    rr = sum(r["chars"] / 4 * (WRITE + READ * r["left"]) for c in cs for r in c["seg_reads"] if r["again"])
    inj = sum(v[1] for v in d["inject"].values()) / 4
    inj_units = inj * (WRITE + READ * 60)  # about 60 requests of carrying to the next compaction
    print(f"== {name}: requests {d['requests']}, units {U/1e6:.1f}M, per request {U/d['requests']/1e3:.1f}k")
    print(f"   compaction machinery: summarising {summ/U:.1%}, restart rewrite {restart/U:.1%}, carried summary {carry/U:.1%}, re-reads of files read before {rr/U:.1%}; total {(summ+restart+carry+rr)/U:.1%}")
    print(f"   kit text injected by hooks: {inj:,.0f} tokens, about {inj_units/U:.2%} of units")
    s = d["series"]
    inc = [b - a for a, b in zip(s, s[1:]) if 0 < b - a < 60000]
    post = st.median(c["post"] for c in cs); wr = st.median(c["post_written"] for c in cs); sumt = st.median(c["summary_tokens"] for c in cs)
    rows = []
    for T in (150e3, 200e3, 260e3, 320e3, 400e3, 600e3):
        x = post; cost = 0; n = 0
        for g in inc:
            x += g; cost += READ * x
            if x >= T:
                cost += READ * x + sumt * OUT + wr * WRITE; x = post; n += 1
        rows.append((int(T / 1e3), n, cost))
    best = min(r[2] for r in rows)
    print("   replay (threshold k: compactions, cost vs best):", "; ".join(f"{t}k: {n}, {c/best:.2f}x" for t, n, c in rows))
