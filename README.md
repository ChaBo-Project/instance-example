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

### 2. Spaces and Collection

The workflow creates the three Spaces and the Hugging Face Collection itself
when they are missing (token permissions in step 3). The Collection is found by
the exact `HF_COLLECTION_TITLE` under the organization of `CHATUI_HF_SPACE`,
with visibility per `HF_COLLECTION_PRIVATE`.

`HF_SPACES_PRIVATE` must remain set to `true`.

The Hugging Face Collection is different from the Qdrant collection configured
through `COLLECTION_NAME`.

### 3. Create a fine-grained Hugging Face token

Create a fine-grained token under:

`Hugging Face → Settings → Access Tokens`

For the first deployment, use your own token. Select the organization that
owns the Spaces and the inference resources and enable:

- `Write contents/settings of repos in selected orgs`
- Collections read/write
- `Make calls to Inference Providers on behalf of selected orgs`
- `Make calls to Inference Endpoints in selected orgs`

Do not enable organization settings, billing, or member-management permissions.

The first run creates the three Spaces and the Collection and adds them and the
embeddings Dataset to the Collection. If an item cannot be added, the run logs
a warning and continues.

Once the instance is live, an organization admin:

1. Adds any items missing from the Collection.
2. Moves the Spaces and the Collection into the instance's Resource Group, if
   the organization uses Resource Groups.
3. Creates a token on the organization's service account, scoped to this
   instance:
   - The three Space repositories: `Read contents of selected repos` and
     `Write contents/settings of selected repos`
   - The embeddings Dataset repository: `Read contents of selected repos`
   - The organization: Collections read/write, `Make calls to Inference
     Providers on behalf of selected orgs`, `Make calls to Inference Endpoints
     in selected orgs`
4. Replaces the `HF_TOKEN` GitHub Actions secret with the service-account token.
5. Manually starts the `Deploy ChaBo instance` workflow from GitHub Actions,
   selecting the branch containing the instance's deployment configuration.
   Changing a GitHub Actions secret does not automatically trigger deployment.
6. Waits for deployment to complete and verifies through ChatUI that ChaBo
   retrieves documents and generates answers.
7. Deletes the first deployment token only after successful verification
   and confirming that no other application or separately configured secret
   still uses it.

Later runs reuse the existing Spaces and Collection and create nothing.

If the organization requires token approval, wait until an organization
administrator approves the token.

### 4. Add the tokens to GitHub Actions

In the GitHub repository, open:

`Settings → Secrets and variables → Actions`

Create this required repository secret:

- Name: `HF_TOKEN`
- Value: the fine-grained Hugging Face token

The workflow uses `HF_TOKEN` to:

- Create or verify the three Spaces and enforce their configured visibility
- Find or create the Hugging Face Collection
- Push content to all three Hugging Face Spaces
- Configure the ChatUI Space variable and secret
- Configure the Orchestrator Space secrets
- Configure the Qdrant Space variables and secrets
- Call the configured Hugging Face inference resources

When `[generator] PROVIDER = azure` in `params.override.cfg.template`, also create a GitHub Actions repository
secret named `AZURE_API_KEY` containing the key for your Azure resource.

The workflow checks that this secret is present and copies it to the
Orchestrator Space. `HF_TOKEN` remains required for both generator choices.
Azure authentication never falls back to `HF_TOKEN`.

The following GitHub Actions secrets are optional:

- `QDRANT__SERVICE__API_KEY`
- `DATASET_READ_TOKEN`
- `CHATUI_BACKEND_TOKEN`

`CHATUI_BACKEND_TOKEN` can be a dedicated read-only token with access to the
private Orchestrator Space. The ChatUI uses this token server-side when calling
the private Orchestrator.

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
- `CHABO_DEPLOY_REF`
- `ORCHESTRATOR_HF_SPACE`
- `QDRANT_HF_SPACE`
- `CHATUI_HF_SPACE`
- `CHATUI_HF_SPACE_PRIVATE`
- `HF_SPACES_PRIVATE`
- `INSTANCE_URL`
- `QDRANT_URL`
- `CHATUI_URL`
- `HF_COLLECTION_TITLE`
- `HF_COLLECTION_PRIVATE`
- `EMBEDDING_DATASET`
- `COLLECTION_NAME`
- `EMBEDDING_DIMENSION`

