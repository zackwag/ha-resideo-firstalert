"""Button platform for First Alert by Resideo."""

from __future__ import annotations

import logging

from homeassistant.components.button import ButtonDeviceClass, ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import ResideoDataUpdateCoordinator
from .entity import ResideoEntity

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Resideo button entities from a config entry."""
    coordinator: ResideoDataUpdateCoordinator = entry.runtime_data

    entities: list[ResideoIdentifyButton] = []
    for device_id in coordinator.data:
        entities.append(ResideoIdentifyButton(coordinator, device_id))

    async_add_entities(entities)


class ResideoIdentifyButton(ResideoEntity, ButtonEntity):
    """Button to identify (chirp/flash) a smoke detector."""

    _attr_device_class = ButtonDeviceClass.IDENTIFY
    _attr_translation_key = "identify"

    def __init__(
        self,
        coordinator: ResideoDataUpdateCoordinator,
        device_id: str,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator, device_id, "identify")

    async def async_press(self) -> None:
        """Send the identify command."""
        _LOGGER.debug("Sending identify command to device %s", self._device_id)
        await self.coordinator.client.identify_device(self._device_id)
