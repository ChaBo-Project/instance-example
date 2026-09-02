# instance-example

GitHub does not replace placeholders automatically when a repository is created
from this template. Complete the following steps manually before running the
deployment workflow.

## Security validation

The `Public repository safety` workflow runs on every push and pull request.

It checks tracked files for common credential formats. In the public template,
it also requires instance-specific values in `deploy.env` to remain empty.

The deployment workflow repeats the safety check before making any Hugging Face
API calls.

Real deployment configuration belongs only in private instance repositories.
Secrets must be stored in GitHub Actions secrets.

### 1. Create or verify the embeddings Dataset

Create the Hugging Face Dataset repository containing the embedded documents,
or verify that the required Dataset already exists.

The Dataset ID must match `EMBEDDING_DATASET` in `deploy.env`.

Example format:

`<organization>/<dataset-name>`

The Dataset must contain the columns expected by the Qdrant initialization
process, including the document ID, vector, and payload metadata.

The workflow finds or creates a Hugging Face Collection that groups the three
Spaces and the embeddings Dataset.

If the token cannot create Collections, create it manually using the exact
`HF_COLLECTION_TITLE`. Set `HF_COLLECTION_PRIVATE="false"` for a public
Collection. The workflow stops with an explanation if the Collection is missing
and cannot be created.

The Hugging Face Collection is different from the Qdrant collection configured
through `COLLECTION_NAME`.

### 2. Create or verify the private backend Spaces

The workflow checks these backend Spaces before configuration and deployment:

1. Orchestrator Space
2. Qdrant Space

The repository IDs must match `ORCHESTRATOR_HF_SPACE` and `QDRANT_HF_SPACE`
in `deploy.env`.

If a Space exists, the workflow reuses it and enforces private visibility.

If a Space is missing and `HF_TOKEN` has repository-creation permission, the
workflow creates it automatically with Docker SDK and private visibility.

If the token cannot create repositories, create each missing Space manually
with:

- The exact repository ID from `deploy.env`
- Docker SDK
- Private visibility
- An empty repository
- The Resource Group configured through `HF_RESOURCE_GROUP_ID`, when set

The token must have read and write access to both Spaces. The workflow stops
with an explanation if a Space is missing, inaccessible, or cannot be created.

`HF_SPACES_PRIVATE` must remain set to `true`.

### 3. Create a fine-grained Hugging Face token

Create a fine-grained token under:

`Hugging Face → Settings → Access Tokens`

Select both Space repositories:

- `spaces/<organization>/<qdrant-space>`
- `spaces/<organization>/<orchestrator-space>`

For fully automatic creation, grant the token permission to create repositories
and Collections in the target organization.

When `HF_RESOURCE_GROUP_ID` is configured, the token owner must have permission
to create and update resources inside that Enterprise Resource Group.

If these creation permissions cannot be granted, manually create the private
Orchestrator and Qdrant Spaces, the public ChatUI Space, and the Hugging Face
Collection before running the workflow.

In both modes, the token must have write access to the three Spaces and the
Collection so the workflow can configure and update them.

Enable these repository permissions:

- `Read contents of selected repos`
- `Write contents/settings of selected repos`

Select the organization that owns the inference resources and enable:

- `Make calls to Inference Providers on behalf of selected orgs`
- `Make calls to Inference Endpoints in selected orgs`

Do not enable organization settings, billing, or member-management permissions.
Repository and Collection creation permissions are optional when all required
Spaces and the Collection are created manually.

If the organization requires token approval, wait until an organization
administrator approves the token.

### 4. Add the tokens to GitHub Actions

In the GitHub repository, open:

`Settings → Secrets and variables → Actions`

Create this required repository secret:

- Name: `HF_TOKEN`
- Value: the fine-grained Hugging Face token

The workflow uses `HF_TOKEN` to:

- Find or create the private Orchestrator and Qdrant Spaces
- Find or create the public ChatUI Space
- Find or create the Hugging Face Collection
- Push content to all three Hugging Face Spaces
- Configure the ChatUI Space variable and secret
- Configure the Orchestrator Space secrets
- Configure the Qdrant Space variables and secrets
- Call the configured Hugging Face inference resources

The following GitHub Actions secrets are optional:

- `QDRANT__SERVICE__API_KEY`
- `DATASET_READ_TOKEN`
- `CHATUI_BACKEND_TOKEN`

`CHATUI_BACKEND_TOKEN` can be a dedicated read-only token with access to the
private Orchestrator Space. The public ChatUI uses this token server-side when
calling the private Orchestrator.

