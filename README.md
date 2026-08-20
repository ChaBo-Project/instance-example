# instance-example

GitHub does not replace placeholders automatically when a repository is created
from this template. Complete the following steps manually before running the
deployment workflow.

### 1. Create or verify the embeddings Dataset

Create the Hugging Face Dataset repository containing the embedded documents,
or verify that the required Dataset already exists.

The Dataset ID must match `EMBEDDING_DATASET` in `deploy.env`.

Example format:

`<organization>/<dataset-name>`

The Dataset must contain the columns expected by the Qdrant initialization
process, including the document ID, vector, and payload metadata.

A Hugging Face Collection is optional and can be used to organize related
resources, but it does not replace the embeddings Dataset or the Qdrant
collection.

### 2. Create the two Hugging Face Spaces

Create these two Spaces manually before running the deployment:

1. Orchestrator Space
2. Qdrant Space

The repository IDs must match `ORCHESTRATOR_HF_SPACE` and `QDRANT_HF_SPACE`
in `deploy.env`.

For both Spaces:

- Select `Docker` as the SDK.
- Use private visibility unless the instance must be public.
- Leave the Space empty.
- Do not add application files manually; the deployment workflow will push them.

The deployment workflow cannot create missing Spaces. It can only push content
to Spaces that already exist.

### 3. Create a fine-grained Hugging Face token

Create a fine-grained token under:

`Hugging Face → Settings → Access Tokens`

Select both Space repositories:

- `spaces/<organization>/<qdrant-space>`
- `spaces/<organization>/<orchestrator-space>`

Enable these repository permissions:

- `Read contents of selected repos`
- `Write contents/settings of selected repos`

Select the organization that owns the inference resources and enable:

- `Make calls to Inference Providers on behalf of selected orgs`
- `Make calls to Inference Endpoints in selected orgs`

Do not enable organization settings, billing, member-management, or
organization-wide repository write permissions unless they are explicitly
required.

If the organization requires token approval, wait until an organization
administrator approves the token.

### 4. Add the token to GitHub Actions

In the GitHub repository, open:

`Settings → Secrets and variables → Actions → New repository secret`

Create:

- Name: `HF_TOKEN`
- Value: the fine-grained Hugging Face token

Never place the token in `deploy.env`, workflow files, README files, or committed
configuration.

### 5. Complete the public deployment configuration

Edit `deploy.env` and fill in all required public values, including:

- `INSTANCE_NAME`
- `CHABO_TAG`
- `ORCHESTRATOR_HF_SPACE`
- `QDRANT_HF_SPACE`
- `INSTANCE_URL`
- `QDRANT_URL`
- `EMBEDDING_ENDPOINT_URL`
- `RERANKER_ENDPOINT_URL`
- `EMBEDDING_DATASET`
- `COLLECTION_NAME`
- `EMBEDDING_DIMENSION`
- Generator settings

`params.override.cfg.template` contains variable placeholders. The deployment
workflow combines it with `deploy.env` and generates the final
`params.override.cfg`.

Do not edit or commit a generated `params.override.cfg`.

### 6. Configure the Qdrant Space manually

This step is not automated.

In the Qdrant Space, open:

`Settings → Variables and secrets`

Add these variables:

- `EMBEDDING_DATASET`
- `COLLECTION_NAME`
- `EMBEDDING_DIMENSION`
- `VECTOR_COLUMN_NAME`
- `BATCH_SIZE`
- `TOP_K`

Add these secrets:

- `QDRANT__SERVICE__API_KEY`
- `DATASET_READ_TOKEN`

`DATASET_READ_TOKEN` must have read access to the embeddings Dataset. For better
security, use a separate read-only token instead of the deployment token.

### 7. Complete optional instance configuration manually

This step is not automated.

Edit `orchestrator/instance_config/instance.yaml` only when the instance needs:

- Metadata filters
- Database context
- Blocklist additions
- Instance-specific guidelines

Leave optional sections empty or commented when they are not required.

### 8. Run the deployment manually

This step is not automated.

Open:

`GitHub → Actions → Deploy ChaBo instance → Run workflow`

Review the validation output before allowing deployment to continue.

A push to a branch configured in `.github/workflows/deploy.yml` can also trigger
the workflow when one of the monitored deployment files changes.
