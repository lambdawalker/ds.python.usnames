# Automated releases and PyPI publishing

The PyPI package is `us-synthetic-names`; its repository is `lambdawalker/ds.python.usnames` and its import is `us_names`.

## Normal release flow

1. Merge feature and fix PRs into `main`. Use Conventional Commit squash titles:
   - `fix: correct initials formatting` proposes a patch release.
   - `feat: add another format` proposes a minor release.
   - `feat!: change the query API` marks a breaking change. Before 1.0, configured policy bumps the minor version; at/after 1.0 it bumps the major version.
   - `docs:` and `chore:` changes alone do not normally require a release.
2. Release Please opens or updates a release PR. It updates `pyproject.toml`, the generator version in `us_names/core.py`, the project's entry in `uv.lock`, `CHANGELOG.md`, and its release manifest. The first release is configured as **0.3.0**.
3. Review the release PR and the **Release and publish Python package** run that prepared it. That run builds/tests the generated PR branch. GitHub's built-in token does not trigger normal PR workflows for bot-created PRs, so check this run directly. If your branch protection requires PR-attached status checks, an owner can close/reopen the PR to trigger normal PR CI, or configure a GitHub App token later.
4. Merge the release PR yourself. Do not edit its generated title or remove its release labels. The next `main` run creates the version tag and GitHub release, checks out the tagged commit, builds and validates distributions, and publishes to PyPI. Approve the `pypi` environment if you configured a required reviewer.

No permanent publish branch or personal access token is needed. Ordinary feature merges prepare a release PR; they do not immediately upload to PyPI. The workflow never auto-merges the release PR.

## Required account settings

Existing PyPI Trusted Publisher settings remain unchanged:

| Field | Value |
|---|---|
| PyPI project | `us-synthetic-names` |
| GitHub owner | `lambdawalker` |
| Repository | `ds.python.usnames` |
| Workflow filename | `publish.yml` |
| Environment | `pypi` |

For a new project, register a pending publisher at https://pypi.org/manage/account/publishing/. The first upload creates the project. For an existing project, configure its Publishing settings. PyPI requires verified email and 2FA. No PyPI API-token secret is used.

Create the `pypi` environment in https://github.com/lambdawalker/ds.python.usnames/settings/environments. Optional required reviewers provide a final publishing approval. Automated releases run on the `main` ref, while the retained manual-release path runs on a version tag: if restricting deployment branches/tags, allow **main** and **v*** tags.

In https://github.com/lambdawalker/ds.python.usnames/settings/actions, enable **Allow GitHub Actions to create and approve pull requests**. Release Please needs this setting to open release PRs. Workflow permissions are scoped per job: release management gets repository/PR writes; only the publishing job gets `id-token: write`.

## Why publishing stays in this workflow

Events produced by `GITHUB_TOKEN` do not start another release workflow. `publish.yml` therefore passes Release Please's `release_created`, tag and SHA outputs directly to dependent build/publish jobs in the same run. PyPI's trusted workflow filename remains unchanged.

The build job tests the library, checks all three version locations, builds a wheel and sdist, runs strict Twine metadata checks, and smoke-tests an installed wheel outside the checkout. The publishing job receives only the validated distribution artifacts and uses Trusted Publishing.

## Recovery and manual operation

- **Run workflow** on `main` reconciles release PRs and merged releases. It may publish if a merged release PR has not yet been released; it is not a build-only command anymore.
- If package building/uploading fails after release creation, use **Re-run failed jobs** on that same run. This preserves its release outputs. Starting a new run will not recreate an already-created release.
- If a partial upload occurred, inspect PyPI before retrying. Existing version filenames cannot be overwritten. The workflow does not silently skip existing files.
- Manual GitHub releases remain supported for recovery: tags must match the package version (`v0.3.0`, for example). Do not manually publish the same version while its automated release PR is pending.
- Do not hand-bump versions for routine releases; Release Please owns the changes. Do not remove the `x-release-please-version` annotation in `core.py`.

After the initial release succeeds:

```sh
python -m pip install us-synthetic-names==0.3.0
python -m us_names download
python -m us_names generate --format full --count 10 --seed 42
```

The database stays in `ds.source.usnames` releases and is not included in PyPI distributions. Dataset and library releases are independent. No code license has been selected automatically; choose and declare one separately if intended.

References:
- https://github.com/googleapis/release-please-action
- https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/
