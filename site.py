#!/usr/bin/env python3
"""Builds index.html (public page) from runs/<date>/ and results. Usage: site.py DATE JUDGE_NOTE"""
import sys, json, pathlib, html
ROOT = pathlib.Path(__file__).resolve().parent
date, judge_note = sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else ""
NAMES = {"sonnet-5.5": "Claude Sonnet 5.5", "opus-5.5": "Claude Opus 5.5", "gpt-6-luna": "gpt-6-luna", "muse-spark-1.3": "Muse Spark 1.3",
         "muse-wonder-full": "Muse Wonder Full 1.0", "free-auto": "free-auto (free router)"}
TASKS = [("walker", "Parkour + combat fighter"), ("physics", "Rube-Goldberg chain"), ("gears", "Clockwork automaton"), ("shader", "Raymarched SDF scene")]
base = ROOT / "runs" / date; rows = []
for m in NAMES:
    cells = {}
    for t, _ in TASKS:
        c = base / m / t
        if not (c / "meta.json").exists(): continue
        j = json.loads((c / "judge.json").read_text()) if (c / "judge.json").exists() else {"score": None, "why": "not judged"}
        cells[t] = (j, (c / "clip.mp4").exists(), json.loads((c / "meta.json").read_text()))
    sc = [v[0]["score"] for v in cells.values() if v[0]["score"] is not None]
    rows.append((m, sum(sc) / len(sc) if sc else 0, cells))
rows.sort(key=lambda r: -r[1])
e = html.escape
H = ['''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>origami-bench: how much can a model fold into 8,000 tokens?</title>
<style>body{font:16px/1.5 system-ui,sans-serif;max-width:1400px;margin:0 auto;padding:24px;color:#111}h1{margin:.2em 0}table.lb{border-collapse:collapse;width:100%;margin:16px 0}
td,th{padding:8px;border-bottom:1px solid #eee;text-align:left}.m{color:#666;font-size:14px}a{color:#5b2ee6}
.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:16px}.grid h4{margin:0;font-size:13px;color:#666;font-weight:600}
.cell{background:#f6f6f8;border-radius:8px;overflow:hidden;font-size:15px}.cell video,.cell .na{width:100%;aspect-ratio:8/5;display:block;background:#111;object-fit:cover}
.na{color:#fff;display:flex!important;align-items:center;justify-content:center}.cell div{padding:5px 8px;display:flex;justify-content:space-between;gap:6px}
.s{font-weight:700}h3{margin:28px 0 8px}@media(max-width:800px){.grid{grid-template-columns:1fr}}</style></head><body>
<h1>🦢 origami-bench</h1><p><b>How much can a model fold into 8,000 tokens?</b> Every model gets the same short prompt and must return one self-contained HTML file under an 8,000-token output budget. It is then <i>actually run</i>: headless WebKit, 10-second video, health checks, video-judge score.</p>
<p class="m">Run of ''' + date + ''': <b>hard tasks</b> (chained sequences, not demos). <a href="previous-run.html">Previous run (easy tasks, 2026-10-12)</a> · <a href="https://github.com/zorahrel/origami-bench">code and method</a></p>
<h2>Leaderboard</h2><table class="lb"><tr><th>#</th><th>model</th><th>mean</th>''' + "".join(f"<th>{n}</th>" for _, n in TASKS) + "</tr>"]
for i, (m, avg, cells) in enumerate(rows, 1):
    H.append(f"<tr><td>{i}</td><td>{e(NAMES[m])}</td><td><b>{avg:.1f}</b></td>")
    for t, _ in TASKS:
        v = cells.get(t); H.append(f'<td><a href="#{m}-{t}">{v[0]["score"] if v and v[0]["score"] is not None else "-"}</a></td>')
    H.append("</tr>")
H.append(f'</table><p class="m">Score 1-10 from the video judge, capped at 4 if nothing moves. {e(judge_note)} One run per cell: differences under ~0.5-1 point are noise. Each clip below is that cell\'s real 10-second render; click "live" to run the scene in your browser.</p>')
for t, tn in TASKS:
    H.append(f"<h3>{e(tn)}</h3><div class=\"grid\">")
    for m, avg, cells in rows:
        v = cells.get(t); H.append(f'<div class="cell" id="{m}-{t}"><h4 style="padding:5px 8px 0">{e(NAMES[m])}</h4>')
        if v and v[1]:
            p = f"runs/{date}/{m}/{t}"
            H.append(f'<video muted loop playsinline preload="none" poster="{p}/poster.jpg" data-src="{p}/clip.mp4"></video>')
        else: H.append('<div class="na">no render</div>')
        j = v[0] if v else {"score": None, "why": ""}
        H.append(f'<div><span class="s" title="{e(j["why"] or "")}">{j["score"] if j["score"] is not None else "-"}/10</span><a href="runs/{date}/{m}/{t}/out.html">live</a></div></div>')
    H.append("</div>")
H.append('''<script>
const io=new IntersectionObserver(es=>es.forEach(x=>{const v=x.target;if(x.isIntersecting){if(!v.src)v.src=v.dataset.src;v.play().catch(()=>{})}else v.pause()}),{threshold:.3});
document.querySelectorAll("video").forEach(v=>io.observe(v));
</script></body></html>''')
(ROOT / "index.html").write_text("\n".join(H))
print("index.html written")
