# 🦢 origami-bench

**How much can a model fold into 8,000 tokens?**

▶ **Live results, every scene clickable: https://zorahrel.github.io/origami-bench/**

A tiny, reproducible benchmark that gives every model the same short prompt, asks for **one self-contained HTML file** (three.js scene, physics sandbox, raymarching shader…) under a hard **8,000-token output budget**, then *actually runs it*: headless WebKit, 7-second video, automatic health checks, and a video-judge score.

No humans voting, no leaderboard to overfit to: four prompts you can read in a minute (`tasks/tasks.json`) and swap for your own.

| Walking humanoid | Physics sandbox |
|---|---|
| ![walker](docs/walker.gif) | ![physics](docs/physics.gif) |
| **Clockwork machine** | **Raymarched SDF** |
| ![gears](docs/gears.gif) | ![shader](docs/shader.gif) |

*Best-scoring output per task (all four: Sonnet 5.5).

## Why few tokens?

Anyone can get a good demo from 50k tokens of output. The interesting question is **density**: how much *working* complexity (articulated joints, collisions, shadows, ray-marched geometry) a model packs into a small budget **on the first try**, with no tools, no retries and no external assets. It is also a cheap proxy for "will this model one-shot a small, visual, self-checking piece of code?".

## Leaderboard (run of 2026-10-12)

Mean over 4 tasks. Score = video-judge rating 1-10 (fixed rubric, capped at 4 if no animation is detected).

| # | model | score | time (4 tasks) | output tokens | animated | clean |
|---|---|---|---|---|---|---|
| 1 | Claude Sonnet 5.5 | **7.2** | 163 s | 22,913\* | 4/4 | 4/4 |
| 2 | Claude Opus 5.5 | 7.0 | 262 s | 26,983\* | 4/4 | 4/4 |
| 3 | Muse Spark 1.3 | 6.5 | 252 s | ~8,155† | 4/4 | 4/4 |
| 4 | Muse Wonder Full 1.0 | 6.2 | 258 s | ~8,929† | 4/4 | 4/4 |
| 5 | gpt-6-luna | 6.0 | 1030 s | 59,987\* | 3/4 | 4/4 |
| 6 | free-auto (free router) | 4.0 | 757 s | 15,062 | 3/4 | 3/4 |

\* Counts include hidden reasoning tokens, which is why some cells are flagged "over budget" in the report even though every HTML file is under 16 KB. The budget in the prompt is a *request*; the harness reports the overshoot but does not discard the cell.
† Estimated from characters (chars / 3.5) because that CLI does not expose usage.

Full per-cell table with judge notes: [`results/2026-10-12.md`](results/2026-10-12.md). Every generated page is in `runs/2026-10-12/<model>/<task>/out.html`: open it in a browser.

**Read it with care:** one run per cell, one judge, scores are noisy by roughly ±1. Differences below ~0.5 are a tie.

## The four tasks

| id | what the model must build |
|---|---|
| `walker` | Articulated humanoid (joint hierarchy, opposite arm/leg swing, knee/elbow bend, body bob) walking on a checkered floor, directional light with soft shadows, coloured point light, fog, orbiting camera |
| `physics` | 150+ spheres dropped into a glass box with **no physics library**: sphere-sphere and wall collisions, restitution, friction, `InstancedMesh`, periodic box shake |
| `gears` | 8+ procedurally generated meshing gears with correct ratios and counter-rotation in a layered 3D layout, pendulum, ticking second hand, metallic look |
| `shader` | Full-screen raymarched SDF scene: morphing blob over an infinite floor, soft shadows, AO, fresnel glow, moving camera. Must compile first try |

All share one preamble: a single HTML file, three.js r170 from the CDN, no addons, no input, no console errors, under 8,000 tokens, raw HTML only.

## How a cell is scored

