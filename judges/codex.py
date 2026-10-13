#!/usr/bin/env python3
"""Frame-based judge for when no video-capable API is available: samples 16 frames from the video and asks `codex exec` (ChatGPT subscription,
no API key) to apply the rubric. Env: VIDEO, PROMPT_FILE (set by bench), CODEX_JUDGE_MODEL (default gpt-6-luna). First output line is 'SCORE: <n>'."""
import os, sys, subprocess, tempfile, pathlib

video, prompt = os.environ["VIDEO"], open(os.environ["PROMPT_FILE"]).read()
model = os.environ.get("CODEX_JUDGE_MODEL", "gpt-6-luna"); N = int(os.environ.get("JUDGE_FRAMES", "24"))
tmp = pathlib.Path(tempfile.mkdtemp(prefix="judge-")); imgs = []
for i in range(N):
    t = round(0.3 + i * 14.4 / (N - 1), 2); f = tmp / f"f{i:02d}.png"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", str(t), "-i", video, "-frames:v", "1", "-vf", "scale=480:-2", str(f)], stdin=subprocess.DEVNULL)
    if f.exists(): imgs += ["-i", str(f)]
if not imgs: sys.exit("no frames extracted")
q = (f"The attached images are {len(imgs) // 2} frames, in time order (about 0.6 s apart), from ONE video. Look only at them, do not search for files. "
     + prompt.replace("This video shows", "The video shows"))
r = subprocess.run(["codex", "exec", "-m", model, "--skip-git-repo-check", "-s", "read-only", *imgs, "-o", str(tmp / "out.txt"), q],
                   cwd=tmp, capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=380)
out = (tmp / "out.txt").read_text() if (tmp / "out.txt").exists() else ""
print(out.strip() or f"no answer (rc={r.returncode}) {r.stderr[-200:]}")
