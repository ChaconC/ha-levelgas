# Development

Use Python 3.14.2+ and [uv](https://docs.astral.sh/uv/):

```sh
uv sync --frozen
uv run pytest -q
uv run ruff check custom_components tests scripts
uv run ruff format --check custom_components tests scripts
uv run python scripts/validate.py
uv run python scripts/package.py
```

Tests run against Home Assistant 2026.10.4. API tests use a loopback HTTP server;
HA lifecycle/config-flow tests mock the external Levelgas service. Tests require
no real account. Never put credentials, APKs, captured responses or `.storage`
files in tests, issues, commits, or release assets.

Use Conventional Commits, for example `fix: preserve filter history on restart`.
Include a failing regression test before changing data or lifecycle behavior.

## Publish the prepared repository

The local repository and manifest are prepared for `ChaconC/ha-levelgas`.
These commands create a public repository and publish it; they are not run by tests:

```sh
gh repo create ChaconC/ha-levelgas --public --source=. --remote=origin \
  --description 'Native Home Assistant integration for Levelgas tank monitors' --push
gh repo edit ChaconC/ha-levelgas --enable-issues \
  --add-topic home-assistant --add-topic hacs --add-topic integration --add-topic levelgas
```

Wait for **Tests**, **HACS validation**, and **hassfest** to pass in Actions. HACS
checks involving GitHub description, topics, issues and public visibility can only
run against the published repository. Check the repository URL in README and
manifest if you choose a different name.

## Release

Update the version in `manifest.json` and `pyproject.toml`, and add release notes
to `CHANGELOG.md`. Keep the tag version equal to the manifest version.

```sh
uv run pytest -q
uv run python scripts/validate.py
git tag 1.0.0
git push origin 1.0.0
gh release create 1.0.0 --title '1.0.0' --notes-file docs/releases/1.0.0.md
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