When `CHATUI_BACKEND_TOKEN` is not configured, the workflow uses `HF_TOKEN` as
the fallback.

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
- `CHATUI_TAG`
- `ORCHESTRATOR_HF_SPACE`
- `QDRANT_HF_SPACE`
- `CHATUI_HF_SPACE`
- `HF_SPACES_PRIVATE`
- `INSTANCE_URL`
- `QDRANT_URL`
- `CHATUI_URL`
- `HF_COLLECTION_TITLE`
- `HF_COLLECTION_PRIVATE`
- `EMBEDDING_ENDPOINT_URL`
- `RERANKER_ENDPOINT_URL`
- `EMBEDDING_DATASET`
- `COLLECTION_NAME`
- `EMBEDDING_DIMENSION`
- Generator settings

`HF_RESOURCE_GROUP_ID` is optional. Set it to the 24-character hexadecimal ID
from the Hugging Face Enterprise Resource Group page when resources must be
created inside that group.

Leave it empty when the organization does not use Resource Groups or when the
token has the required organization-wide permissions.

`params.override.cfg.template` contains variable placeholders. The deployment
workflow combines it with `deploy.env` and generates the final
`params.override.cfg`.

Do not edit or commit a generated `params.override.cfg`.

### 6. Automatic Hugging Face Space configuration

The workflow automatically configures the required Hugging Face Space settings.
They do not need to be entered manually in the Hugging Face Space interface.

When `HF_RESOURCE_GROUP_ID` is configured, newly created Spaces and Collections
are assigned to that Resource Group.

Existing Spaces and Collections are reused in their current Resource Group. The
workflow does not move existing resources between Resource Groups.

#### Orchestrator and Qdrant Spaces

For each backend Space, the workflow:

- Reuses the configured Space when it exists
- Creates a private Docker Space when it is missing and the token permits creation
- Enforces private visibility
- Stops with manual-creation instructions when creation is not permitted
- Stops if the token cannot read or update the Space

`HF_SPACES_PRIVATE` must be `true`.

#### ChatUI Space

The workflow:

- Reuses the configured ChatUI Space when it exists
- Creates it automatically when it is missing and the token permits creation
- Stops with manual-creation instructions when creation is not permitted
- Enforces public visibility
- Deploys the configured ChatUI image
- Generates the `DOTENV_LOCAL` configuration
- Connects ChatUI to the private Orchestrator

The workflow configures:

- `DOTENV_LOCAL` as a public Space variable
- `HF_TOKEN` as a private Space secret

The workflow removes conflicting entries if either name exists under the wrong
configuration type.

The ChatUI `HF_TOKEN` value comes from `CHATUI_BACKEND_TOKEN` when that optional
GitHub Actions secret exists. Otherwise, the deployment `HF_TOKEN` is used.

#### Hugging Face Collection

The workflow searches under the organization from `CHATUI_HF_SPACE` for the
exact title configured through `HF_COLLECTION_TITLE`.

If the Collection exists, the workflow reuses it. If it is missing and the
token permits Collection creation, the workflow creates it.

If creation permission is unavailable, manually create the Collection with:

- The exact title from `HF_COLLECTION_TITLE`
- The organization from `CHATUI_HF_SPACE`
- The visibility configured through `HF_COLLECTION_PRIVATE`
- The Resource Group configured through `HF_RESOURCE_GROUP_ID`, when set

The workflow adds:

- The Orchestrator Space
- The Qdrant Space
- The ChatUI Space
- The embeddings Dataset

Existing items are not duplicated. The token must have write access to the
Collection so its visibility and items can be updated.

The workflow stops with an explanation if the Collection is missing and cannot
be created, if multiple Collections have the same title, or if the token cannot
update it.

Adding private backend Spaces to a public Collection does not change the
visibility of those Spaces.

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
2. Finds or creates the private Orchestrator and Qdrant Spaces.
3. Finds or creates the public ChatUI Space.
4. Configures the ChatUI Space variable and secret.
5. Generates `params.override.cfg` from `deploy.env` and
   `params.override.cfg.template`.
6. Configures the Orchestrator Space secrets.
7. Configures the selected Qdrant Space variables.
8. Configures the Qdrant Space secrets, including fallback handling.
9. Deploys the Orchestrator Space.
10. Deploys the Qdrant Space.
11. Deploys the ChatUI Space.
12. Finds or creates the Hugging Face Collection and adds the deployment
    resources.

The following prerequisites remain manual:

- Create or verify the embeddings Dataset.
- Create a fine-grained Hugging Face token with write access to the deployment
  resources.
- Either grant repository and Collection creation permissions or manually create
  the three Spaces and Hugging Face Collection.
- Add the token to GitHub Actions.
- Complete the public values in `deploy.env`.
- Optionally configure `instance.yaml`.
- Start the workflow through GitHub Actions or merge the changes into a
  configured deployment branch.
