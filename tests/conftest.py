"""Shared pytest fixtures/setup.

custom_components/resideo_firstalert/__init__.py imports Home Assistant,
which isn't a dependency of this test suite. api.py and auth.py don't import
anything from homeassistant at all, so we register a synthetic
"resideo_firstalert" package pointing at the component directory and import
submodules directly from it, bypassing the package's __init__.py entirely.
"""

from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path

_COMPONENT_DIR = (
    Path(__file__).parent.parent / "custom_components" / "resideo_firstalert"
)

if "resideo_firstalert" not in sys.modules:
    _pkg = types.ModuleType("resideo_firstalert")
    _pkg.__path__ = [str(_COMPONENT_DIR)]
    sys.modules["resideo_firstalert"] = _pkg
    importlib.import_module("resideo_firstalert.const")
    importlib.import_module("resideo_firstalert.api")
    importlib.import_module("resideo_firstalert.auth")
