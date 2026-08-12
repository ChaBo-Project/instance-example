# Chabo Qdrant — &lt;INSTANCE_NAME&gt;

Private Qdrant instance for this ChaBo deployment, fronted by a Gradio facade
(`app.py`, `api_name="query_points"`) so the Space's own HF private-Space auth protects
the retrieval API instead of relying solely on Qdrant's own API key.

This folder holds no source at all — the wrapper (`Dockerfile`, `app.py`,
`initialize_qdrant.py`, `start.sh`) lives once, generically, in `ChaBo-Deploy`
(`vendored/qdrant/`), the org's one sanctioned "vendored third-party wrapper" exception
to "no application source in a deploy repo." This repo's `.github/workflows/deploy.yml`
references it at a pinned version via `ChaBo-Deploy`'s `deploy-hf-space` composite
action — never a copy. **Do not edit files in the HF Space directly** — the next deploy
overwrites them.

> The Space itself must exist (SDK: Docker) before the deploy workflow can push to it —
> see the top-level `README.md`'s instantiation checklist, step 3.

## Required Space Secrets

- `QDRANT__SERVICE__API_KEY` — Qdrant's internal API key (local connection only).
- `DATASET_READ_TOKEN` — HF token with read access to the private embeddings dataset.

## Required Space Variables

- `EMBEDDING_DATASET` — HF Dataset repo id holding pre-embedded points (`id`, `vector`,
  `payload` columns). No code default — must be set, or indexing fails outright.
- `COLLECTION_NAME` — Qdrant collection to create/query. Code default
  `default_collection` exists but should always be set explicitly per instance.
- `EMBEDDING_DIMENSION` — must match the dataset's vector size. Code default `1024`
  exists but should be set explicitly to match your embedding model, not relied on.

## Optional Space Variables (code defaults exist, override only if needed)

- `VECTOR_COLUMN_NAME` (default `vector`) — column in `EMBEDDING_DATASET` holding the
  embedding vector, if it's named something other than `vector`.
- `BATCH_SIZE` (default `200`) — indexing batch size for the initial upsert; raise/lower
  to tune for larger datasets or a slower embedding endpoint.
- `TOP_K` (default `10`) — only sets the Gradio UI's default value for manual testing;
  every real query from the orchestrator passes its own `top_k` per request
  (`[retrieval] top_k`/`prefetch_top_k` in `params.override.cfg`), so this rarely
  matters in practice.

On boot, `initialize_qdrant.py` checks whether `COLLECTION_NAME` already exists; if not
(fresh Space, crash, redeploy), it pulls the full dataset from `EMBEDDING_DATASET` and
re-indexes from scratch — `EMBEDDING_DATASET` is the durable source of truth, not this
Space's local disk.
