"""Binary sensor platform for First Alert by Resideo."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

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
from .entity import ResideoEntity

PARALLEL_UPDATES = 0  # Coordinator handles all updates


@dataclass(frozen=True, kw_only=True)
class ResideoBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes a Resideo binary sensor entity."""

    value_fn: Callable[[DeviceState], bool]


BINARY_SENSOR_DESCRIPTIONS: tuple[ResideoBinarySensorEntityDescription, ...] = (
    # Primary alarm sensors (enabled by default)
    ResideoBinarySensorEntityDescription(
        key="smoke",
        translation_key="smoke",
        device_class=BinarySensorDeviceClass.SMOKE,
        value_fn=lambda state: state.smoke_state == ALARM_STATE_ALARM,
    ),
    ResideoBinarySensorEntityDescription(
        key="co",
        translation_key="co",
        device_class=BinarySensorDeviceClass.CO,
        value_fn=lambda state: state.co_state == ALARM_STATE_ALARM,
    ),
    ResideoBinarySensorEntityDescription(
        key="malfunction",
        translation_key="malfunction",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda state: state.malfunction_state
        not in (ALARM_STATE_NONE, ALARM_STATE_UNKNOWN),
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
    ),
    # Additional alarm states (enabled by default)
    ResideoBinarySensorEntityDescription(
        key="test_mode",
        translation_key="test_mode",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=lambda state: state.test_state == ALARM_STATE_TESTING,
    ),
    ResideoBinarySensorEntityDescription(
        key="silenced",
        translation_key="silenced",
        value_fn=lambda state: state.silence_state == ALARM_STATE_SILENCED,
    ),
    ResideoBinarySensorEntityDescription(
        key="end_of_life",
        translation_key="end_of_life",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda state: state.eol_state == ALARM_STATE_EOL_YES,
    ),
    ResideoBinarySensorEntityDescription(
        key="early_warning",
        translation_key="early_warning",
        value_fn=lambda state: state.early_warning is True,
    ),
    # Diagnostic sensors (disabled by default)
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

    entities: list[ResideoBinarySensor] = []
    for device_id, device_state in coordinator.data.items():
        for description in BINARY_SENSOR_DESCRIPTIONS:
            entities.append(
                ResideoBinarySensor(
                    coordinator=coordinator,
                    device_id=device_id,
                    description=description,
                )
            )

    async_add_entities(entities)


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
