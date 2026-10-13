# Resume: Codex judge for gpt-6.1-sol and gpt-6-astra (after 17:35)

State (13/10 16:40): clips + page published (commit 5e4dfbe). Only the Codex judge is missing, on 4 cells with video:
gpt-6.1-sol/{walker,physics,shader}, gpt-6-astra/walker. router + claude judges already stored; panel.py reuses them.
Not resumable without regenerating (Codex quota): gpt-6.1-sol/gears, gpt-6-astra/{gears,shader} = no HTML, physics = 182 B. Scored 1, shown on the page.

Command (from ~/Projects/origami-bench; deletes judge.json, so the panel calls only the missing Codex judge):

    cd ~/Projects/origami-bench && for c in gpt-6.1-sol/walker gpt-6.1-sol/physics gpt-6.1-sol/shader gpt-6-astra/walker; do
      d=runs/2026-10-13-v3/$c; rm -f $d/judge.json
      python3 - "$d" <<'PY'
    import sys,json,pathlib
    d=pathlib.Path(sys.argv[1])
    import importlib.machinery as m
    b=m.SourceFileLoader("bench","bench").load_module()
    t=d.name; _,descs=b.load_tasks()
    auto=json.loads((d/"auto.json").read_text())
    print(d, b.judge_cell(d, descs[t], auto))
    PY
    done
    python3 bench report --date 2026-10-13-v3 && python3 site.py 2026-10-13-v3 "" && git add -A . && git commit -qm "v3: Codex judge for gpt-6.1-sol and gpt-6-astra" && git push origin HEAD

Then drop the "in arrivo" note in site.py (line with class="hint") and rebuild.
