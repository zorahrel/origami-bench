#!/usr/bin/env python3
"""Router judge: sends N frames to a vision model on any OpenAI-compatible endpoint
(free local router by default). Env: VIDEO, PROMPT_FILE (set by bench),
BENCH_OPENAI_BASE (default http://127.0.0.1:18791/v1), BENCH_OPENAI_KEY (optional),
ROUTER_JUDGE_MODEL (default gemini-3.5-flash-lite), JUDGE_FRAMES (default 8).
First output line is 'SCORE: <n>'."""
import os, sys, json, base64, subprocess, tempfile, pathlib, urllib.request

video, prompt = os.environ["VIDEO"], open(os.environ["PROMPT_FILE"]).read()
models = os.environ.get("ROUTER_JUDGE_MODEL", "gemini-3.8-flash,gemini-3.5-flash-lite").split(",")  # first that answers wins (free quota varies)
N = int(os.environ.get("JUDGE_FRAMES_SMALL", "8"))
base = os.environ.get("BENCH_OPENAI_BASE", "http://127.0.0.1:18791/v1").rstrip("/")
tmp = pathlib.Path(tempfile.mkdtemp(prefix="judge-router-")); parts = [{"type": "text", "text": prompt.replace("This video shows", "The video shows") + f" The attached {N} images are frames in time order from the video."}]
for i in range(N):
    t = round(0.5 + i * 14.0 / (N - 1), 2); f = tmp / f"f{i:02d}.jpg"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", str(t), "-i", video, "-frames:v", "1", "-vf", "scale=480:-2", "-q:v", "5", str(f)], stdin=subprocess.DEVNULL)
    if f.exists():
        parts.append({"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(f.read_bytes()).decode()}})
hdr = {"content-type": "application/json"}
if os.environ.get("BENCH_OPENAI_KEY"): hdr["authorization"] = "Bearer " + os.environ["BENCH_OPENAI_KEY"]
err = ""
for model in models:
    body = json.dumps({"model": model, "messages": [{"role": "user", "content": parts}], "max_tokens": 600}).encode()
    try:
        j = json.load(urllib.request.urlopen(urllib.request.Request(base + "/chat/completions", body, hdr), timeout=300))
        out = j["choices"][0]["message"].get("content") or ""
        if out.strip(): print(out); sys.exit(0)
    except Exception as e:
        err = f"{model}: {e}"
print(f"no answer (judge failed: {err})"[:300])
