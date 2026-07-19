"""Binary sensor platform for First Alert by Resideo."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import DeviceState
from .const import (
    ALARM_STATE_ALARM,
    ALARM_STATE_EOL_YES,
    ALARM_STATE_LOW,
    ALARM_STATE_NONE,
    ALARM_STATE_SILENCED,
    ALARM_STATE_TESTING,
    ALARM_STATE_UNKNOWN,
)
from .coordinator import ResideoDataUpdateCoordinator
from .entity import ResideoEntity, async_add_entities_for_devices

PARALLEL_UPDATES = 0  # Coordinator handles all updates


def _epoch_to_iso(epoch: int | None) -> str | None:
    """Convert a unix epoch timestamp to an ISO 8601 string."""
    if epoch is None:
        return None
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()


@dataclass(frozen=True, kw_only=True)
class ResideoBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes a Resideo binary sensor entity."""

    value_fn: Callable[[DeviceState], bool]
    # Key into DeviceState.alarm_timestamps for a "last_changed" attribute,
    # for sensors backed by an alarmState sub-object. None if not applicable.
    alarm_key: str | None = None


BINARY_SENSOR_DESCRIPTIONS: tuple[ResideoBinarySensorEntityDescription, ...] = (
    # Primary alarm sensors (enabled by default)
    ResideoBinarySensorEntityDescription(
        key="smoke",
        translation_key="smoke",
        device_class=BinarySensorDeviceClass.SMOKE,
        value_fn=lambda state: state.smoke_state == ALARM_STATE_ALARM,
        alarm_key="smoke",
    ),
    ResideoBinarySensorEntityDescription(
        key="co",
        translation_key="co",
        device_class=BinarySensorDeviceClass.CO,
        value_fn=lambda state: state.co_state == ALARM_STATE_ALARM,
        alarm_key="co",
    ),
    ResideoBinarySensorEntityDescription(
        key="malfunction",
        translation_key="malfunction",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda state: state.malfunction_state
        not in (ALARM_STATE_NONE, ALARM_STATE_UNKNOWN),
        alarm_key="malfunction",
    ),
    ResideoBinarySensorEntityDescription(
        key="connectivity",
        translation_key="connectivity",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        value_fn=lambda state: state.is_online,
    ),
    ResideoBinarySensorEntityDescription(
        key="battery_low",
        translation_key="battery_low",
        device_class=BinarySensorDeviceClass.BATTERY,
        value_fn=lambda state: state.battery_state == ALARM_STATE_LOW,
        alarm_key="battery",
    ),
    # Additional alarm states (enabled by default)
    ResideoBinarySensorEntityDescription(
        key="test_mode",
        translation_key="test_mode",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=lambda state: state.test_state == ALARM_STATE_TESTING,
        alarm_key="test",
    ),
    ResideoBinarySensorEntityDescription(
        key="silenced",
        translation_key="silenced",
        value_fn=lambda state: state.silence_state == ALARM_STATE_SILENCED,
        alarm_key="silence",
    ),
    ResideoBinarySensorEntityDescription(
        key="end_of_life",
        translation_key="end_of_life",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda state: state.eol_state == ALARM_STATE_EOL_YES,
        alarm_key="eol",
    ),
    ResideoBinarySensorEntityDescription(
        key="early_warning",
        translation_key="early_warning",
        value_fn=lambda state: state.early_warning is True,
    ),
    # Diagnostic sensors (disabled by default)
    ResideoBinarySensorEntityDescription(
        key="connectivity_computed",
        translation_key="connectivity_computed",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda state: state.is_online_computed,
    ),
    ResideoBinarySensorEntityDescription(
        key="supervision_healthy",
        translation_key="supervision_healthy",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda state: state.is_supervision_healthy,
    ),
    ResideoBinarySensorEntityDescription(
        key="fault",
        translation_key="fault",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda state: state.fault,
    ),
    ResideoBinarySensorEntityDescription(
        key="e2_fault",
        translation_key="e2_fault",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda state: state.e2_fault,
    ),
    ResideoBinarySensorEntityDescription(
        key="photo_fault",
        translation_key="photo_fault",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda state: state.photo_fault,
    ),
    ResideoBinarySensorEntityDescription(
        key="drift_malfunction",
        translation_key="drift_malfunction",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda state: state.drift_malfunction,
    ),
    ResideoBinarySensorEntityDescription(
        key="co_fault",
        translation_key="co_fault",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda state: state.co_fault,
    ),
    ResideoBinarySensorEntityDescription(
        key="temperature_fault",
        translation_key="temperature_fault",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda state: state.temperature_fault,
    ),
    ResideoBinarySensorEntityDescription(
        key="voice_fault",
        translation_key="voice_fault",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda state: state.voice_fault,
    ),
    ResideoBinarySensorEntityDescription(
        key="radio_fault",
        translation_key="radio_fault",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda state: state.radio_fault,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Resideo binary sensors from a config entry."""
    coordinator = entry.runtime_data

    def _entities_for_device(device_id: str) -> list[ResideoBinarySensor]:
        return [
            ResideoBinarySensor(
                coordinator=coordinator,
                device_id=device_id,
                description=description,
            )
            for description in BINARY_SENSOR_DESCRIPTIONS
        ]

    async_add_entities_for_devices(
        coordinator, entry, async_add_entities, _entities_for_device
    )


class ResideoBinarySensor(ResideoEntity, BinarySensorEntity):
    """Representation of a Resideo binary sensor."""

    entity_description: ResideoBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: ResideoDataUpdateCoordinator,
        device_id: str,
        description: ResideoBinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, device_id, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        device_state = self._device_state
        if device_state is None:
            return None
        return self.entity_description.value_fn(device_state)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the last-changed timestamp for alarm-backed sensors."""
        alarm_key = self.entity_description.alarm_key
        device_state = self._device_state
        if alarm_key is None or device_state is None:
            return None
        last_changed = _epoch_to_iso(device_state.alarm_timestamps.get(alarm_key))
        if last_changed is None:
            return None
        return {"last_changed": last_changed}
