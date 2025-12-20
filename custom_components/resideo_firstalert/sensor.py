"""Sensor platform for First Alert by Resideo."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, SIGNAL_STRENGTH_DECIBELS_MILLIWATT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import DeviceState
from .const import DOMAIN
from .coordinator import ResideoDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class ResideoSensorEntityDescription(SensorEntityDescription):
    """Describes a Resideo sensor entity."""

    value_fn: Callable[[DeviceState], Any]


SENSOR_DESCRIPTIONS: tuple[ResideoSensorEntityDescription, ...] = (
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
        options=["ac", "battery", "unknown"],
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
        value_fn=lambda state: state.last_message_time,
    ),
    ResideoSensorEntityDescription(
        key="firmware_version",
        translation_key="firmware_version",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda state: state.firmware_version,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Resideo sensors from a config entry."""
    coordinator = entry.runtime_data

    entities: list[ResideoSensor] = []
    for device_id, device_state in coordinator.data.items():
        for description in SENSOR_DESCRIPTIONS:
            entities.append(
                ResideoSensor(
                    coordinator=coordinator,
                    device_id=device_id,
                    description=description,
                )
            )

    async_add_entities(entities)


class ResideoSensor(CoordinatorEntity[ResideoDataUpdateCoordinator], SensorEntity):
    """Representation of a Resideo sensor."""

    entity_description: ResideoSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ResideoDataUpdateCoordinator,
        device_id: str,
        description: ResideoSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._device_id = device_id
        self._attr_unique_id = f"{device_id}_{description.key}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device_state = self.coordinator.data.get(self._device_id)
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

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        device_state = self.coordinator.data.get(self._device_id)
        if device_state is None:
            return None
        return self.entity_description.value_fn(device_state)
