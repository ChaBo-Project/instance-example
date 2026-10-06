# Template synchronization

Product owners can update their ChaBo instance repository from the public
`ChaBo-Project/instance-example` repository when they are ready.

Updates are not pushed centrally to all instance repositories. Each product
owner starts the update workflow from their own target repository.

No Git CLI commands are required on the product owner's computer.

## Overview

The target repository contains the workflow:

```text
.github/workflows/update-from-template.yml
```

The product owner starts this workflow manually from the target repository's
GitHub Actions page.

The workflow:

1. checks out the target repository's current `main` branch;
2. downloads the selected version of the public source template;
3. copies the managed infrastructure files into the target checkout;
4. reports, but never changes, template changes to instance-specific files;
5. records the source commit in `.template-version`;
6. creates a normal commit on a separate update branch;
7. pushes the update branch to the target repository;
8. provides a GitHub comparison link.

The product owner uses the comparison link to create a pull request through the
GitHub website.

The workflow never merges the pull request automatically.

## Source repository

The public source template is:

```text
https://github.com/ChaBo-Project/instance-example
```

The source repository can be downloaded without a token because it is public.

## Choosing the source version

When starting the workflow, the product owner provides a source reference:
an exact source commit SHA or a branch, normally `main`.

`instance-example` is not tagged; its `main` branch is the current template.

### Exact commit SHA

Use an exact commit SHA when a particular approved source commit is required.

Example:

```text
0123456789abcdef0123456789abcdef01234567
```

### Main branch

Use:

```text
main
```

to synchronize the latest commit currently available on the source
repository's `main` branch.

## Starting an update

In the target repository:

1. Open the repository on GitHub.
2. Select **Actions**.
3. Select **Update from instance-example**.
4. Select **Run workflow**.
5. Enter the required commit SHA or branch in **Source ref**.
6. Select **Run workflow** again.
7. Wait for the workflow to finish.
8. Open the completed workflow run.
9. Read the workflow summary.
10. Select **Open the comparison and create the pull request**.

The comparison page shows the proposed changes before the pull request is
created.

## Creating the pull request

On the comparison page:

1. Confirm that the base branch is `main`.
2. Confirm that the compare branch starts with:

   ```text
   chore/update-instance-example-
   ```

3. Review the displayed changes.
4. Select **Create pull request**.
5. Add a clear title and description.
6. Create the pull request.
7. Wait for all required checks.
8. Request the normal review.
9. Merge only after the checks and review pass.

The pull request is created manually so that the target repository's normal
pull-request workflows run.

## Repository history preservation

The source and target repositories are checked out into separate directories:

```text
source/
target/
```

The workflow never replaces the target repository with a new template copy.

The synchronization process:

- starts from the target repository's current `main`;
- preserves the target repository's `.git` directory;
- creates a new branch from the target's existing history;
- applies template changes as a normal new commit;
- does not reset the target's `main` branch;
- does not force-push;
- does not rewrite or remove existing commits;
- does not combine the unrelated source and target Git histories.

All existing commits in the target repository remain unchanged.

## Managed and instance-specific files

Only these infrastructure files are managed. They are identical in every
instance and are overwritten, added, or removed to match the source:

```text
.gitattributes
.gitignore
.github/workflows/deploy.yml
.github/workflows/public-safety.yml
.github/workflows/update-from-template.yml
docs/template-synchronization.md
scripts/check-public-safety.py
scripts/render-config.py
scripts/sync-template.py
scripts/test-sync-template.py
scripts/validate-config.py
```

The list lives in `MANAGED_PATHS` in `scripts/sync-template.py`. The workflow
runs the source template's copy of that script, so the list always matches the
template version being synchronized.

Every other file is instance-specific, for example `deploy.env`,
`orchestrator/instance_config/*`, `chatui/*` and the README files. The workflow
never writes, adds, or deletes them. `.git` is never touched.

The workflow verifies that `deploy.env` remains unchanged. If `deploy.env` does
not exist in the target repository root, synchronization stops with an error.

## Instance-file report

The workflow summary shows a diff for every instance-specific file that the
template changed. The product owner ports the wanted parts manually in a
separate commit.

`.template-version` records the source commit of the last synchronization.
When it is present, the report shows only template changes since that commit,
so the instance's own customizations do not appear as noise.

When it is missing, as on the first synchronization of an existing instance,
the report shows every difference between the instance and the template,
including files that exist only in the instance.

## deploy.env compatibility report

The workflow compares the variable names in the source and target `deploy.env`
files.

It does not compare, copy, or display variable values.

If the source contains variables that are missing from the target, the workflow:

- displays a warning in the workflow run;
- lists the missing variable names in the workflow summary;
- tells the product owner that manual configuration is required;
- continues preparing the shared template update.

If the target contains variables that are not present in the source, the
workflow lists their names as target-only variables. It does not remove them.

Target-only variables may be intentional instance-specific settings or old
variables that are no longer used by the template. The product owner must review
them manually.

The synchronization workflow never modifies `deploy.env`. Required variables
and their correct values must be added manually through a separate reviewed
configuration change.

## Authentication

Reading the source repository requires no credentials because
`ChaBo-Project/instance-example` is public.

Pushing an update branch requires a dedicated, least-privilege GitHub App.
This is necessary because template updates may modify files under
`.github/workflows/`. GitHub does not allow the target repository's built-in
`GITHUB_TOKEN` to push those workflow-file changes.

The GitHub App must have only these repository permissions:

