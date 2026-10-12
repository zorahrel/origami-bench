#!/usr/bin/env python3
"""Default judge: sends the video to Gemini and prints the model's answer (first line must be 'SCORE: <n>').
Env: VIDEO, PROMPT_FILE (set by bench), GEMINI_API_KEY (free key from https://aistudio.google.com), GEMINI_MODEL (optional)."""
import os, sys, json, base64, urllib.request

key = os.environ.get("GEMINI_API_KEY") or sys.exit("set GEMINI_API_KEY (or point BENCH_JUDGE_CMD at your own judge)")
model = os.environ.get("GEMINI_MODEL", "gemini-flash-latest")
video = open(os.environ["VIDEO"], "rb").read()
prompt = open(os.environ["PROMPT_FILE"]).read()
body = json.dumps({"contents": [{"parts": [
    {"inline_data": {"mime_type": "video/webm", "data": base64.b64encode(video).decode()}},
    {"text": prompt}]}]}).encode()
req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                             body, {"content-type": "application/json", "x-goog-api-key": key})
try:
    j = json.load(urllib.request.urlopen(req, timeout=300))
except urllib.error.HTTPError as e:
    sys.exit(f"Gemini HTTP {e.code}: {e.read().decode()[:200]}")
print(j["candidates"][0]["content"]["parts"][0]["text"])
