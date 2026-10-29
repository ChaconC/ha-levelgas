"""Native Home Assistant support for Levelgas."""

from homeassistant.const import Platform

from .coordinator import LevelgasCoordinator

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass, entry):
    coordinator = LevelgasCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_update_options))
    return True


async def async_update_options(hass, entry):
    if dict(entry.options) != entry.runtime_data.configured_options:
        await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass, entry):
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass, entry):
    from homeassistant.helpers.storage import Store

    await Store(hass, 1, f"levelgas.{entry.entry_id}.history").async_remove()