- Contents: Read and write
- Workflows: Read and write
- Metadata: Read-only, granted automatically

The App does not require pull-request, administration, secrets, deployment, or
merge permissions.

Install the App only on the productive instance repositories that use template
synchronization. The App does not need access to the public source repository.

The workflow creates a short-lived installation token for the current target
repository. The token is automatically revoked when the workflow job finishes.

The token is used only to:

- check out the target repository;
- create the synchronization branch;
- push the synchronization commit.

The workflow does not use the token to create, approve, or merge a pull request.

## Required target repository secrets

Store the GitHub App credentials only as encrypted GitHub Actions secrets in
each target repository.

Create these repository secrets:

```text
INSTANCE_SYNC_APP_ID
INSTANCE_SYNC_APP_PRIVATE_KEY
```

`INSTANCE_SYNC_APP_ID` contains the numeric GitHub App ID.

`INSTANCE_SYNC_APP_PRIVATE_KEY` contains the complete private key, including
the `BEGIN` and `END` lines.

Never store the private key in:

- the repository;
- `deploy.env`;
- workflow variables;
- documentation;
- workflow output;
- commits or pull requests.

GitHub does not display a secret's value after it has been stored.

## Required target repository settings

GitHub Actions must be enabled in the target repository.

The workflow's built-in `GITHUB_TOKEN` receives only:

```yaml
permissions:
  contents: read
```

The separate GitHub App token receives only:

```yaml
permission-contents: write
permission-workflows: write
```

These permissions allow the workflow to push an update branch containing
ordinary files and GitHub Actions workflow files.

The workflow does not request permission to approve or merge pull requests.

## Installing synchronization in a target repository

New repositories created from the updated template receive the workflow and
synchronization scripts automatically.

An existing target repository must receive this file once through a reviewed
pull request:

```text
.github/workflows/update-from-template.yml
```

The first synchronization then adds the remaining managed files.

Before running synchronization for the first time:

1. install the GitHub App on the target repository;
2. select only the target repositories that require synchronization;
3. add `INSTANCE_SYNC_APP_ID` as an Actions repository secret;
4. add `INSTANCE_SYNC_APP_PRIVATE_KEY` as an Actions repository secret;
5. confirm that the App has Contents and Workflows read/write permissions;
6. approve updated App permissions if the App was changed after installation;
7. confirm that normal pull-request review is required before changes reach
   `main`.

After the initial pull request is merged, the product owner can start future
updates from the target repository's Actions page.

## Registering another target repository

To enable another productive instance repository:

1. add the repository to the GitHub App installation's selected repositories;
2. install the synchronization files through a reviewed pull request;
3. add the two required Actions secrets to the target repository;
4. run the workflow manually with `main` or an exact source commit;
5. review the generated comparison and create a pull request;
6. merge only after the target repository's required checks and review pass.

## Traceability

Every synchronization commit records:

- the source repository;
- the selected source reference;
- the exact source commit SHA;
- the target repository's base commit SHA.

The workflow summary also displays this information.

The update branch name includes the first 12 characters of the source commit
SHA.

Example:

```text
chore/update-instance-example-0123456789ab
```

## Existing update branch

If an update branch for the selected source commit already exists, the workflow
does not force-push or replace it.

The workflow reports that the branch already exists and provides the comparison
link again.

If the existing branch is no longer wanted, a maintainer should review it and
delete it through the GitHub website before running the same update again.

## No-change update

If the target already matches the selected source version, the workflow:

- creates no new commit;
- creates no new branch;
- reports that no update is required.

## Validation

The synchronization tests run in the public-safety workflow.

The tests cover:

- managed files copied, added, and removed;
- instance-specific files never written, and reported;
- a report limited to template changes when `.template-version` exists;
- `.template-version` recorded;
- unchanged `deploy.env` and target `.git` across repeated runs;
- `deploy.env` variable names reported without values;
- a missing target `deploy.env`;
- identical source and target directories.

After the product owner creates the pull request, the target repository's normal
pull-request checks also run.

## Reviewing an update

Before merging, verify:

- the requested source reference is correct;
- the exact source commit belongs to the intended release or branch;
- the target base commit is correct;
- only managed files and `.template-version` changed;
- the instance-file report has been reviewed and wanted changes ported
  separately;
- no secrets or credentials appear in the changes;
- all required checks pass;
- the required reviewer approves the pull request.

Never merge an update pull request automatically.

## Troubleshooting

Open the target repository's **Actions** page and select the failed
**Update from instance-example** run.

### Source reference not found

Confirm that the entered commit SHA or branch exists in the public source
repository.

### Missing deploy.env

Confirm that this file exists in the target repository root:

```text
deploy.env
```

### Permission denied while pushing the branch

Check:

1. the GitHub App is installed on the target repository;
2. the installation includes this repository under
   **Only select repositories**;
3. the App has **Contents: Read and write**;
4. the App has **Workflows: Read and write**;
5. the `INSTANCE_SYNC_APP_ID` Actions secret exists;
6. the `INSTANCE_SYNC_APP_PRIVATE_KEY` Actions secret exists;
7. the stored private key belongs to the configured App;
8. repository or organization rules allow the App to create update branches.

If the App permissions were changed after installation, review and approve the
updated installation permissions before running the workflow again.

### Update branch already exists

Open the branch using the comparison link shown in the workflow summary.

Review the existing branch, create its pull request, or delete the branch
through GitHub before rerunning the same source version.
