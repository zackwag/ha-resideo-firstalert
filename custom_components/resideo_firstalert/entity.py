"""Base entity for First Alert by Resideo."""

from __future__ import annotations

from collections.abc import Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
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


def async_add_entities_for_devices(
    coordinator: ResideoDataUpdateCoordinator,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
    entities_for_device: Callable[[str], list[Entity]],
) -> None:
    """Add entities for known devices, and for any discovered later.

    Registers a coordinator listener so that devices added to the Resideo
    account after initial setup get their entities created automatically,
    instead of requiring the integration to be reloaded.
    """
    known_device_ids: set[str] = set()

    @callback
    def _add_new_devices() -> None:
        new_device_ids = set(coordinator.data) - known_device_ids
        if not new_device_ids:
            return
        known_device_ids.update(new_device_ids)
        async_add_entities(
            [
                entity
                for device_id in new_device_ids
                for entity in entities_for_device(device_id)
            ]
        )

    entry.async_on_unload(coordinator.async_add_listener(_add_new_devices))
    _add_new_devices()
