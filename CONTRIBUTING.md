# Development

Use Python 3.14.2+ and [uv](https://docs.astral.sh/uv/):

```sh
uv sync --locked --python 3.14
uv run --frozen pytest -q
uv run --frozen ruff check custom_components tests scripts
uv run --frozen ruff format --check custom_components tests scripts
uv run --frozen python scripts/validate.py
uv run --frozen python scripts/package.py
```

Tests run against Home Assistant 2026.10.4. API tests use a loopback HTTP server;
HA lifecycle/config-flow tests mock the external Levelgas service. Tests require
no real account.

Use Conventional Commits, for example `fix: preserve filter history on restart`.
Include a failing regression test before changing data or lifecycle behavior.

## Pull request checks

The [Validate workflow](.github/workflows/validate.yaml) runs on every pull request,
push, and manual dispatch. New commits cancel older validation runs for the same
PR or branch. Each job has a 15-minute timeout.

| Check | Validates |
| --- | --- |
| Lint and formatting | Ruff lint rules and Python formatting |
| Tests | pytest suite, integration metadata and translations, and installation ZIP build |
| HACS validation | HACS integration and repository requirements |
| hassfest | Home Assistant integration requirements |

Both Python jobs use `uv sync --locked` so a stale or missing lockfile fails CI.
When changing dependencies, run `uv lock` and commit `uv.lock` alongside
`pyproject.toml`. Subsequent commands use `--frozen` to avoid changing the lockfile.

The `main` branch requires pull requests and all four checks listed above, with
the branch up to date before merging. These requirements also apply to repository
administrators. Approving reviews are optional; force pushes and branch deletion
are disabled.

## Release

Update the version in `manifest.json` and `pyproject.toml`, and add release notes
to `CHANGELOG.md` and `docs/releases/`. Run `uv lock` to update the project version
in the lockfile. Merge the release PR after all required checks pass, then tag
the merged commit. Keep the tag version equal to the manifest version.

```sh
uv run pytest -q
uv run python scripts/validate.py
git tag 1.0.1
git push origin 1.0.1
gh release create 1.0.1 --title '1.0.1' --notes-file docs/releases/1.0.1.md
```

The release workflow tests the code, builds `levelgas.zip`, and attaches it to the
release. HACS/Marketplace install the integration directory from GitHub; the ZIP
is also available for manual installation. Nothing under `private/` is packaged.

## Marketplace catalog

A custom repository works without catalog approval. For catalog submission, first
publish a release and pass all HACS and hassfest checks without ignored checks.
Then follow the [catalog submission guide](https://contributors.home-assistant.io/marketplace/guides/catalog/).

References: [repository structure](https://contributors.home-assistant.io/marketplace/reference/repository-structure/),
[hacs.json](https://contributors.home-assistant.io/marketplace/reference/hacs-json/),
[validation](https://contributors.home-assistant.io/marketplace/reference/validation/).
