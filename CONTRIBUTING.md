# Contributing to ha-resideo-firstalert

> [!NOTE]
> This project isn't actively maintained (see the README) — PRs are reviewed on a best-effort basis, but they are welcome.

## What lives here

This repo is the **Home Assistant integration only** — config flow, coordinator, entities, diagnostics, repairs, `manifest.json`. It talks to Resideo's cloud API exclusively through [`pyresideo-firstalert`](https://github.com/zackwag/pyresideo-firstalert), a separate PyPI package that owns all HTTP/auth/SignalR logic.

It does **not** own:

- HTTP calls to Resideo/Auth0
- Token refresh, PKCE, or any auth-flow logic
- Parsing of Resideo API responses
- Exception types describing API failures

Those all live upstream in `pyresideo-firstalert`. See [AGENTS.md](AGENTS.md) for the full rationale and a decision rule for "which repo does this change belong in."

### The re-export shims

`custom_components/resideo_firstalert/api.py`, `auth.py`, `signalr.py`, and `const.py` are **thin re-export shims** — they import names from `resideo_firstalert_api` and re-list them in `__all__`, purely so the rest of this integration can use stable `.api`/`.auth`/`.signalr`/`.const` import paths. Don't add real logic to these files; add it upstream and re-export it here.

## Dev setup

```bash
git clone https://github.com/zackwag/ha-resideo-firstalert.git
cd ha-resideo-firstalert
cp config/configuration.yaml.example config/configuration.yaml
docker compose up -d
```

Open <http://localhost:8123>, complete onboarding, then add the integration via **Settings → Devices & Services → Add Integration → First Alert by Resideo**. The `custom_components` folder is mounted into the container, so `docker compose restart` picks up code changes.

## Running tests

```bash
pip install -r requirements-test.txt
PYTHONPATH=custom_components python -m pytest tests/ -v
```

These tests cover the re-export shims and the underlying API/auth behavior (inherited from `pyresideo-firstalert`'s own coverage) — they do **not** import or exercise `config_flow.py`, `coordinator.py`, or any entity platform, because that requires a real `homeassistant` install and none is in `requirements-test.txt`. If you change `config_flow.py` or anything importing `homeassistant.*`, verify it by hand — see the note in [AGENTS.md](AGENTS.md) about the v2.1.0 shim regression this exact gap caused.

## Making a change

1. If the change touches Resideo's API surface at all (new endpoint, header, auth flow, response field), it almost certainly belongs in `pyresideo-firstalert`, not here — see AGENTS.md before writing code.
2. If you're consuming a new name from `pyresideo-firstalert`, confirm it's actually re-exported by the relevant shim (`api.py`/`auth.py`/`signalr.py`/`const.py`) before wiring it into `config_flow.py` or elsewhere.
3. Update `strings.json` and `translations/en.json` together — they should stay identical, but there's no build step enforcing that, so keep them in sync by hand.
4. `main` is a protected branch — direct pushes are rejected. All changes, including version bumps, go through a PR with passing CI (`Test`, `pytest`, `validate` (hassfest), `validate-hacs`).

## Releasing

1. Bump `version` in `custom_components/resideo_firstalert/manifest.json` (patch for fixes, minor for features) via a PR, same as any other change.
2. Once merged, trigger the release workflow: `gh workflow run release.yml -f version=X.Y.Z`. It re-runs tests, verifies the manifest version matches, tags `vX.Y.Z`, pushes the tag, and creates the GitHub Release — all in one step. Don't tag manually; let the workflow do it.
