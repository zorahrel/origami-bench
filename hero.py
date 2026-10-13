#!/usr/bin/env python3
"""Re-renders the best-scoring cell of each task at 1280x800 for the page's 'Best of each task' videos.
Usage: hero.py DATE -> docs/hero-<task>.mp4 + hero-<task>.jpg (replaces the old 320 px GIFs)."""
import sys, json, subprocess, pathlib, os, shutil, tempfile
ROOT = pathlib.Path(__file__).resolve().parent
date = sys.argv[1]; base = ROOT / "runs" / date
for t in ("walker", "physics", "gears", "shader"):
    best = None
    for c in base.glob(f"*/{t}"):
        jf = c / "judge.json"
        if not jf.exists() or not (c / "out.html").exists(): continue
        sc = json.loads(jf.read_text()).get("score")
        if isinstance(sc, (int, float)) and (best is None or sc > best[0]): best = (sc, c)
    if not best: continue
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="hero-"))
    subprocess.run([sys.executable, str(ROOT / "render.py"), str(best[1] / "out.html"), str(tmp)], env={**os.environ, "RENDER_W": "1280", "RENDER_H": "800"}, capture_output=True, text=True, check=True)
    out = ROOT / "docs" / f"hero-{t}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "1", "-i", str(tmp / "video.webm"), "-vf", "fps=30", "-c:v", "libx264", "-preset", "slow", "-crf", "24", "-pix_fmt", "yuv420p", "-an", "-movflags", "+faststart", str(out)], check=True, stdin=subprocess.DEVNULL)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "6", "-i", str(tmp / "video.webm"), "-frames:v", "1", "-q:v", "3", str(ROOT / "docs" / f"hero-{t}.jpg")], check=True, stdin=subprocess.DEVNULL)
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"{t}: {best[1].parent.name} ({best[0]}) -> {out.name} {out.stat().st_size // 1024} KB")
