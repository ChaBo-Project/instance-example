# Chabo Orchestrator — &lt;INSTANCE_NAME&gt;

Config for this instance's orchestrator Space: `instance_config/`
(`params.override.cfg.template` / `instance.yaml` / `prompt_overrides.md`), holding this
instance's Tier-1/Tier-2 overrides on top of the published, instance-blind
`ghcr.io/chabo-project/chabo-rag-orchestrator` image. The deploy workflow renders
`params.override.cfg.template` into `params.override.cfg` from `deploy.env`; never
commit a rendered `params.override.cfg`.

This folder holds **only config, not the Dockerfile or any deploy source** — those live
once, generically, in `ChaBo-Deploy` (`hf-spaces/orchestrator.Dockerfile` +
`.github/actions/deploy-hf-space`), referenced by this repo's
`.github/workflows/deploy.yml` at the version pinned by `CHABO_DEPLOY_REF`. This repo
never copies ChaBo-Deploy's scripts/templates — only references them, per the org's
Guidelines (A3.4 / A7). The deploy workflow renders the actual Dockerfile from that
template, overlays the rendered `instance_config/` into it, and pushes the result to the
HF Space — **do not edit files in that Space directly**, the next deploy overwrites them.

> The deploy workflow creates the Space (private, SDK: Docker) if it doesn't exist, and
> sets the secrets below from GitHub Actions secrets — see the top-level `README.md`,
> step 6.

## Space Secrets (set by the workflow)

- `HF_TOKEN` — used for: (1) inference-provider calls to your embedding/reranker
  endpoints, (2) reused as `QDRANT_API_KEY` if Qdrant runs as a private
  gradio-wrapped Space authenticated the same way.
- `QDRANT_API_KEY` — set to the same `HF_TOKEN` value (see `../qdrant/README.md`).
- `AZURE_API_KEY` — copied from the GitHub Actions secret when nonempty; required when
  `[generator] PROVIDER` is `azure`.
