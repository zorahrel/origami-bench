#!/usr/bin/env python3
"""Builds index.html (public page) from runs/<date>/ and results. Usage: site.py DATE JUDGE_NOTE
Single big player: task tabs + model strip with scores, keyboard arrows, #task/model
deep links, clip/live/compare modes. Static HTML/CSS/JS, no build step."""
import sys, json, pathlib, html
ROOT = pathlib.Path(__file__).resolve().parent
date, judge_note = sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else ""
OUT = sys.argv[3] if len(sys.argv) > 3 else "index.html"
NAMES = {"sonnet-5.5": "Claude Sonnet 5.5", "opus-5.5": "Claude Opus 5.5", "haiku-5.5": "Claude Haiku 5.5",
         "gpt-6-luna": "gpt-6-luna", "gpt-6.1-sol": "gpt-6.1-sol", "gpt-6-sol": "gpt-6-sol",
         "gpt-6-astra": "gpt-6-astra", "gpt-5.6-sol": "gpt-5.6-sol", "gpt-5.6-terra": "gpt-5.6-terra",
         "gpt-5.6-luna": "gpt-5.6-luna",
         "muse-spark-1.3": "Muse Spark 1.3", "muse-wonder-full": "Muse Wonder Full 1.0",
         "free-auto": "free-auto (free router)"}
TASKS = [("walker", "Parkour + combat gauntlet"), ("physics", "Extreme Rube-Goldberg"),
         ("gears", "Clockwork orrery-automaton"), ("shader", "Rich raymarched SDF")]
base = ROOT / "runs" / date
models = [m for m in NAMES if (base / m).exists()]
def effort_of(m):
    for t, _ in TASKS:
        f = base / m / t / "meta.json"
        if f.exists(): return json.loads(f.read_text()).get("effort") or "unrecorded"
    return "unrecorded"
EFFORT = {m: effort_of(m) for m in models}
LABEL = {m: f"{NAMES[m]} \u00b7 {EFFORT[m]}" for m in models}  # e.g. "Claude Opus 5.5 · max"
cells, rows = {}, []
for m in models:
    d = {}
    for t, _ in TASKS:
        c = base / m / t
        if not (c / "meta.json").exists(): continue
        j = json.loads((c / "judge.json").read_text()) if (c / "judge.json").exists() else {"score": None, "why": "not judged"}
        pj = {}
        for jn in ("codex", "router", "claude"):
            jf = c / f"judge_{jn}.json"
            if jf.exists():
                try: pj[jn] = json.loads(jf.read_text()).get("score")
                except Exception: pass
        mt = json.loads((c / "meta.json").read_text())
        d[t] = {"s": j["score"], "tok": mt.get("out_tokens"), "est": mt.get("out_tokens_estimated"), "sec": mt.get("gen_seconds"), "err": mt.get("error"), "effort": mt.get("effort"), "why": j.get("why", ""),
                "clip": f"runs/{date}/{m}/{t}/clip.mp4" if (c / "clip.mp4").exists() else None,
                "poster": f"runs/{date}/{m}/{t}/poster.jpg" if (c / "poster.jpg").exists() else None,
                "live": f"runs/{date}/{m}/{t}/out.html" if (c / "out.html").exists() else None,
                "pj": pj}
    sc = [v["s"] for v in d.values() if isinstance(v["s"], (int, float))]
    cells[m] = d
    rows.append((m, sum(sc) / len(sc) if sc else 0, len(sc)))
rows.sort(key=lambda r: (-r[1], r[0]))
e = html.escape
def jmean(m, jn):
    v = [c["pj"][jn] for c in cells[m].values() if isinstance(c["pj"].get(jn), (int, float))]
    return f"{sum(v)/len(v):.1f}" if v else "-"
lb = "".join(
    f"<tr><td>{i}</td><td><a href=\"#{TASKS[0][0]}/{m}\" onclick=\"setTimeout(()=>document.getElementById('player').scrollIntoView(),0)\">{e(LABEL[m])}</a></td><td><b>{avg:.1f}</b></td>" +
    "".join(f"<td class=\"j\">{jmean(m, jn)}</td>" for jn in ("codex", "router", "claude")) +
    "".join(f"<td>{cells[m].get(t, {}).get('s') if cells[m].get(t, {}).get('s') is not None else '-'}</td>" for t, _ in TASKS) + "</tr>"
    for i, (m, avg, n) in enumerate(rows, 1))