Then edit `orchestrator/instance_config/params.override.cfg.template` and fill
in the keys marked "Required": the embedding and reranker endpoints and the
generator settings.

Set `CHATUI_HF_SPACE_PRIVATE` to control the visibility of the ChatUI Space:

- `"false"` keeps the ChatUI Space public.
- `"true"` keeps the ChatUI Space private.

The workflow enforces this setting on every run. A private ChatUI requires users to sign in to Hugging Face and have
access to the Space.

This setting is independent of `HF_COLLECTION_PRIVATE`. For example, the
ChatUI Space can be private while the Hugging Face Collection remains public.
Adding a private Space to a public Collection does not make the Space public.

`params.override.cfg.template` holds the orchestrator pipeline settings, edited
directly in the file. A few values shared with the workflow and the Qdrant Space
(`QDRANT_URL`, `COLLECTION_NAME`, `FILTERABLE_FIELDS`) are `${...}` placeholders
filled from `deploy.env`; leave those as they are. The deployment workflow
renders the final `params.override.cfg` and validates it before making any
Hugging Face changes.

Do not edit or commit a generated `params.override.cfg`.

The parameter template is based on the published ChaBo-Orchestrator
`instance_config.example/params.override.cfg`. It leaves optional settings
commented so the selected Orchestrator image remains the source of truth for
defaults.

`orchestrator/instance_config/prompt_overrides.md` is based on the published
Orchestrator example. Leave its sections empty to use the framework defaults.

`chatui/env.local.template` is based on ChaBo-ChatUI's root `.env` file and
lists the supported settings available for instance customization. The
workflow inserts the model configuration, instance name and public URL, then
uploads the rendered content as the Hugging Face `DOTENV_LOCAL` variable.
Re-synchronize the template with ChaBo-ChatUI whenever `CHATUI_TAG` is
upgraded. Never add passwords, tokens or other secrets to this public file.

`chatui/PRIVACY.md` replaces the default ChatUI privacy page during deployment.
It is an editable starting point, not completed compliance text. Before
deploying a real instance, review the complete file and replace the AI Act
transparency placeholder with approved instance-specific information.

#### Deployment action version

Set `CHABO_DEPLOY_REF` in `deploy.env` to select the ChaBo-Deploy
release used for Orchestrator, Qdrant, and ChatUI deployments.

Example:

```bash
CHABO_DEPLOY_REF="hf-spaces-v0.2.0"
```

