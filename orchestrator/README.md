# Chabo Orchestrator — &lt;INSTANCE_NAME&gt;

Config for this instance's orchestrator Space: `instance_config/`
(`params.override.cfg` / `instance.yaml` / `prompt_overrides.md`), holding this
instance's Tier-1/Tier-2 overrides on top of the published, instance-blind
`ghcr.io/chabo-project/chabo-rag-orchestrator` image.

This folder holds **only config, not the Dockerfile or any deploy source** — those live
once, generically, in `ChaBo-Deploy` (`templates/orchestrator.Dockerfile` +
`.github/actions/deploy-hf-space`), referenced by this repo's
`.github/workflows/deploy.yml` at a pinned version. This repo never copies
ChaBo-Deploy's scripts/templates — only references them, per the org's Guidelines
(A3.4 / A7). The deploy workflow renders the actual Dockerfile from that template,
overlays `instance_config/` into it, and pushes the result to the HF Space — **do not
edit files in that Space directly**, the next deploy overwrites them.

> The Space itself must exist (SDK: Docker) before the deploy workflow can push to it —
> see the top-level `README.md`'s instantiation checklist, step 3.

## Required Space Secrets

- `HF_TOKEN` — used for: (1) inference-provider calls to your embedding/reranker
  endpoints, (2) reused as `QDRANT_API_KEY` if Qdrant runs as a private
  gradio-wrapped Space authenticated the same way.
- `QDRANT_API_KEY` — set to the same `HF_TOKEN` value if using the pattern above (see
  `../qdrant/README.md`).
