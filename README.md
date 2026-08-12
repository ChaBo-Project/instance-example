# instance-example

Template repo for a new ChaBo instance, deployed via the `hf-spaces` topology (two HF
Spaces: orchestrator + a Gradio-wrapped Qdrant), matching the working `instance-endev`
deployment. This repo holds **only this instance's config** — no application source, no
deploy scripts. Deploy mechanics live once, generically, in
[`ChaBo-Deploy`](https://github.com/ChaBo-Project/ChaBo-Deploy), referenced here at a
pinned version — see `orchestrator/README.md` / `qdrant/README.md` for why.

## Using this template

GitHub does **not** substitute placeholders automatically when a repo is generated from
a template — after creating your instance repo from this one
(`gh repo create instance-<name> --template ChaBo-Project/instance-example`, or "Use this
template" in the GitHub UI), work through this checklist by hand:

1. **Replace every `<INSTANCE_NAME>` placeholder** with your instance's actual name:
   - `deploy.env` (header comment)
   - `.github/workflows/deploy.yml` (`name:`, both `title:` fields)
   - `orchestrator/README.md`, `qdrant/README.md` (headers)
   - `orchestrator/instance_config/instance.yaml`,
     `orchestrator/instance_config/params.override.cfg` (header comments)
2. **Fill in every `<fill in>` placeholder**:
   - `deploy.env` — `CHABO_TAG`, `ORCHESTRATOR_HF_SPACE`, `QDRANT_HF_SPACE`,
     `INSTANCE_URL`
   - `orchestrator/instance_config/params.override.cfg` — at minimum
     `[hf_endpoints]`, `[qdrant]`, `[generator]`, and `[query_rewriter]`'s `llm_*`
     keys (or set `[query_rewriter] enabled = false` instead of filling those in)
3. **Create two empty HF Spaces by hand** — one for each of `ORCHESTRATOR_HF_SPACE` and
   `QDRANT_HF_SPACE` from `deploy.env` (e.g. at `hf.co/new-space`). This has to happen
   before the deploy workflow ever runs: `deploy-hf-space`'s `push.sh` does a
   `git clone` into `huggingface.co/spaces/<org>/<name>`, which fails on a namespace that
   doesn't exist yet — the workflow renders and pushes *content* into a Space, it doesn't
   create the Space itself. For each Space:
   - **SDK: Docker** (required — the rendered content is a `Dockerfile`, not a Gradio/
     Streamlit app spec).
   - Visibility: private, unless you have a specific reason to make it public.
   - Leave it otherwise empty — the first deploy run populates it.
4. **Re-enable GitHub Actions** in your new repo's Actions tab — workflows copied from
   a template repo are disabled by default until a maintainer turns them on.
5. **Add the `HF_TOKEN` secret** (Settings → Secrets and variables → Actions) — see
   `orchestrator/README.md` for what it's used for.
6. **Set the Qdrant Space's own Variables/Secrets by hand**, now that it exists, in its
   HF Space Settings panel (`COLLECTION_NAME`, `EMBEDDING_DATASET`,
   `EMBEDDING_DIMENSION`, `QDRANT__SERVICE__API_KEY`, `DATASET_READ_TOKEN`) — never
   applied by CI, see the commented block at the bottom of `deploy.env` and
   `qdrant/README.md`. Can be done before or after the first deploy run, but must be set
   before the Qdrant Space will actually come up healthy.
7. Optionally fill in `orchestrator/instance_config/instance.yaml` (filters, db_context,
   blocklist, instance_guidelines — all optional) and
   `orchestrator/instance_config/prompt_overrides.md` (query rewrite / filter extraction
   prompt steps — leave empty to use the framework defaults).
8. Push to `main` — `.github/workflows/deploy.yml` runs on any push touching
   `orchestrator/**`, `qdrant/**`, or `deploy.env`, and deploys both HF Spaces.

## Scope note

Only the `hf-spaces` topology is covered by this template so far. `ChaBo-Deploy` is
gaining a second topology (`docker-compose-vm`, for co-located single-VM deployment) —
once that's merged and proven, this template will likely grow a second variant. Until
then, this template assumes HF Spaces.
