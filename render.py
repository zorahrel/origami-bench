#!/usr/bin/env python3
"""Opens an HTML in headless WebKit, records 10 s of video and runs the automatic checks. Usage: render.py file.html out_dir -> JSON on stdout."""
import sys, json, subprocess, hashlib, shutil, pathlib, time
from playwright.sync_api import sync_playwright

html = pathlib.Path(sys.argv[1]).resolve(); out = pathlib.Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
vendor = pathlib.Path(__file__).parent / "vendor" / "three.module.js"
import os
W, H, SECS = int(os.environ.get("RENDER_W", 640)), int(os.environ.get("RENDER_H", 400)), float(os.environ.get("RENDER_SECS", 15.0))

def gray(png):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(png), "-vf", "scale=48:30", "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True)
    return r.stdout

errors, shots = [], []
with sync_playwright() as p:
    b = p.webkit.launch()
    try:
        ctx = b.new_context(viewport={"width": W, "height": H}, record_video_dir=str(out / "_v"), record_video_size={"width": W, "height": H})
        page = ctx.new_page()
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(str(e)))
        def serve_three(route):
            route.fulfill(status=200, content_type="text/javascript", headers={"access-control-allow-origin": "*"}, body=vendor.read_bytes())
        page.route("**/three.module*.js", serve_three)
        page.goto(html.as_uri(), wait_until="load", timeout=20000)
        t0 = time.time()
        for i, t in enumerate([2.0, 5.0, 8.0, 11.0, 13.5]):
            page.wait_for_timeout(max(0, int((t - (time.time() - t0)) * 1000)))
            f = out / f"shot{i}.png"; page.screenshot(path=str(f)); shots.append(f)
        page.wait_for_timeout(max(0, int((SECS - (time.time() - t0)) * 1000)))
        vid = page.video
        ctx.close()
        vpath = vid.path()
        shutil.move(vpath, out / "video.webm")
    finally:
        b.close()
shutil.rmtree(out / "_v", ignore_errors=True)

gs = [gray(f) for f in shots]
def mad(a, c): return sum(abs(x - y) for x, y in zip(a, c)) / max(1, len(a))
diffs = [round(mad(gs[i], gs[i + 1]), 2) for i in range(len(gs) - 1)]
g = gs[-1]; mean = sum(g) / max(1, len(g)); std = (sum((x - mean) ** 2 for x in g) / max(1, len(g))) ** .5
res = {"console_errors": errors[:5], "n_errors": len(errors), "std": round(std, 2), "diffs": diffs,
       "not_blank": std > 6 and len(set(g)) > 12, "animated": sum(d > 0.8 for d in diffs) >= 2}
for f in shots[:-1]: f.unlink()
print(json.dumps(res))
