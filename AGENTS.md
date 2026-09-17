# Agent instructions for ha-resideo-firstalert

This repo and [pyresideo-firstalert](https://github.com/zackwag/pyresideo-firstalert) are split along a hard boundary: **this repo is the Home Assistant integration; the other repo is the Resideo API client it depends on.** Honor that split.

## The rule

If your change involves any of the following, it belongs in `pyresideo-firstalert` **instead of here**:

- An HTTP request to any Resideo/Auth0 host
- Authentication or token handling of any kind (PKCE, refresh rotation, captcha workarounds, header/user-agent requirements)
- Parsing or shaping data that comes back from Resideo's API
- A new exception type describing an API failure mode

If your change involves any of the following, it belongs **here**:

- Config entries, config flow steps, options flow
- Entities, the coordinator, platforms (`binary_sensor`, `sensor`, `event`)
- `manifest.json`, `strings.json`, translations, diagnostics, repairs
- Anything that imports `homeassistant.*`

Do not reimplement or duplicate API-layer logic in `custom_components/resideo_firstalert/{api,auth,signalr,const}.py` — those four files are re-export shims, not real modules. They should only ever contain an import from `resideo_firstalert_api` and a matching `__all__`.

## Cross-repo changes

1. Land, test, and release the change in `pyresideo-firstalert` first (see that repo's AGENTS.md for its release steps).
2. Bump the `pyresideo-firstalert==X.Y.Z` pin in **both** `custom_components/resideo_firstalert/manifest.json` and `requirements-test.txt` to the newly released version.
3. **Update the relevant shim's import list and `__all__`** to re-export any new name you're about to consume, in the same change that wires it into `config_flow.py`/`coordinator.py`/etc.
4. Only then write the Home Assistant-side code that uses it.

Step 3 is the one that gets skipped. Do not skip it.

## Verify config_flow.py changes by actually importing them

Neither this repo's `pytest` suite nor its `hassfest`/HACS CI actually imports `config_flow.py` (or `coordinator.py`, or any entity platform) — `requirements-test.txt` has no `homeassistant` dependency, and hassfest/HACS validation only check `manifest.json`/`strings.json` schemas, not Python imports. This is a real, currently-open CI gap, not a hypothetical.

**Incident:** browser-assisted login (v2.1.0) added `config_flow.py` imports of four PKCE helper functions from the local `.auth` shim, but the shim's re-export list wasn't updated to include them. Every check passed — `pytest`, `validate` (hassfest), `validate-hacs` — and the release went out with the browser-login step raising `ImportError` on every use. Fixed in v2.1.1.

Before merging any change to `config_flow.py`, `coordinator.py`, `__init__.py`, or an entity platform, verify it actually imports:

```bash
pip install homeassistant   # into a scratch venv, not requirements-test.txt
PYTHONPATH=custom_components python -c "
import resideo_firstalert.config_flow
import resideo_firstalert.coordinator
import resideo_firstalert.__init__
import resideo_firstalert.binary_sensor
import resideo_firstalert.sensor
import resideo_firstalert.event
"
```

If every one of those imports cleanly, the shim boundary is intact. If any of them doesn't, fix the shim before doing anything else.