1. **Generate**: the model's adapter runs the prompt; the HTML is extracted from the reply; time and tokens are recorded.
2. **Render** (`render.py`): headless **WebKit** via Playwright, 640x400, 7 s video. `three.module.js` is served from `vendor/` so runs are offline-reproducible.
3. **Automatic checks**: no console errors · canvas not blank (pixel std-dev and distinct levels) · **animation detected** = mean difference between 4 screenshots exceeds a threshold in at least 2 of 3 pairs.
4. **Judge**: the video goes to a vision model with a fixed rubric (1-2 blank/broken/static · 3-4 poor or off-task · 5-6 recognisable, simple animation · 7-8 task met well with lights/shadows/depth · 9-10 surprising, near-professional). A blank page scores 1 without calling the judge; no detected animation caps the score at 4.

A VLM judge is fine for "does it move, does it look rich", and not for fine geometry. That is all this needs.

## Run it

Requirements: Python 3.9+, `pip install playwright && playwright install webkit`, `ffmpeg` (frame diffs and GIFs), plus whichever model CLIs you want to test.

```bash
./bench list
./bench run                                   # every model x every task, today's date
./bench run --models opus-5.5 --tasks walker,gears --force
./bench run --no-judge                        # generation + automatic checks only
./bench report --date 2026-10-12              # rebuild results/<date>.md
./bench gifs   --date 2026-10-12              # best cell per task -> docs/*.gif
```

Finished cells are cached in `runs/<date>/<model>/<task>/` (`out.html`, `meta.json`, `auto.json`, `judge.json`; videos and raw replies are git-ignored), so adding a model only runs that model.

### Judge

By default `judges/gemini.py` sends the video to Gemini (set `GEMINI_API_KEY`; a free key from Google AI Studio works, mind the daily quota). To use any other judge, set `BENCH_JUDGE_CMD` to a shell command that reads `$VIDEO` and `$PROMPT_FILE` and prints `SCORE: <n>` on its first line followed by a short justification.

## Add a model (one line)

Append to `models.conf` (or to a git-ignored `models.local.conf`):

```
name        adapter    argument
my-model    claude     claude-opus-5-5
```

| adapter | runs |
|---|---|
| `claude <model-id>` | `claude -p --model <id>` (Claude Code CLI) |
| `codex <model>` | `codex exec -m <model>` |
| `openai <model>` | any OpenAI-compatible `/chat/completions` endpoint (`BENCH_OPENAI_BASE`, `BENCH_OPENAI_KEY`): OpenRouter, vLLM, Ollama, LiteLLM… |
| `agentdir <command>` | a CLI agent called as `<command> -C <dir> <prompt>` that may save an `.html` instead of replying with it |
| `cmd <shell command>` | anything else: reads the prompt from `$PROMPT_FILE`, prints the HTML (or a reply containing it) to stdout |

## Add or change a task

Edit `tasks/tasks.json`: `preamble` is shared, each entry under `tasks` is the specific ask. Keep prompts short and identical for every model; that is the point.

## Prior art, and what was reused

- **Pelican riding a bicycle** (Simon Willison): one fixed prompt, code output, judge by looking. This is the template. https://simonwillison.net/tags/pelican-riding-a-bicycle/ · https://github.com/simonw/pelican-bicycle. Its known weakness (labs may train on the exact prompt, so leaderboards saturate) is why the tasks here are original and easy to rotate; see also alternative prompts at https://gally.net/temp/20251107pelican-alternatives/about.html
- **WebDev Arena** (LMArena): pairwise human votes on generated sites. https://arena.ai/blog/webdev-arena. Not reusable (needs people), but it inspired the fixed rubric.
- **Design Arena**: human-voted leaderboards for websites, via https://benchlm.ai/benchmarks/designarenawebsite. Same limitation, and tuned for sites rather than 3D/animation.
- **Three.js / voxel one-shot tests**: no standardised benchmark found at the time of writing, only informal community comparisons; hence the 3D tasks here.

## Limits

- 1 run per cell, 1 judge: noisy (±1). Re-run with `--force` and average if a ranking matters.
- Token counts for some CLIs include reasoning and others are estimated from characters; compare them as orders of magnitude, not exact figures.
- Wall-clock time includes queueing and network on free or shared endpoints.
- WebKit headless only; a page that needs WebGL features WebKit lacks will score as broken.
- The judge sees 640x400 video: fine detail is invisible to it.

## License

MIT, see [`LICENSE`](LICENSE). Bundled `vendor/three.module.js` is three.js r170, also MIT (see `vendor/NOTICE.txt`).