Find available releases on the
[ChaBo-Deploy tags page](https://github.com/ChaBo-Project/ChaBo-Deploy/tags).

This setting controls deployment scripts and templates.
`CHABO_TAG` and `CHATUI_TAG` separately select the application images.

To upgrade, update this value to a compatible release and test the
deployment. This release tag does not automatically follow newer releases.

#### Choose the answer generator

Configure the answer generator in the `[generator]` section of
`params.override.cfg.template`.

Both options keep ChatUI, Orchestrator and Qdrant on Hugging Face.
Selecting Azure only changes where answers are generated; it does not
create Azure resources or deploy a model.

| Setting | Hugging Face | Azure |
|---|---|---|
| `PROVIDER` | `huggingface` | `azure` |
| `MODEL` | Hugging Face model repository ID | Exact Azure deployment name |
| `INFERENCE_PROVIDER` | For example, `nscale` | Empty; ignored by Azure |
| `ORGANIZATION` | Your Hugging Face billing organization | Empty; ignored by Azure |
| `AZURE_ENDPOINT` | Empty | Azure API base URL ending in `/openai/v1/` |
| Required GitHub secrets | `HF_TOKEN` | `HF_TOKEN` and `AZURE_API_KEY` |

For Azure, the resource and model deployment must already exist.

Update all provider-specific settings together. Changing
`PROVIDER` does not automatically replace the other values.

Embedding, reranking and query rewriting have separate configuration.
Changing the answer generator does not change those services.

#### Metadata settings

- `CONTEXT_META_FIELDS` (`[generator]` in the template): metadata included in
  the context sent to the generator.
  Default: `filename,project_id,document_source,document_type`.
- `TITLE_META_FIELDS` (`[generator]` in the template): metadata displayed with
  generated answers. Default: `filename,page`.
- `FILTERABLE_FIELDS` (`deploy.env`): metadata used to filter document searches.
  Leave empty to disable filtering. Enabling filters also requires matching
  entries in `instance.yaml` and filter LLM configuration in the template.

#### Apply and verify changes

Commit and push your changes, then start a new `Deploy ChaBo instance`
workflow run. Select the branch containing your updated configuration.

In the Hugging Face Orchestrator Space:

1. Check `instance_config/params.override.cfg` for the provider, model
   and endpoint.
2. Check the container startup logs for the selected generator provider.
3. Send a question through ChatUI to verify that generation works.

Configuration validation checks for missing values. It does not verify
whether Azure accepts the key, endpoint or deployment name.

Both provider configurations update the same Spaces when their repository
IDs remain unchanged. Separate Git branches do not create separate instances.

### 6. Automatic Hugging Face Space configuration

The workflow automatically configures the required Hugging Face Space settings.
They do not need to be entered manually in the Hugging Face Space interface.

#### Orchestrator and Qdrant Spaces

For each backend Space, the workflow:

- Reuses the configured Space when it exists
- Creates a private Docker Space when it is missing
- Enforces private visibility
- Stops with an explanation if the token cannot create, read, or update it

`HF_SPACES_PRIVATE` must be `true`.

#### ChatUI Space

The workflow:

- Reuses the configured ChatUI Space when it exists, or creates it when missing
- Enforces the visibility configured through `CHATUI_HF_SPACE_PRIVATE`
- Deploys the configured ChatUI image
- Generates the `DOTENV_LOCAL` configuration
- Connects ChatUI to the private Orchestrator

 Set `CHATUI_HF_SPACE_PRIVATE="false"` for a public ChatUI Space or
`CHATUI_HF_SPACE_PRIVATE="true"` for a private ChatUI Space.

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

If the Collection is missing, the workflow creates it. It enforces the
visibility configured through `HF_COLLECTION_PRIVATE` and adds:

- The Orchestrator Space
- The Qdrant Space
- The ChatUI Space
- The embeddings Dataset

Existing items are not duplicated. If an item cannot be added, the workflow
logs a warning and continues; an admin can add it manually (step 3). The token must have write access to the
Collection so its visibility and items can be updated.

The workflow stops with an explanation if the Collection cannot be created,
if multiple Collections have the same title, or if the token cannot update it.

Adding private backend Spaces to a public Collection does not change the
visibility of those Spaces.

#### Orchestrator Space secrets

The workflow configures:

- `HF_TOKEN` from the GitHub Actions secret `HF_TOKEN`.
- `QDRANT_API_KEY` from the same `HF_TOKEN`.
- `AZURE_API_KEY` from the matching GitHub Actions secret, when nonempty.

`AZURE_API_KEY` is required when the answer generator uses Azure.

The current workflow copies the Azure key whenever it is supplied,
even if another generator is selected. Switching providers does not
automatically delete existing Hugging Face Space secrets.

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

Edit `orchestrator/instance_config/prompt_overrides.md` only when the instance
needs custom query-rewriting or metadata-filter instructions. Leave both
headings empty to use the framework defaults.

## What the deployment workflow automates

The `Deploy ChaBo instance` workflow performs these operations:

1. Validates the required public configuration and GitHub secret.
2. Generates `params.override.cfg` from `deploy.env` and
   `params.override.cfg.template`, and validates it.
3. Finds or creates the private Orchestrator and Qdrant Spaces.
4. Finds or creates the ChatUI Space and enforces the configured visibility.
5. Renders the ChatUI environment template and configures the resulting
   Space variable and required secret.
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
- Add the token to GitHub Actions.
- After the first run (admin): complete the Collection, move resources into
  the Resource Group, and replace `HF_TOKEN` with a scoped service-account
  token (step 3).
- Complete the public values in `deploy.env`.
- Optionally configure `instance.yaml`.
- Start the workflow through GitHub Actions or merge the changes into a
  configured deployment branch.
