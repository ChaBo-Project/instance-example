# RAGAS evaluation data for this instance

This folder holds this instance's RAGAS evaluation test set and results.

## `eval/` must stay top-level

Never move or nest this folder inside `orchestrator/`, `chatui/`, `qdrant/`, or `scripts/`.
`deploy.yml`'s push trigger only watches those four folders (plus `deploy.env` and
`.github/workflows/deploy.yml`) — a top-level `eval/` never triggers a redeploy when you commit
eval results, but nesting it inside one of those folders later would silently start triggering
a real redeploy on every eval commit.

## Contents

- `testset.xlsx` — this instance's real questions + correct answers (the `Questions` sheet) and
  guidance for whoever fills it in (the `Instructions` sheet). Replace the placeholder content
  with real data for this instance.
- `results/` — one timestamped subfolder per run (e.g. `results/2026-11-17T10-00-00Z/`), plus `runs.csv` (one summary row per run) in `results/` itself. Always committed (no sensitive content):
  - `manifest.json` and `summary.json` (what was run, and the scores)
  - `params.override.cfg` (Mode B only: the rendered orchestrator config that produced the run; secret-free)
  - `runs.csv`

  Whether `cases.jsonl`/`cases.csv` (which include real answer text and retrieved chunk text) also get committed, or stay local-only, is controlled by `results/.gitignore` — **default for this instance: local-only** (see that file). The ignore rules match files inside the per-run subfolders too. Change them if this instance's corpus is low-sensitivity enough to commit full run history instead.

## How to run

The eval CLI lives in [ChaBo-Orchestrator](https://github.com/ChaBo-Project/ChaBo-Orchestrator) (`tests/eval/ragas/`). See its README, section "RAGAS evaluation", for the setup. By default the CLI writes into the orchestrator repo, so **always pass `--out-dir` pointing to this repo's `eval/results`**.

Example (Mode B: spin up a temporary container from this instance's config; run from the ChaBo-Orchestrator repo root):

```bash
python tests/eval/ragas/run_eval.py \
  --instance-repo /path/to/this/instance-repo \
  --testset /path/to/this/instance-repo/eval/testset.xlsx \
  --out-dir /path/to/this/instance-repo/eval/results \
  --limit 2
```

Remove `--limit 2` for a full run. Then review `git status` and commit the new run folder and the updated `runs.csv`.
