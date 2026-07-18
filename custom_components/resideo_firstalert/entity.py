"""Base entity for First Alert by Resideo."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import DeviceState
from .const import DOMAIN
from .coordinator import ResideoDataUpdateCoordinator


class ResideoEntity(CoordinatorEntity[ResideoDataUpdateCoordinator]):
    """Base class for Resideo entities backed by the data coordinator."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ResideoDataUpdateCoordinator,
        device_id: str,
        key: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._attr_unique_id = f"{device_id}_{key}"

    @property
    def _device_state(self) -> DeviceState | None:
        """Return the current device state, if available."""
        return self.coordinator.data.get(self._device_id)

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device_state = self._device_state
        if device_state:
            return DeviceInfo(
                identifiers={(DOMAIN, self._device_id)},
                name=device_state.name,
                manufacturer="First Alert / Resideo",
                model=device_state.sku or device_state.device_type,
                sw_version=device_state.firmware_version,
            )
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=self._device_id,
            manufacturer="First Alert / Resideo",
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return super().available and self._device_id in self.coordinator.data
