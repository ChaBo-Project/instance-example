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

### 4. Add the tokens to GitHub Actions

In the GitHub repository, open:

`Settings → Secrets and variables → Actions`

Create this required repository secret:

- Name: `HF_TOKEN`
- Value: the fine-grained Hugging Face token

The workflow uses `HF_TOKEN` to:

- Push content to both Hugging Face Spaces
- Configure the Orchestrator Space secrets
- Configure the Qdrant Space variables and secrets
- Call the configured Hugging Face inference resources

The following GitHub Actions secrets are optional:

- `QDRANT__SERVICE__API_KEY`
- `DATASET_READ_TOKEN`

When an optional secret is not configured, the workflow uses `HF_TOKEN` as its
default value.

If `HF_TOKEN` is used as `DATASET_READ_TOKEN`, it must have read access to the
embeddings Dataset.

For better separation of permissions, a dedicated read-only
`DATASET_READ_TOKEN` can be used.

Never place token values in `deploy.env`, workflow files, README files, or other
committed configuration.

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

### 6. Automatic Hugging Face Space configuration

The workflow automatically configures the required Hugging Face Space settings.
They do not need to be entered manually in the Hugging Face Space interface.

#### Orchestrator Space secrets

The workflow configures:

- `HF_TOKEN`
- `QDRANT_API_KEY`

Both use the required GitHub Actions secret `HF_TOKEN`.

#### Qdrant Space variables

The workflow reads these public values from `deploy.env` and adds them to the
Qdrant Space:

- `EMBEDDING_DATASET`
- `COLLECTION_NAME`
- `EMBEDDING_DIMENSION`
- `VECTOR_COLUMN_NAME`
- `BATCH_SIZE`
- `TOP_K`

Only these selected values are added to the Qdrant Space settings. The workflow
does not submit all values from `deploy.env` to Hugging Face.

#### Qdrant Space secrets

The workflow configures:

- `QDRANT__SERVICE__API_KEY`
- `DATASET_READ_TOKEN`

For each secret:

1. The workflow uses the matching optional GitHub Actions secret when it exists.
2. Otherwise, the workflow uses `HF_TOKEN` as the fallback.

Secret values are never stored in `deploy.env` and are not printed in the
workflow logs.

### 7. Complete optional instance configuration manually

This step is not automated.

Edit `orchestrator/instance_config/instance.yaml` only when the instance needs:

- Metadata filters
- Database context
- Blocklist additions
- Instance-specific guidelines

Leave optional sections empty or commented when they are not required.

## What the deployment workflow automates

The `Deploy ChaBo instance` workflow performs these operations:

1. Validates the required public configuration and GitHub secret.
2. Generates `params.override.cfg` from `deploy.env` and
   `params.override.cfg.template`.
3. Configures the Orchestrator Space secrets.
4. Configures the selected Qdrant Space variables.
5. Configures the Qdrant Space secrets, including fallback handling.
6. Deploys the Orchestrator Space.
7. Deploys the Qdrant Space.

The following prerequisites remain manual:

- Create or verify the embeddings Dataset.
- Create both empty Docker Spaces.
- Create the fine-grained Hugging Face token.
- Add the token to GitHub Actions.
- Complete the public values in `deploy.env`.
- Optionally configure `instance.yaml`.
- Start the workflow through GitHub Actions or merge the changes into a
  configured deployment branch.
