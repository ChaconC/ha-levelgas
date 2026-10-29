"""Raw readings and a median-smoothed level curve."""

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, EntityCategory
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

SENSORS = (
    SensorEntityDescription(
        key="tank_level",
        translation_key="tank_level",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:propane-tank",
    ),
    SensorEntityDescription(
        key="battery",
        translation_key="battery",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.BATTERY,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="last_reading", translation_key="last_reading", device_class=SensorDeviceClass.TIMESTAMP
    ),
    SensorEntityDescription(
        key="tank_level_smoothed",
        translation_key="tank_level_smoothed",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:chart-bell-curve-cumulative",
        suggested_display_precision=1,
    ),
)


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(LevelgasSensor(entry.runtime_data, description) for description in SENSORS)


class LevelgasSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, description):
        super().__init__(coordinator)
        self.entity_description = description
        tank_hash = coordinator.entry.data["tank_hash"]
        self._attr_unique_id = f"{tank_hash}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, tank_hash)},
            name=f"Levelgas {coordinator.data['tank_name']}",
            manufacturer="Levelgas",
            model="Tank monitor",
        )

    @property
    def native_value(self):
        return self.coordinator.data[self.entity_description.key]

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        if self.entity_description.key == "tank_level_smoothed":
            return {
                "sample_count": data["smoothing_sample_count"],
                "window_start": data["smoothing_window_start"],
                "window_size": self.coordinator.smoother.count,
                "method": "median",
                "last_reading": data["last_reading"].isoformat(),
            }
        return None
