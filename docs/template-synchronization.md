# Template synchronization

Product owners can update their ChaBo instance repository from the public `ChaBo-Project/instance-example` repository when they are ready.

Updates are not pushed centrally to all instance repositories. Each product owner starts the update workflow from their own target repository.

No Git CLI commands are required on the product owner's computer.

## Overview

The target repository contains the workflow:

```text
.github/workflows/update-from-template.yml
```

The product owner starts this workflow manually from the target repository's GitHub Actions page.

The workflow:

1. checks out the target repository's current `main` branch;
2. downloads the selected version of the public source template;
3. copies shared template files into the target checkout;
4. preserves the target repository's `deploy.env`;
5. creates a normal commit on a separate update branch;
6. pushes the update branch to the target repository;
7. provides a GitHub comparison link.

The product owner uses the comparison link to create a pull request through the GitHub website.

The workflow never merges the pull request automatically.

## Source repository

The public source template is:

```text
https://github.com/ChaBo-Project/instance-example
```

The source repository can be downloaded without a token because it is public.

## Choosing the source version

When starting the workflow, the product owner provides a source reference.

The source reference can be:

- a published release tag, such as `v1.2.0`;
- an exact source commit SHA;
- the `main` branch.

### Published release tag

Use a release tag for a stable and reproducible productive update.

Example:

```text
v1.2.0
```

This ensures that the same template version can be reviewed and applied again later.

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

to synchronize the latest commit currently available on the source repository's `main` branch.

The `main` branch and the latest published release are not necessarily the same version. A release tag is preferred for productive updates.

## Starting an update

In the target repository:

1. Open the repository on GitHub.
2. Select **Actions**.
3. Select **Update from instance-example**.
4. Select **Run workflow**.
5. Enter the required release tag, commit SHA, or branch in **Source ref**.
6. Select **Run workflow** again.
7. Wait for the workflow to finish.
8. Open the completed workflow run.
9. Read the workflow summary.
10. Select **Open the comparison and create the pull request**.

The comparison page shows the proposed changes before the pull request is created.

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

The pull request is created manually so that the target repository's normal pull-request workflows run.

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

## Protected target files

The following target content is never synchronized from the source:

```text
.git
deploy.env
```

The workflow verifies that `deploy.env` remains unchanged.

If `deploy.env` does not exist in the target repository root, synchronization stops with an error.

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

## Shared files

All other files are treated as shared template files.

The synchronization supports:

- newly added files;
- modified files;
- renamed files;
- deleted files;
- new directories;
- deleted directories;
- file-to-directory changes;
- directory-to-file changes;
- symbolic links.

A file that exists only in the target repository is proposed for deletion unless it is `.git` or `deploy.env`.

Product owners must therefore review every generated comparison and pull request for unintended deletion of target-specific files.

## Authentication

No GitHub App private key or personal access token is required for this workflow.

Reading the source repository requires no credentials because the source is public.

The workflow uses the target repository's temporary `GITHUB_TOKEN` only to create and push the update branch inside that same target repository.

The token is not committed to the repository and is not displayed in the workflow output.

The workflow does not use the token to merge changes.

## Required target repository settings

GitHub Actions must be enabled in the target repository.

The workflow requests:

```yaml
permissions:
  contents: write
```

This permission is used only to push the update branch.

Repository or organization policy must allow the workflow's `GITHUB_TOKEN` to write repository contents.

The workflow does not request permission to approve or merge pull requests.

## Installing the workflow in a target repository

New repositories created from the updated template receive the workflow and synchronization scripts automatically.

An existing target repository must receive these files once through a reviewed pull request:

```text
.github/workflows/update-from-template.yml
scripts/sync-template.py
```

The target should also receive:

```text
scripts/test-sync-template.py
```

After that initial pull request is merged, the product owner can start future updates from the target repository's Actions page.

## Traceability

Every synchronization commit records:

- the source repository;
- the selected source reference;
- the exact source commit SHA;
- the target repository's base commit SHA.

The workflow summary also displays this information.

The update branch name includes the first 12 characters of the source commit SHA.

Example:

```text
chore/update-instance-example-0123456789ab
```

## Existing update branch

If an update branch for the selected source commit already exists, the workflow does not force-push or replace it.

The workflow reports that the branch already exists and provides the comparison link again.

If the existing branch is no longer wanted, a maintainer should review it and delete it through the GitHub website before running the same update again.

## No-change update

If the target already matches the selected source version, the workflow:

- creates no new commit;
- creates no new branch;
- reports that no update is required.

## Validation

The synchronization tests run in the public-safety workflow.

The tests cover:

- modified shared files;
- newly added shared files;
- deleted shared files;
- file and directory type changes;
- copied workflow files;
- unchanged `deploy.env`;
- preservation of the target `.git` directory;
- a second synchronization with no additional changes;
- a missing target `deploy.env`;
- identical source and target directories;
- permission failures.

After the product owner creates the pull request, the target repository's normal pull-request checks also run.

## Reviewing an update

Before merging, verify:

- the requested source reference is correct;
- the exact source commit belongs to the intended release or branch;
- the target base commit is correct;
- `deploy.env` has no changes;
- no target-specific files are removed unintentionally;
- no secrets or credentials appear in the changes;
- all required checks pass;
- the required reviewer approves the pull request.

Never merge an update pull request automatically.

## Troubleshooting

Open the target repository's **Actions** page and select the failed **Update from instance-example** run.

### Source reference not found

Confirm that the entered release tag, commit SHA, or branch exists in the public source repository.

### Missing deploy.env

Confirm that this file exists in the target repository root:

```text
deploy.env
```

### Permission denied while pushing the branch

Check:

1. the target repository's **Settings**;
2. **Actions**;
3. **General**;
4. **Workflow permissions**;
5. organization policies that may prevent `contents: write`.

### Update branch already exists

Open the branch using the comparison link shown in the workflow summary.

Review the existing branch, create its pull request, or delete the branch through GitHub before rerunning the same source version.

### Target-specific file is proposed for deletion

Do not merge the pull request until the file is reviewed.

If the file must remain target-specific, the synchronization design must be updated to protect it explicitly.
