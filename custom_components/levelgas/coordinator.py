"""One API poll shared by all Levelgas entities."""

import logging
from datetime import timedelta

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ApiError, AuthError, LevelgasClient
from .const import DEFAULT_POLL_HOURS, DEFAULT_SMOOTHING_SAMPLES, DEFAULT_TIMEZONE, DOMAIN
from .model import Smoother, normalize_tank

_LOGGER = logging.getLogger(__name__)


class LevelgasCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry):
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(hours=entry.options.get("poll_hours", DEFAULT_POLL_HOURS)),
        )
        self.entry = entry
        self.configured_options = dict(entry.options)
        self.zone = entry.options.get("timezone", DEFAULT_TIMEZONE)
        self.client = LevelgasClient(
            async_get_clientsession(hass),
            entry.data["email"],
            entry.data["password"],
            entry.data.get("session"),
        )
        self.store = Store(hass, 1, f"{DOMAIN}.{entry.entry_id}.history")
        self.saved_history = None

    async def _async_setup(self):
        self.saved_history = await self.store.async_load()
        self.smoother = await self.hass.async_add_executor_job(
            Smoother,
            self.entry.options.get("smoothing_samples", DEFAULT_SMOOTHING_SAMPLES),
            self.zone,
            self.saved_history,
        )

    async def _async_update_data(self):
        try:
            tank = await self.client.tank(self.entry.data["tank_hash"])
            reading = normalize_tank(tank, self.zone)
            reading.update(self.smoother.update(reading, tank.get("levelHistory")))
        except AuthError as error:
            raise ConfigEntryAuthFailed("Levelgas credentials were rejected") from error
        except (ApiError, ValueError) as error:
            raise UpdateFailed("Could not retrieve valid Levelgas readings") from error
        if self.client.session_token != self.entry.data.get("session"):
            self.hass.config_entries.async_update_entry(
                self.entry, data={**self.entry.data, "session": self.client.session_token}
            )
        snapshot = self.smoother.snapshot()
        if snapshot != self.saved_history:
            await self.store.async_save(snapshot)
            self.saved_history = snapshot
        return reading
