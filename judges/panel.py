#!/usr/bin/env python3
"""Panel judge (default BENCH_JUDGE_CMD): runs three vendor-diverse judges and averages.
- codex  = gpt-6-luna via Codex CLI (OpenAI, ChatGPT subscription), 24 frames
- router = gemini-3.5-flash-lite via free local OpenAI-compatible router, 8 frames
- claude = claude-haiku-5-5 via Claude Code CLI subscription, 8 frames (NOTE: Anthropic
  models also compete; this judge is disclosed, never used alone)
Env: VIDEO, PROMPT_FILE (set by bench). Writes judge_<name>.json next to judge.json
(panel mean). Prints 'SCORE: <mean>' + per-judge breakdown. Never tunes for any model:
whatever comes out is reported."""
import os, sys, re, json, subprocess, pathlib

ROOT = pathlib.Path(__file__).resolve().parent
video = os.environ["VIDEO"]
cell = pathlib.Path(video).parent
JUDGES = [("codex", ROOT / "codex.py"), ("router", ROOT / "router.py"), ("claude", ROOT / "claude_judge.py")]

def parse(out):
    m = re.search(r"SCORE:\s*(\d+)", out)
    rest = (out.split("\n", 1)[1] if m and "\n" in out else out)[:300].strip().replace("\n", " ")
    return (min(10, int(m.group(1))) if m else None), rest

scores, notes = {}, {}
env = {**os.environ, "VIDEO": video}
for name, script in JUDGES:
    f = cell / f"judge_{name}.json"
    if f.exists():
        try:
            old = json.loads(f.read_text()); scores[name] = old["score"]; notes[name] = old.get("why", ""); continue
        except Exception: pass
    try:
        r = subprocess.run([sys.executable, "-I", str(script)], capture_output=True, text=True, timeout=420,
                           stdin=subprocess.DEVNULL, env=env)
        sc, why = parse(r.stdout)
        detail = {"score": sc, "why": why or (r.stdout + r.stderr)[:200]}
        if sc is not None: f.write_text(json.dumps(detail))
        scores[name], notes[name] = sc, detail["why"]
    except Exception as e:
        scores[name], notes[name] = None, f"judge failed: {e}"[:200]

valid = {k: v for k, v in scores.items() if isinstance(v, (int, float))}
if valid:
    print(f"SCORE: {round(sum(valid.values()) / len(valid), 1)}")
    print("Panel (" + ", ".join(f"{k}={scores[k]}" for k in scores) + "). " + " ".join(f"[{k}] {notes[k]}" for k in valid if notes[k])[:360])
else:
    print("no answer (all panel judges failed: " + "; ".join(notes.values())[:200] + ")")
