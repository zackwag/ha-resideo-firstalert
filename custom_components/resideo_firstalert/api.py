"""API client for First Alert by Resideo — re-exported from pyresideo-firstalert."""

from resideo_firstalert_api import (
    DeviceState,
    Location,
    ResideoApiClient,
    ResideoApiError,
    ResideoAuthError,
    ResideoConnectionError,
)

__all__ = [
    "DeviceState",
    "Location",
    "ResideoApiClient",
    "ResideoApiError",
    "ResideoAuthError",
    "ResideoConnectionError",
]
