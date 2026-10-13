#!/usr/bin/env python3
"""Claude judge: sends N frames to a Claude model via the Claude Code CLI subscription
(no API key). NOTE: an Anthropic model is also a contestant family here, so this judge
is reported separately and never used alone (self-bias disclosure in results).
Env: VIDEO, PROMPT_FILE (set by bench), CLAUDE_JUDGE_MODEL (default claude-haiku-5-5),
JUDGE_FRAMES_SMALL (default 8). First output line is 'SCORE: <n>'."""
import os, sys, json, subprocess, tempfile, pathlib

video, prompt = os.environ["VIDEO"], open(os.environ["PROMPT_FILE"]).read()
model = os.environ.get("CLAUDE_JUDGE_MODEL", "claude-haiku-5-5")
N = int(os.environ.get("JUDGE_FRAMES_SMALL", "8"))
tmp = pathlib.Path(tempfile.mkdtemp(prefix="judge-claude-")); names = []
for i in range(N):
    t = round(0.5 + i * 14.0 / (N - 1), 2); f = tmp / f"f{i:02d}.jpg"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", str(t), "-i", video, "-frames:v", "1", "-vf", "scale=480:-2", "-q:v", "5", str(f)], stdin=subprocess.DEVNULL)
    if f.exists(): names.append(f"frame {i + 1}: {f}")
q = (prompt.replace("This video shows", "The video shows")
     + f" The {len(names)} attached frame images are in time order from the video. Read every one with the Read tool, then score. "
     + " ".join(names))
try:
    r = subprocess.run(["claude", "-p", "--model", model, "--tools", "Read", "--output-format", "json", q],
                       capture_output=True, text=True, timeout=380, stdin=subprocess.DEVNULL, cwd=str(tmp))
    try:
        print(json.loads(r.stdout).get("result", "").strip() or f"no answer (rc={r.returncode}) {r.stderr[-200:]}")
    except Exception:
        print(f"no answer (unparsable, rc={r.returncode}) {(r.stdout + r.stderr)[-200:]}")
except Exception as e:
    print(f"no answer (judge failed: {e})"[:300])
