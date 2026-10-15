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
- `results/` — per-run output: `manifest.json`, `summary.json`, `runs.csv` are always committed
  (no sensitive content). Whether `cases.jsonl`/`cases.csv` (which include real answer text and
  retrieved chunk text) also get committed, or stay local-only, is controlled by
  `results/.gitignore` — **default for this instance: local-only** (see that file). Change it if
  this instance's corpus is low-sensitivity enough to commit full run history instead.
