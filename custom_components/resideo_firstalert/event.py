"""Event platform for First Alert by Resideo."""

from __future__ import annotations

from homeassistant.components.event import EventDeviceClass, EventEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import ResideoDataUpdateCoordinator
from .entity import ResideoEntity

PARALLEL_UPDATES = 0

ALARM_EVENT_TYPES = [
    "smoke_alarm",
    "smoke_early_warning",
    "smoke_interconnect_alarm",
    "co_alarm",
    "co_early_warning",
    "co_interconnect_alarm",
    "battery_low",
    "battery_replace",
    "power_ac_loss",
    "power_ac_restored",
    "malfunction",
    "end_of_life",
    "silence",
    "test",
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Resideo event entities from a config entry."""
    coordinator: ResideoDataUpdateCoordinator = entry.runtime_data

    entities: list[ResideoAlarmEvent] = []
    for device_id in coordinator.data:
        entities.append(ResideoAlarmEvent(coordinator, device_id))

    async_add_entities(entities)


class ResideoAlarmEvent(ResideoEntity, EventEntity):
    """Event entity that fires when alarm state changes are detected."""

    _attr_device_class = EventDeviceClass.DOORBELL  # closest built-in class
    _attr_event_types = ALARM_EVENT_TYPES
    _attr_translation_key = "alarm_event"

    def __init__(
        self,
        coordinator: ResideoDataUpdateCoordinator,
        device_id: str,
    ) -> None:
        """Initialize the event entity."""
        super().__init__(coordinator, device_id, "alarm_event")
        self._prev_smoke: str | None = None
        self._prev_co: str | None = None
        self._prev_battery: str | None = None
        self._prev_power: str | None = None
        self._prev_malfunction: str | None = None
        self._prev_eol: str | None = None
        self._prev_silence: str | None = None
        self._prev_test: str | None = None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        device_state = self._device_state
        if device_state is None:
            super()._handle_coordinator_update()
            return

        # On first load, just record state without firing events
        if self._prev_smoke is None:
            self._prev_smoke = device_state.smoke_state
            self._prev_co = device_state.co_state
            self._prev_battery = device_state.battery_state
            self._prev_power = device_state.power_state
            self._prev_malfunction = device_state.malfunction_state
            self._prev_eol = device_state.eol_state
            self._prev_silence = device_state.silence_state
            self._prev_test = device_state.test_state
            super()._handle_coordinator_update()
            return

        # Detect smoke state changes
        if device_state.smoke_state != self._prev_smoke:
            event_type = self._classify_smoke(device_state.smoke_state)
            if event_type:
                self._trigger_event(
                    event_type,
                    {"state": device_state.smoke_state, "event_source": device_state.alarm_event_sources.get("smoke")},
                )
            self._prev_smoke = device_state.smoke_state

        # Detect CO state changes
        if device_state.co_state != self._prev_co:
            event_type = self._classify_co(device_state.co_state)
            if event_type:
                self._trigger_event(
                    event_type,
                    {"state": device_state.co_state, "event_source": device_state.alarm_event_sources.get("co")},
                )
            self._prev_co = device_state.co_state

        # Detect battery changes
        if device_state.battery_state != self._prev_battery:
            if device_state.battery_state == "low":
                self._trigger_event("battery_low", {"state": device_state.battery_state})
            elif device_state.battery_state in ("replace", "critical"):
                self._trigger_event("battery_replace", {"state": device_state.battery_state})
            self._prev_battery = device_state.battery_state

        # Detect power changes
        if device_state.power_state != self._prev_power:
            if device_state.power_state in ("dc", "acToDc", "acLoss"):
                self._trigger_event("power_ac_loss", {"state": device_state.power_state})
            elif device_state.power_state in ("ac", "dcToAc", "acRestored", "acOnly"):
                if self._prev_power in ("dc", "acToDc", "acLoss"):
                    self._trigger_event("power_ac_restored", {"state": device_state.power_state})
            self._prev_power = device_state.power_state

        # Detect malfunction changes
        if device_state.malfunction_state != self._prev_malfunction:
            if device_state.malfunction_state not in ("none", "unknown"):
                self._trigger_event("malfunction", {"state": device_state.malfunction_state})
            self._prev_malfunction = device_state.malfunction_state

        # Detect EOL changes
        if device_state.eol_state != self._prev_eol:
            if device_state.eol_state in ("yes", "eolWarning", "expired"):
                self._trigger_event("end_of_life", {"state": device_state.eol_state})
            self._prev_eol = device_state.eol_state

        # Detect silence changes
        if device_state.silence_state != self._prev_silence:
            if device_state.silence_state == "silenced":
                self._trigger_event("silence", {"state": device_state.silence_state})
            self._prev_silence = device_state.silence_state

        # Detect test changes
        if device_state.test_state != self._prev_test:
            if device_state.test_state == "testing":
                self._trigger_event("test", {"state": device_state.test_state})
            self._prev_test = device_state.test_state

        super()._handle_coordinator_update()

    @staticmethod
    def _classify_smoke(state: str) -> str | None:
        if state == "idle":
            return None
        if "InterconnectAlarm" in state or "interconnectAlarm" in state:
            return "smoke_interconnect_alarm"
        if "EarlyWarning" in state or "earlyWarning" in state:
            return "smoke_early_warning"
        return "smoke_alarm"

    @staticmethod
    def _classify_co(state: str) -> str | None:
        if state == "idle":
            return None
        if "InterconnectAlarm" in state or "interconnectAlarm" in state:
            return "co_interconnect_alarm"
        if "EarlyWarning" in state or "earlyWarning" in state:
            return "co_early_warning"
        return "co_alarm"
