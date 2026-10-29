"""Account setup, tank selection, reauthentication and options."""

import probatio as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import dt as dt_util

from .api import ApiError, AuthError, LevelgasClient
from .const import DEFAULT_POLL_HOURS, DEFAULT_SMOOTHING_SAMPLES, DEFAULT_TIMEZONE, DOMAIN


def credentials_schema(email=None):
    return vol.Schema(
        {
            vol.Required("email", **({"default": email} if email else {})): str,
            vol.Required("password"): selector.TextSelector(
                selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
            ),
        }
    )


class LevelgasConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return LevelgasOptionsFlow()

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            self.credentials = user_input
            self.client = LevelgasClient(
                async_get_clientsession(self.hass), user_input["email"], user_input["password"]
            )
            try:
                await self.client.login()
                self.tanks = await self.client.tanks()
            except AuthError:
                errors["base"] = "invalid_auth"
            except ApiError:
                errors["base"] = "cannot_connect"
            else:
                if not self.tanks:
                    return self.async_abort(reason="no_tanks")
                if len(self.tanks) == 1:
                    return await self._finish(self.tanks[0])
                return await self.async_step_tank()
        return self.async_show_form(step_id="user", data_schema=credentials_schema(), errors=errors)

    async def async_step_tank(self, user_input=None):
        if user_input is not None:
            for tank in self.tanks:
                if tank["tankHash"] == user_input["tank_hash"]:
                    return await self._finish(tank)
            return self.async_abort(reason="no_tanks")
        options = [
            selector.SelectOptionDict(
                value=t["tankHash"], label=str(t.get("name") or t.get("tankName") or t["tankHash"])
            )
            for t in self.tanks
        ]
        return self.async_show_form(
            step_id="tank",
            data_schema=vol.Schema(
                {
                    vol.Required("tank_hash"): selector.SelectSelector(
                        selector.SelectSelectorConfig(options=options)
                    )
                }
            ),
        )

    async def _finish(self, tank):
        await self.async_set_unique_id(tank["tankHash"])
        self._abort_if_unique_id_configured()
        name = tank.get("name") or tank.get("tankName") or "Tank"
        return self.async_create_entry(
            title=f"Levelgas {name}",
            data={
                **self.credentials,
                "tank_hash": tank["tankHash"],
                "tank_name": name,
                "session": self.client.session_token,
            },
        )

    async def async_step_reauth(self, entry_data):
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        entry = self._get_reauth_entry()
        errors = {}
        if user_input is not None:
            client = LevelgasClient(
                async_get_clientsession(self.hass), user_input["email"], user_input["password"]
            )
            try:
                await client.login()
                tanks = await client.tanks()
            except AuthError:
                errors["base"] = "invalid_auth"
            except ApiError:
                errors["base"] = "cannot_connect"
            else:
                if not any(t["tankHash"] == entry.data["tank_hash"] for t in tanks):
                    errors["base"] = "wrong_account"
                else:
                    return self.async_update_reload_and_abort(
                        entry, data_updates={**user_input, "session": client.session_token}
                    )
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=credentials_schema(entry.data["email"]),
            errors=errors,
        )


class LevelgasOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        errors = {}
        if user_input is not None:
            count = user_input["smoothing_samples"]
            if type(count) is not int or count < 3 or count > 31 or count % 2 != 1:
                errors["base"] = "invalid_window"
            elif await dt_util.async_get_time_zone(user_input["timezone"]) is None:
                errors["base"] = "invalid_timezone"
            else:
                return self.async_create_entry(title="", data=user_input)
        options = self.config_entry.options
        return self.async_show_form(
            step_id="init",
            errors=errors,
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "poll_hours", default=options.get("poll_hours", DEFAULT_POLL_HOURS)
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=24)),
                    vol.Required(
                        "smoothing_samples",
                        default=options.get("smoothing_samples", DEFAULT_SMOOTHING_SAMPLES),
                    ): vol.All(vol.Coerce(int), vol.Range(min=3, max=31)),
                    vol.Required(
                        "timezone", default=options.get("timezone", DEFAULT_TIMEZONE)
                    ): str,
                }
            ),
        )
