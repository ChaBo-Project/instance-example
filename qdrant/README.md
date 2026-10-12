# Chabo Qdrant — &lt;INSTANCE_NAME&gt;

Private Qdrant instance for this ChaBo deployment, fronted by a Gradio facade
(`app.py`, `api_name="query_points"`) so the Space's own HF private-Space auth protects
the retrieval API instead of relying solely on Qdrant's own API key.

This folder holds no source at all — the wrapper (`Dockerfile`, `app.py`,
`initialize_qdrant.py`, `start.sh`) lives once, generically, in `ChaBo-Deploy`
(`hf-spaces/qdrant/`), the org's one sanctioned "vendored third-party wrapper" exception
to "no application source in a deploy repo." This repo's `.github/workflows/deploy.yml`
references it at the version pinned by `CHABO_DEPLOY_REF` via `ChaBo-Deploy`'s
`deploy-hf-space` composite action — never a copy. **Do not edit files in the HF Space
directly** — the next deploy overwrites them.

> The deploy workflow creates the Space (private, SDK: Docker) if it doesn't exist, and
> sets the secrets and variables below from GitHub Actions secrets and `deploy.env` —
> see the top-level `README.md`, step 6.

## Space Secrets (set by the workflow)

- `QDRANT__SERVICE__API_KEY` — Qdrant's internal API key (local connection only).
- `DATASET_READ_TOKEN` — HF token with read access to the private embeddings dataset.

Each comes from the matching optional GitHub Actions secret, or `HF_TOKEN` if that's
unset.

Optional, set manually in the Space: `QDRANT__SERVICE__READ_ONLY_API_KEY` — a read-only
key `app.py` uses for `query_points` instead of the admin key.

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
- `FILTERABLE_FIELDS` (default empty) — same `field:type,...` value as the
  orchestrator's filterable fields. Creates a payload index on `metadata.<field>` for
  each entry (`str`/`list` → keyword, `int` → integer) before upload, so filtered search
  stays fast on large collections. The type must match the stored values. Sent only
  when nonempty in `deploy.env`; an empty value removes it from the Space.
- `QDRANT_TIMEOUT` (default: qdrant-client's) — search timeout in seconds, whole
  number. Sent only when nonempty in `deploy.env`.

On boot, `initialize_qdrant.py` checks whether `COLLECTION_NAME` already exists; if not,
it pulls the full dataset from `EMBEDDING_DATASET` and
re-indexes from scratch. Storage is ephemeral (`/tmp`), so every restart reloads —
`EMBEDDING_DATASET` is the durable source of truth, not this Space's local disk.
