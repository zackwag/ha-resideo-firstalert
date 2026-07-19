"""Sensor platform for First Alert by Resideo."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from dateutil.parser import isoparse
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import SIGNAL_STRENGTH_DECIBELS_MILLIWATT, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import DeviceState
from .coordinator import ResideoDataUpdateCoordinator
from .entity import ResideoEntity, async_add_entities_for_devices

PARALLEL_UPDATES = 0  # Coordinator handles all updates


def parse_timestamp(value: str | None) -> datetime | None:
    """Parse an ISO timestamp string to datetime."""
    if value is None:
        return None
    try:
        return isoparse(value)
    except (ValueError, TypeError):
        return None


@dataclass(frozen=True, kw_only=True)
class ResideoSensorEntityDescription(SensorEntityDescription):
    """Describes a Resideo sensor entity."""

    value_fn: Callable[[DeviceState], Any]


SENSOR_DESCRIPTIONS: tuple[ResideoSensorEntityDescription, ...] = (
    # Status sensors (enabled by default)
    ResideoSensorEntityDescription(
        key="battery_status",
        translation_key="battery_status",
        device_class=SensorDeviceClass.ENUM,
        options=["good", "low", "unknown"],
        value_fn=lambda state: state.battery_state,
    ),
    ResideoSensorEntityDescription(
        key="power_source",
        translation_key="power_source",
        device_class=SensorDeviceClass.ENUM,
        options=["ac", "battery", "dc", "unknown"],
        value_fn=lambda state: state.power_state,
    ),
    ResideoSensorEntityDescription(
        key="smoke_status",
        translation_key="smoke_status",
        device_class=SensorDeviceClass.ENUM,
        options=["idle", "alarm", "unknown"],
        value_fn=lambda state: state.smoke_state,
    ),
    ResideoSensorEntityDescription(
        key="co_status",
        translation_key="co_status",
        device_class=SensorDeviceClass.ENUM,
        options=["idle", "alarm", "unknown"],
        value_fn=lambda state: state.co_state,
    ),
    ResideoSensorEntityDescription(
        key="test_status",
        translation_key="test_status",
        device_class=SensorDeviceClass.ENUM,
        options=["idle", "testing", "unknown"],
        value_fn=lambda state: state.test_state,
    ),
    ResideoSensorEntityDescription(
        key="silence_status",
        translation_key="silence_status",
        device_class=SensorDeviceClass.ENUM,
        options=["not_silenced", "silenced", "unknown"],
        value_fn=lambda state: state.silence_state,
    ),
    ResideoSensorEntityDescription(
        key="eol_status",
        translation_key="eol_status",
        device_class=SensorDeviceClass.ENUM,
        options=["no", "yes", "unknown"],
        value_fn=lambda state: state.eol_state,
    ),
    # Configuration sensors (enabled by default)
    ResideoSensorEntityDescription(
        key="language",
        translation_key="language",
        value_fn=lambda state: state.language,
    ),
    # Diagnostic sensors (disabled by default)
    ResideoSensorEntityDescription(
        key="registration_status",
        translation_key="registration_status",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda state: state.registration_status,
    ),
    ResideoSensorEntityDescription(
        key="data_sync_state",
        translation_key="data_sync_state",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda state: state.data_sync_state,
    ),
    ResideoSensorEntityDescription(
        key="debug_level",
        translation_key="debug_level",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda state: state.debug_level,
    ),
    ResideoSensorEntityDescription(
        key="room",
        translation_key="room",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda state: state.room,
    ),
    ResideoSensorEntityDescription(
        key="wifi_signal_strength",
        translation_key="wifi_signal_strength",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda state: state.rssi,
    ),
    ResideoSensorEntityDescription(
        key="wifi_ssid",
        translation_key="wifi_ssid",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda state: state.ssid,
    ),
    ResideoSensorEntityDescription(
        key="last_seen",
        translation_key="last_seen",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda state: parse_timestamp(state.last_message_time),
    ),
    ResideoSensorEntityDescription(
        key="firmware_version",
        translation_key="firmware_version",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda state: state.firmware_version,
    ),
    ResideoSensorEntityDescription(
        key="fw_ver_exec_core",
        translation_key="fw_ver_exec_core",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda state: state.fw_ver_exec_core,
    ),
    ResideoSensorEntityDescription(
        key="fw_ver_sensor_core",
        translation_key="fw_ver_sensor_core",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda state: state.fw_ver_sensor_core,
    ),
    ResideoSensorEntityDescription(
        key="hw_ver_e2c",
        translation_key="hw_ver_e2c",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda state: state.hw_ver_e2c,
    ),
    ResideoSensorEntityDescription(
        key="hw_ver_exec_core",
        translation_key="hw_ver_exec_core",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda state: state.hw_ver_exec_core,
    ),
    ResideoSensorEntityDescription(
        key="hw_ver_sensor_core",
        translation_key="hw_ver_sensor_core",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda state: state.hw_ver_sensor_core,
    ),
    ResideoSensorEntityDescription(
        key="voice_file_version",
        translation_key="voice_file_version",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda state: state.voice_file_ver,
    ),
    ResideoSensorEntityDescription(
        key="running_hours",
        translation_key="running_hours",
        native_unit_of_measurement="h",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda state: state.running_hours,
    ),
    ResideoSensorEntityDescription(
        key="registration_date",
        translation_key="registration_date",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda state: parse_timestamp(state.registration_date),
    ),
    ResideoSensorEntityDescription(
        key="last_firmware_update",
        translation_key="last_firmware_update",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda state: parse_timestamp(state.last_firmware_update_time),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Resideo sensors from a config entry."""
    coordinator = entry.runtime_data

    def _entities_for_device(device_id: str) -> list[ResideoSensor]:
        return [
            ResideoSensor(
                coordinator=coordinator,
                device_id=device_id,
                description=description,
            )
            for description in SENSOR_DESCRIPTIONS
        ]

    async_add_entities_for_devices(
        coordinator, entry, async_add_entities, _entities_for_device
    )


class ResideoSensor(ResideoEntity, SensorEntity):
    """Representation of a Resideo sensor."""

    entity_description: ResideoSensorEntityDescription

    def __init__(
        self,
        coordinator: ResideoDataUpdateCoordinator,
        device_id: str,
        description: ResideoSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, device_id, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        device_state = self._device_state
        if device_state is None:
            return None
        return self.entity_description.value_fn(device_state)
