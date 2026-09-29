# Publishing to PyPI

The PyPI distribution name is **us-synthetic-names**. The GitHub repository is **lambdawalker/ds.python.usnames**, and the Python import is **us_names**. These names serve different purposes and do not have to match.

This repository uses [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/), which exchanges GitHub Actions' identity for short-lived upload credentials. Do not create a PyPI API token or add a `PYPI_API_TOKEN` secret for this workflow. Linking accounts alone does not configure this project/workflow trust.

## One-time setup by the owner

1. Sign into PyPI with a verified email address and two-factor authentication.
2. Open https://pypi.org/manage/account/publishing/ and add a **pending publisher**, choosing GitHub. Use these exact values:

   | Field | Value |
   |---|---|
   | PyPI project name | `us-synthetic-names` |
   | Owner | `lambdawalker` |
   | Repository name | `ds.python.usnames` |
   | Workflow name | `publish.yml` |
   | Environment name | `pypi` |

   The workflow field is the filename, not the display title or full `.github/workflows/` path. A pending publisher creates the PyPI project on the first successful upload; no initial token upload is needed. It does not reserve a project name. If the project already exists under your account, configure the same publisher under that project's **Publishing** settings instead.

3. In https://github.com/lambdawalker/ds.python.usnames/settings/environments create an environment named **pypi**. No secrets are required. For an optional manual approval step, configure yourself as a required reviewer. If you restrict deployment tags, allow `v*` tags; a `main`-only branch rule would block release publishing.
4. Check that the **Build and publish Python package** workflow passes on `main`.

## First release

The current library version is `0.3.0`.

1. Open https://github.com/lambdawalker/ds.python.usnames/releases/new.
2. Create a new tag **v0.3.0**, targeting the updated **main** branch that contains `publish.yml`.
3. Use a title such as **US synthetic names 0.3.0**, add release notes, and click **Publish release**. Saving a draft does not upload to PyPI.
4. Watch **Actions → Build and publish Python package**. Approve the `pypi` environment if you enabled a reviewer.
5. The workflow runs tests, checks version/tag consistency, builds a wheel and source distribution, checks metadata with Twine, tests the installed wheel, and publishes with Trusted Publishing.
6. After success, test installation in a fresh virtual environment:

   ```sh
   python -m pip install us-synthetic-names==0.3.0
   python -m us_names download
   python -m us_names generate --format full --count 10 --seed 42
   ```

The database is not uploaded to PyPI. It remains a GitHub release asset in `ds.source.usnames`, downloaded explicitly by the library.

## Later releases

Update both `[project].version` in `pyproject.toml` and `VERSION` in `us_names/core.py`, then run `uv lock` to update the lockfile. Commit the change, wait for CI, and publish a GitHub release with the matching `v<version>` tag. Each PyPI version must be new; previously used filenames cannot be overwritten, even after deletion. Dataset versions are independent of library versions.

Pushes, pull requests and **Run workflow** build and check the package only. Uploading occurs only on a **published GitHub release** in this repository. Pre-releases also publish: use a PEP 440 version such as `0.4.0rc1` and tag `v0.4.0rc1` when intentionally releasing a candidate.

If publishing fails because trust is missing, finish the pending-publisher setup with the exact values above, then use **Re-run failed jobs**. For a partial upload, inspect which files reached PyPI before retrying; the workflow deliberately does not silently skip existing files.

## Tokens and project creation

Project-scoped API tokens apply to existing projects. Trusted Publishing avoids the first-upload bootstrap problem via pending publishers. After the project is created, the publisher becomes an ordinary project publisher automatically. PyPI and TestPyPI have separate accounts/publisher configurations; this workflow targets production PyPI only.

The repository currently does not declare a code license. No license was selected automatically as part of publishing setup; add your chosen license and matching package metadata if you intend to grant reuse rights.

References:
- https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/
- https://docs.pypi.org/trusted-publishers/using-a-publisher/
- https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/
