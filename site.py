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
    return f"{sum(v)/len(v):.1f}" if v else ("in arrivo" if jn == "codex" else "-")
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
        agree.append(f"{ja}&ndash;{jb}: r={'n/a' if r is None else f'{r:.2f}'}, gap {d:.1f} pt")
AGREE = "Judge agreement: " + "; ".join(agree) + "." if agree else ""
def fmt_t(sec):
    return f"{sec/60:.0f} min" if sec >= 120 else f"{sec:.0f} s"
def tot_sec(m): return sum(c["sec"] or 0 for c in cells[m].values())
def tot_tok(m): return sum(c["tok"] or 0 for c in cells[m].values())
def jmean(m, jn):
    v = [c["pj"][jn] for c in cells[m].values() if isinstance(c["pj"].get(jn), (int, float))]
    return f"{sum(v)/len(v):.1f}" if v else "-"
detail = "".join(
    f"<tr><td>{e(LABEL[m])}</td><td>{avg:.1f}</td>" +
    "".join(f"<td>{cells[m].get(t, {}).get('s') if cells[m].get(t, {}).get('s') is not None else '-'}</td>" for t, _ in TASKS) +
    "".join(f"<td>{jmean(m, jn)}</td>" for jn in ("codex", "router", "claude")) +
    f"<td>{tot_tok(m):,}</td></tr>" for m, avg, n in rows)
ORDER = [m for m, _, _ in rows]
AVG = {m: round(a, 1) for m, a, _ in rows}
SECS = {m: fmt_t(tot_sec(m)) for m in models}
data = json.dumps({"date": date, "names": {m: LABEL[m] for m in models},
                   "tasks": [{"id": t, "name": n} for t, n in TASKS], "cells": cells})
data = json.dumps({"date": date, "names": {m: LABEL[m] for m in models}, "order": ORDER, "avg": AVG, "time": SECS,
                   "tasks": [{"id": t, "name": n} for t, n in TASKS], "cells": cells})
page = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>origami-bench: how much can a model fold into 12,000 tokens?</title>
<style>
*{box-sizing:border-box}
body{font:16px/1.45 system-ui,sans-serif;max-width:1180px;margin:0 auto;padding:12px;color:#111;overflow-x:hidden}
h1{margin:0;font-size:clamp(20px,5vw,28px)}.sub{color:#555;font-size:14px;margin:2px 0 10px}a{color:#5b2ee6}
main{display:flex;flex-direction:column;gap:12px}
@media(min-width:900px){main{display:grid;grid-template-columns:minmax(0,2fr) minmax(300px,1fr);gap:20px;align-items:start}#rank{order:2}#playerbox{order:1}}
.tabs{display:flex;gap:6px;overflow-x:auto;padding:2px 0 6px;-webkit-overflow-scrolling:touch}
.tabs button{flex:1 0 auto;border:1px solid #ddd;background:#f6f6f8;border-radius:8px;padding:10px 12px;font-size:14px;cursor:pointer;white-space:nowrap;min-height:44px}
.tabs button.on{background:#111;color:#fff;border-color:#111}
#stage{background:#000;border-radius:12px;overflow:hidden}
#stage video,#stage iframe{width:100%;aspect-ratio:8/5;display:block;border:0;background:#000}
#stage iframe{display:none}#stage.live video{display:none}#stage.live iframe{display:block}
#cap{display:flex;gap:8px;align-items:center;margin-top:8px;flex-wrap:wrap}
#cap b{font-size:15px;flex:1 1 160px;min-width:0}
#cap button{border:1px solid #ddd;background:#fff;border-radius:8px;padding:9px 12px;font-size:14px;cursor:pointer;min-height:40px}
#cap button.on{background:#5b2ee6;color:#fff;border-color:#5b2ee6}
#why{font-size:13px;color:#555;margin:6px 0 0;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
#why.open{display:block}
#rank h2{font-size:15px;margin:0 0 6px;color:#555;font-weight:600}
#rank ol{list-style:none;margin:0;padding:0}
#rank li button{display:grid;grid-template-columns:22px minmax(0,1fr) 40px 56px;gap:8px;align-items:center;width:100%;border:0;border-bottom:1px solid #eee;background:none;padding:0 4px;min-height:44px;font:inherit;font-size:14px;cursor:pointer;text-align:left;position:relative}
#rank li button.on{background:#f1ecff;font-weight:600}
#rank .n{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
#rank .s{font-weight:700;text-align:right}#rank .t{color:#777;font-size:12px;text-align:right}#rank .r{color:#999;font-size:12px}
#rank .bar{position:absolute;left:0;bottom:0;height:3px;background:#5b2ee6;opacity:.35}
.hint{font-size:12px;color:#888;margin:6px 0 0}
details{margin:18px 0 0;border-top:1px solid #eee;padding-top:10px}
summary{cursor:pointer;font-weight:600;padding:8px 0}
details p,details li{font-size:14px;color:#444}
.tw{overflow-x:auto}table{border-collapse:collapse;font-size:13px;min-width:560px}td,th{padding:5px 8px;border-bottom:1px solid #eee;text-align:left;white-space:nowrap}
footer{margin:16px 0 8px;font-size:13px;color:#666}
</style></head><body>
<h1>\U0001F9A2 origami-bench</h1>
<p class="sub">One prompt, 12,000 tokens, one HTML file, actually run and scored on video. Tap a model or a task.</p>
<main>
<section id="playerbox">
<div class="tabs" id="tabs" role="tablist"></div>
<div id="stage"><video id="v" controls muted loop playsinline preload="metadata"></video><iframe id="live" title="live scene" loading="lazy" allow="autoplay; fullscreen"></iframe></div>
<div id="cap"><b id="capt"></b><button id="mClip" class="on">Clip</button><button id="mLive">Live</button></div>
<p id="why"></p>
</section>
<section id="rank"><h2>Ranking, mean of 4 tasks</h2><ol id="rl"></ol><p class="hint">Score 1-10 &middot; total generation time &middot; one run per cell, under ~1 point is a tie.</p><p class="hint">gpt-6.1-sol and gpt-6-astra: Codex judge <b>in arrivo</b> (scores are the mean of the other two judges). 4 of their 8 cells produced no page, scored 1.</p></section>
</main>
<details id="how"><summary>How it works</summary>
<p>Every model gets the same short prompt per task and must return one self-contained HTML file (three.js r170) under 12,000 output tokens. Each file is rendered headless in WebKit for 15 s; a panel of three vendor-diverse video judges (gpt-6-luna, Gemini via a free router, claude-haiku-5-5) scores 1-10 against a fixed rubric; capped at 4 if nothing moves. __JUDGENOTE__</p>
<p><b>Effort.</b> Every model ran at its maximum: Claude <code>--effort max</code>, Codex <code>model_reasoning_effort=xhigh</code>, Muse <code>--reasoning-effort ultra</code>; free-auto has no setting.</p>
<p><b>Tokens.</b> Claude and Codex counts include hidden reasoning, so most cells show as over budget; the HTML itself is always under 32 KB. Muse counts are estimated from characters.</p>
<p>__AGREE__ The Gemini judge is the most lenient; Claude and GPT models also compete, hence the panel.</p>
<div class="tw"><table><tr><th>model</th><th>mean</th><th>walker</th><th>physics</th><th>gears</th><th>shader</th><th>GPT judge</th><th>Gemini judge</th><th>Claude judge</th><th>output tokens</th></tr>__DETAIL__</table></div>
<p>Keys: &larr;/&rarr; model &middot; &uarr;/&darr; task &middot; space play/pause &middot; links like <code>#walker/opus-5.5</code>.</p>
</details>
<footer><a href="results/__DATE__.md">Full report</a> &middot; <a href="run-2026-10-13.html">8k run</a> &middot; <a href="previous-run.html">first run</a> &middot; <a href="https://github.com/zorahrel/origami-bench">code and method</a></footer>
<script>
const D=__DATA__;
const tabs=document.getElementById('tabs'),stage=document.getElementById('stage'),v=document.getElementById('v'),
live=document.getElementById('live'),rl=document.getElementById('rl'),why=document.getElementById('why'),capt=document.getElementById('capt');
let task=D.tasks[0].id,model=D.order[0],mode='clip';
D.tasks.forEach(t=>{const b=document.createElement('button');b.textContent=t.name.split(' ')[0]==='Parkour'?'Walker':t.name;b.dataset.t=t.id;b.setAttribute('role','tab');b.onclick=()=>setTask(t.id);tabs.appendChild(b)});
const SHORT={walker:'Walker',physics:'Physics',gears:'Gears',shader:'Shader'};
[...tabs.children].forEach(b=>b.textContent=SHORT[b.dataset.t]||b.textContent);
function esc(s){return String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
function has(m,t){return D.cells[m]&&D.cells[m][t]}
function buildRank(){rl.innerHTML='';const mx=Math.max(...Object.values(D.avg));
D.order.forEach((m,i)=>{const li=document.createElement('li'),b=document.createElement('button');
if(m===model)b.classList.add('on');
b.innerHTML='<span class="r">'+(i+1)+'</span><span class="n">'+esc(D.names[m])+'</span><span class="s">'+D.avg[m].toFixed(1)+'</span><span class="t">'+D.time[m]+'</span><i class="bar" style="width:'+(D.avg[m]/10*100)+'%"></i>';
b.onclick=()=>{setModel(m);stage.scrollIntoView({behavior:'smooth',block:'nearest'})};li.appendChild(b);rl.appendChild(li)})}
function setTask(t){if(!D.tasks.some(x=>x.id===t))return;task=t;[...tabs.children].forEach(b=>b.classList.toggle('on',b.dataset.t===t));show();syncHash()}
function setModel(m){if(!D.cells[m])return;model=m;buildRank();show();syncHash()}
function show(){const c=has(model,task)?D.cells[model][task]:null;
stage.classList.toggle('live',mode==='live');
document.getElementById('mClip').classList.toggle('on',mode==='clip');document.getElementById('mLive').classList.toggle('on',mode==='live');
if(!c){v.removeAttribute('src');v.dataset.k='';capt.textContent=D.names[model]+': no result';why.textContent='';return}
if(mode==='live'){if(live.dataset.k!==model+task){live.dataset.k=model+task;live.src=c.live||''}}
else if(v.dataset.k!==model+task){v.poster=c.poster||'';v.dataset.k=model+task;v.src=c.clip||'';v.play().catch(()=>{})}
capt.textContent=D.names[model]+' \u00b7 '+(c.s??'-')+'/10';why.textContent=c.why||''}
function setMode(m){mode=m;show()}
document.getElementById('mClip').onclick=()=>setMode('clip');document.getElementById('mLive').onclick=()=>setMode('live');
why.onclick=()=>why.classList.toggle('open');
function step(d){const i=D.order.indexOf(model);setModel(D.order[(i+d+D.order.length)%D.order.length])}
function stepTask(d){const ts=D.tasks.map(t=>t.id);setTask(ts[(ts.indexOf(task)+d+ts.length)%ts.length])}
document.addEventListener('keydown',e=>{if(/INPUT|SELECT|TEXTAREA/.test(e.target.tagName))return;
if(e.key==='ArrowRight')step(1);else if(e.key==='ArrowLeft')step(-1);
else if(e.key==='ArrowDown'){e.preventDefault();stepTask(1)}else if(e.key==='ArrowUp'){e.preventDefault();stepTask(-1)}
else if(e.key===' '&&e.target.tagName!=='BUTTON'&&mode!=='live'){e.preventDefault();v.paused?v.play():v.pause()}});
let tx=null;stage.addEventListener('touchstart',e=>{tx=e.touches[0].clientX},{passive:true});
stage.addEventListener('touchend',e=>{if(tx===null||mode==='live')return;const dx=e.changedTouches[0].clientX-tx;tx=null;if(Math.abs(dx)>70)step(dx<0?1:-1)});
function syncHash(){history.replaceState(null,'','#'+task+'/'+model)}
(function init(){const h=location.hash.replace('#','').split('/');if(h[1]&&D.cells[h[1]])model=h[1];buildRank();setTask(h[0]||D.tasks[0].id);
window.addEventListener('hashchange',()=>{const p=location.hash.replace('#','').split('/');if(p[1]&&D.cells[p[1]]&&p[1]!==model)setModel(p[1]);if(p[0]&&p[0]!==task)setTask(p[0])})})();
</script></body></html>"""
page = page.replace("__DATE__", date).replace("__DETAIL__", detail).replace("__AGREE__", AGREE).replace("__JUDGENOTE__", e(judge_note)).replace("__DATA__", data)
(ROOT / OUT).write_text(page)
print(OUT, "written:", len(page) // 1024, "KB")
