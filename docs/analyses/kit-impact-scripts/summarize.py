import json,statistics as st
names=[('lane1','k-lane1.json'),('demo-mat-porting','k-demo-mat-porting.json'),('mat-lib','k-mat-lib.json'),('JUNE mat-lib','k-base-mat-lib.json'),('JUNE cx-opt','k-base-cx.json')]
def m(v): return round(st.median(v)) if v else None
for n,f in names:
    d=json.load(open(f)); cs=d['comps']; N=len(cs)
    print('=====',n,'requests',d['requests'],'compactions',N,'req/compaction',round(d['requests']/N,1),'units M',round(d['units']/1e6,1),'prompts',d['prompts'])
    print(' pre: median',m([c['pre'] for c in cs]),'max',max(c['pre'] for c in cs),'>300k',sum(c['pre']>300000 for c in cs),'<200k',sum(c['pre']<200000 for c in cs),'| triggers',{t:sum(1 for c in cs if c['trigger']==t) for t in set(c['trigger'] for c in cs)})
    print(' dur s median',m([c['dur'] for c in cs]),'| post median',m([c['post'] for c in cs]),'written at restart median',m([c['post_written'] for c in cs]),'summary tok median',m([c['summary_tokens'] for c in cs]),'| first request ctx',d['first_request_ctx'])
    print(' handoff before',sum(c['handoff'] for c in cs),'clear_point',sum(c['clear_point'] for c in cs),'warned',sum(c['warned'] for c in cs),'| edits in flight at boundary: compactions',sum(1 for c in cs if c['edits_in_flight']),'edits',sum(c['edits_in_flight'] for c in cs))
    print(' AskUserQuestion in first 30 requests after: compactions',sum(1 for c in cs if c['asks_after']),'questions',sum(c['asks_after'] for c in cs),'| repeated non-trivial Bash: compactions',sum(1 for c in cs if c['repeats_after']),[x for c in cs for x in c['repeat_cmds']][:3])
    hp=[c['handoff_prompt_to_boundary_s'] for c in cs if c['handoff_prompt_to_boundary_s'] is not None]
    print(' handoff prompt->boundary s median',m(hp),'max',max(hp) if hp else None,'n',len(hp),'| warn->compact requests median',m([c['warn_requests'] for c in cs if c['warn_requests'] is not None]),'max',max([c['warn_requests'] for c in cs if c['warn_requests'] is not None] or [0]))
    print(' requests_after median',m([c['requests_after'] for c in cs]),'sum',sum(c['requests_after'] for c in cs))
    rs=[(c,r) for c in cs for r in c['reads']]
    rb=[(c,r) for c,r in rs if r['read_before']]
    def tok(l): return sum(r['chars'] for _,r in l)/4
    def unitsum(l): return sum(r['chars']/4*(1.25+0.1*c['requests_after']) for c,r in l)
    print(' reads in first 15 requests:',len(rs),'tokens',round(tok(rs)),'| of files read earlier in the session:',len(rb),'tokens',round(tok(rb)),'per compaction',round(tok(rb)/N),'share of units',f"{unitsum(rb)/d['units']:.1%}")
    nm=[(c,r) for c,r in rb if r['named']]; un=[(c,r) for c,r in rb if not r['named']]
    print('   named by handoff',len(nm),round(tok(nm)),'tok | chosen by model',len(un),round(tok(un)),'tok | first-time reads',len(rs)-len(rb),round(tok(rs)-tok(rb)),'tok')
    print(' lint',d['lint'],'| inject tokens',sum(v[1] for v in d['inject'].values())//4,{k:(v[0],v[1]//max(v[0],1)) for k,v in d['inject'].items()})