import itertools, math
def corr(a, b):
    n = len(a)
    if n < 3: return None
    ma, mb = sum(a)/n, sum(b)/n
    va = sum((x-ma)**2 for x in a); vb = sum((y-mb)**2 for y in b)
    return sum((x-ma)*(y-mb) for x, y in zip(a, b)) / math.sqrt(va*vb) if va and vb else None
agree = []
for ja, jb in itertools.combinations(("codex", "router", "claude"), 2):
    pairs = [(c["pj"][ja], c["pj"][jb]) for m in cells for c in cells[m].values() if isinstance(c["pj"].get(ja), (int, float)) and isinstance(c["pj"].get(jb), (int, float))]
    if pairs:
        r = corr([x for x, _ in pairs], [y for _, y in pairs]); d = sum(abs(x-y) for x, y in pairs)/len(pairs)
        agree.append(f"{ja}&ndash;{jb}: r={'n/a' if r is None else f'{r:.2f}'}, mean gap {d:.1f} pt ({len(pairs)} cells)")
AGREE = "Judge agreement (Pearson r over cells, mean absolute gap): " + "; ".join(agree) + "." if agree else ""
show = []
for t, tn in TASKS:
    best = None
    for m in models:
        c = cells[m].get(t)
        if c and isinstance(c["s"], (int, float)) and (best is None or c["s"] > best[0]): best = (c["s"], m)
    hv = ROOT / "docs" / f"hero-{t}.mp4"
    if best and hv.exists():
        show.append(f'<a class="hero" href="#{t}/{best[1]}" onclick="setTimeout(()=>document.getElementById(\'player\').scrollIntoView(),0)"><video muted loop playsinline autoplay preload="metadata" poster="docs/hero-{t}.jpg" src="docs/hero-{t}.mp4"></video><span><b>{e(tn)}</b> &middot; best: {e(LABEL[best[1]])} {best[0]}/10 &middot; open in player</span></a>')
SHOWCASE = ('<h2>Best of each task</h2><div class="heroes">' + "".join(show) + '</div>') if show else ""
data = json.dumps({"date": date, "names": {m: LABEL[m] for m in models},
                   "tasks": [{"id": t, "name": n} for t, n in TASKS], "cells": cells})
page = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>origami-bench: how much can a model fold into 12,000 tokens?</title>
<style>
body{font:16px/1.5 system-ui,sans-serif;max-width:1100px;margin:0 auto;padding:16px;color:#111}
h1{margin:.2em 0;font-size:clamp(22px,4vw,32px)}h2{margin:26px 0 8px}.m{color:#666;font-size:14px}a{color:#5b2ee6}
table.lb{border-collapse:collapse;width:100%;margin:12px 0;font-size:15px}
td.j,th.j{color:#777;font-size:13px}td,th{padding:7px 8px;border-bottom:1px solid #eee;text-align:left}
.heroes{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}.hero{display:block;background:#111;border-radius:12px;overflow:hidden;text-decoration:none}.hero video{width:100%;aspect-ratio:8/5;display:block;background:#000}.hero span{display:block;color:#eee;font-size:13px;padding:7px 10px}@media(max-width:700px){.heroes{grid-template-columns:1fr}}
.tabs{display:flex;gap:6px;overflow-x:auto;padding:4px 0;-webkit-overflow-scrolling:touch}
.tabs button{flex:1 0 auto;border:1px solid #ddd;background:#f6f6f8;border-radius:8px;padding:9px 12px;font-size:15px;cursor:pointer;white-space:nowrap}
.tabs button.on{background:#111;color:#fff;border-color:#111}
#stage{background:#000;border-radius:12px;overflow:hidden;margin-top:10px}
#stage video,#stage iframe{width:100%;aspect-ratio:8/5;display:block;border:0;background:#000}
#stage iframe{display:none}
#stage.live video{display:none}#stage.live iframe{display:block}
#bar{display:flex;gap:8px;align-items:center;margin-top:10px;flex-wrap:wrap}
#bar select{font-size:15px;padding:8px;border-radius:8px;border:1px solid #ddd;max-width:100%}
.mode{display:flex;gap:4px;margin-left:auto}
.mode button{border:1px solid #ddd;background:#fff;border-radius:8px;padding:8px 12px;font-size:14px;cursor:pointer}
.mode button.on{background:#5b2ee6;color:#fff;border-color:#5b2ee6}
#strip{display:flex;gap:6px;overflow-x:auto;padding:8px 0;-webkit-overflow-scrolling:touch}
#strip button{flex:0 0 auto;border:1px solid #ddd;background:#fff;border-radius:8px;padding:8px 10px;font-size:13px;cursor:pointer;text-align:left;width:148px}
#strip button.on{border-color:#5b2ee6;box-shadow:0 0 0 1px #5b2ee6}
#strip img{width:100%;aspect-ratio:8/5;object-fit:cover;border-radius:5px;display:block;margin-bottom:4px}#strip b{display:block;font-size:15px}#strip span{color:#666}
#why{font-size:14px;color:#444;margin:6px 0;min-height:2.2em}
#cmp{display:none;gap:8px}#cmp.on{display:flex}#cmp>div{flex:1;min-width:0}
#cmp video{width:100%;aspect-ratio:8/5;background:#000;border-radius:8px;display:block}
#cmp select{width:100%;margin-top:4px;font-size:14px;padding:7px;border-radius:8px;border:1px solid #ddd}
#cmp p{font-size:13px;color:#444;margin:4px 0}
@media(max-width:640px){#cmp.on{flex-direction:column}.mode{margin-left:0}#strip button{width:128px}}
.nav{font-size:13px;color:#888;margin-top:4px}
</style></head><body>
<h1>\U0001F9A2 origami-bench</h1>
<p><b>How much can a model fold into 12,000 tokens?</b> Same short prompt for every model: one self-contained HTML file. Then <i>actually run</i>: headless WebKit, 15-second video, health checks, panel-of-3 video-judge score.</p>
<p class="m">Run of __DATE__: <b>extreme tasks</b> (branching chain reactions, full gauntlets, orrery-automatons, rich shaders). <a href="run-2026-10-13.html">Run of 2026-10-13 (4 hard tasks, 8k tokens, 1 judge)</a> &middot; <a href="previous-run.html">Run of 2026-10-12 (easy)</a> &middot; <a href="results/__DATE__.md">full report with per-judge scores</a> &middot; <a href="https://github.com/zorahrel/origami-bench">code and method</a></p>
<h2>Leaderboard</h2>
<table class="lb"><tr><th>#</th><th>model</th><th>panel mean</th><th class="j" title="gpt-6-luna, OpenAI">GPT judge</th><th class="j" title="Gemini via free router, Google">Gemini judge</th><th class="j" title="claude-haiku-5-5, Anthropic (also a contestant)">Claude judge</th><th>walker</th><th>physics</th><th>gears</th><th>shader</th></tr>
__LB__</table>
<p class="m"><b>Every contestant ran at its maximum reasoning effort</b> (shown after the model name): Claude <code>--effort max</code>, Codex <code>model_reasoning_effort=xhigh</code>, Muse <code>--reasoning-effort ultra</code>; free-auto has no effort setting ("default"). The effort used is stored in each cell's <code>meta.json</code>.</p>
<p class="m">Panel mean of 3 vendor-diverse judges (codex/gpt-6-luna, free router/Gemini (3.8-flash, falling back to 3.5-flash-lite when the free quota is out), claude/haiku-5-5 &mdash; the Anthropic judge is disclosed, never used alone), capped at 4 if nothing moves. __JUDGENOTE__ __AGREE__ One run per cell: differences under ~0.5&ndash;1 point are noise.</p>
__SHOWCASE__
<h2 id="player">Player</h2>
<div class="tabs" id="tabs" role="tablist"></div>
<div id="stage"><video id="v" controls muted loop playsinline preload="metadata"></video><iframe id="live" title="live scene" loading="lazy" allow="autoplay; fullscreen"></iframe></div>
<div id="bar">
<button id="prev" title="previous model">&larr;</button>
<select id="model"></select>
<button id="next" title="next model">&rarr;</button>
<div class="mode"><button id="mClip" class="on">Clip</button><button id="mLive">Live</button><button id="mCmp">Compare</button></div>
</div>
<div id="strip"></div>
<div id="why"></div>
<div id="cmp"><div><video id="vA" controls muted loop playsinline preload="metadata"></video><select id="selA"></select><p id="whyA"></p></div>
<div><video id="vB" controls muted loop playsinline preload="metadata"></video><select id="selB"></select><p id="whyB"></p></div></div>
<p class="nav">Keys: &larr;/&rarr; switch model &middot; &uarr;/&darr; switch task &middot; space play/pause &middot; swipe the video on a phone &middot; linkable as #task/model (e.g. #walker/opus-5.5). Live runs the generated out.html in your browser; Compare plays two clips side by side.</p>
<script>
const D=__DATA__;
const tabs=document.getElementById('tabs'),stage=document.getElementById('stage'),v=document.getElementById('v'),
live=document.getElementById('live'),msel=document.getElementById('model'),strip=document.getElementById('strip'),
why=document.getElementById('why'),cmp=document.getElementById('cmp');
let task=D.tasks[0].id,model=null,mode='clip';
D.tasks.forEach(t=>{const b=document.createElement('button');b.textContent=t.name;b.dataset.t=t.id;b.setAttribute('role','tab');b.onclick=()=>setTask(t.id);tabs.appendChild(b)});
function modelsFor(t){return Object.keys(D.cells).filter(m=>D.cells[m][t]).sort((a,b)=>((D.cells[b][t].s??-1)-(D.cells[a][t].s??-1)))}
function setTask(t){if(!D.tasks.some(x=>x.id===t))return;task=t;
[...tabs.children].forEach(b=>b.classList.toggle('on',b.dataset.t===t));
const ms=modelsFor(t);if(!ms.includes(model))model=ms[0]||null;buildModelUI();show();syncHash()}
function setModel(m){if(!D.cells[m]||!D.cells[m][task])return;model=m;buildModelUI();show();syncHash()}
function buildModelUI(){const ms=modelsFor(task);
msel.innerHTML='';ms.forEach(m=>{const o=document.createElement('option');o.value=m;
o.textContent=D.names[m]+' ('+(D.cells[m][task].s??'-')+')';if(m===model)o.selected=true;msel.appendChild(o)});
strip.innerHTML='';ms.forEach(m=>{const c=D.cells[m][task];const b=document.createElement('button');
if(m===model)b.classList.add('on');b.innerHTML=(c.poster?'<img loading="lazy" src="'+c.poster+'">':'')+'<b>'+esc(D.names[m])+'</b><span>'+(c.s??'-')+'/10</span>';
b.onclick=()=>setModel(m);strip.appendChild(b)});
for(const id of['mClip','mLive','mCmp'])document.getElementById(id).classList.remove('on');
document.getElementById(mode==='clip'?'mClip':mode==='live'?'mLive':'mCmp').classList.add('on')}
function esc(s){return String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
function show(){const c=model?D.cells[model][task]:null;
stage.classList.toggle('live',mode==='live');cmp.classList.toggle('on',mode==='cmp');
if(!c){v.removeAttribute('src');why.textContent='no render';return}
if(mode==='live'){if(live.dataset.k!==model+task){live.dataset.k=model+task;live.src=c.live||''}}
else{v.poster=c.poster||'';if(v.dataset.k!==model+task){v.dataset.k=model+task;v.src=c.clip||'';v.play().catch(()=>{})}}
const pj=c.pj||{};why.innerHTML='<b>'+esc(D.names[model])+' &middot; '+(c.s??'-')+'/10</b> <span style="color:#888">(effort: '+esc(c.effort||'?')+' &middot; codex '+(pj.codex??'-')+' / router '+(pj.router??'-')+' / claude '+(pj.claude??'-')+')</span><br>'+esc(c.why||'');
if(mode==='cmp')syncCmp()}
function setMode(m){mode=m;if(m==='cmp'&&!selA.value)selA.value=model;buildModelUI();show()}
document.getElementById('mClip').onclick=()=>setMode('clip');
document.getElementById('mLive').onclick=()=>setMode('live');
document.getElementById('mCmp').onclick=()=>setMode('cmp');
document.getElementById('prev').onclick=()=>step(-1);document.getElementById('next').onclick=()=>step(1);
msel.onchange=()=>setModel(msel.value);
function step(d){const ms=modelsFor(task);setModel(ms[(ms.indexOf(model)+d+ms.length)%ms.length])}
function stepTask(d){const ts=D.tasks.map(t=>t.id);setTask(ts[(ts.indexOf(task)+d+ts.length)%ts.length])}
document.addEventListener('keydown',e=>{if(/INPUT|SELECT|TEXTAREA/.test(e.target.tagName))return;
if(e.key==='ArrowRight')step(1);else if(e.key==='ArrowLeft')step(-1);
else if(e.key==='ArrowDown'){e.preventDefault();stepTask(1)}else if(e.key==='ArrowUp'){e.preventDefault();stepTask(-1)}});
document.addEventListener('keydown',e=>{if(e.key===' '&&!/INPUT|SELECT|TEXTAREA|BUTTON/.test(e.target.tagName)&&mode!=='live'){e.preventDefault();v.paused?v.play():v.pause()}});
let tx=null;stage.addEventListener('touchstart',e=>{tx=e.touches[0].clientX},{passive:true});
stage.addEventListener('touchend',e=>{if(tx===null||mode==='live')return;const dx=e.changedTouches[0].clientX-tx;tx=null;if(Math.abs(dx)>70)step(dx<0?1:-1)});
function syncHash(){history.replaceState(null,'','#'+task+'/'+model)}
function syncCmp(){for(const[vid,sel,wh]of[[vA,selA,whyA],[vB,selB,whyB]]){
const c=D.cells[sel.value]?D.cells[sel.value][task]:null;if(!c)continue;
vid.poster=c.poster||'';if(vid.dataset.k!==sel.value+task){vid.dataset.k=sel.value+task;vid.src=c.clip||''}
wh.innerHTML='<b>'+esc(D.names[sel.value])+' '+(c.s??'-')+'/10</b><br>'+esc(c.why||'')}}
const selA=document.getElementById('selA'),selB=document.getElementById('selB'),
vA=document.getElementById('vA'),vB=document.getElementById('vB'),
whyA=document.getElementById('whyA'),whyB=document.getElementById('whyB');
function fillCmp(sel,keep){const cur=keep||model;sel.innerHTML='';modelsFor(task).forEach(m=>{
const o=document.createElement('option');o.value=m;o.textContent=D.names[m]+' ('+(D.cells[m][task].s??'-')+')';
if(m===cur)o.selected=true;sel.appendChild(o)})}
const _show=show;show=function(){_show();if(mode==='cmp'){fillCmp(selA,selA.value||model);
fillCmp(selB,selB.value||modelsFor(task)[1]||model);syncCmp()}};
selA.onchange=syncCmp;selB.onchange=syncCmp;
(function init(){const h=location.hash.replace('#','').split('/');setTask(h[0]||D.tasks[0].id);
if(h[1]&&D.cells[h[1]]&&D.cells[h[1]][task])setModel(h[1]);window.addEventListener('hashchange',()=>{
const p=location.hash.replace('#','').split('/');if(p[0]&&p[0]!==task)setTask(p[0]);if(p[1]&&p[1]!==model)setModel(p[1])})})();
</script></body></html>"""
page = page.replace("__DATE__", date).replace("__LB__", lb).replace("__SHOWCASE__", SHOWCASE).replace("__AGREE__", AGREE).replace("__JUDGENOTE__", e(judge_note)).replace("__DATA__", data)
(ROOT / OUT).write_text(page)
print(OUT, "written:", len(page) // 1024, "KB")
