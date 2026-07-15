"""The Bosso Lights integration"""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import BossoApiClient
from .const import CONF_ACCESS_TOKEN, CONF_REFRESH_TOKEN, DOMAIN
from .coordinator import BossoCoordinator

_LOGGER = logging.getLogger(__name__)
PLATFORMS: list[Platform] = [Platform.LIGHT, Platform.SELECT]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Smart Lighting from a config entry."""
    _LOGGER.info("Smart Lighting integration v1.2.1 loading")

    api = BossoApiClient(
        async_get_clientsession(hass),
        access_token=entry.data.get(CONF_ACCESS_TOKEN),
        refresh_token=entry.data.get(CONF_REFRESH_TOKEN),
    )

    # Persist updated tokens whenever the API client refreshes them
    def _save_tokens(access: str, refresh: str) -> None:
        hass.config_entries.async_update_entry(
            entry,
            data={
                **entry.data,
                CONF_ACCESS_TOKEN: access,
                CONF_REFRESH_TOKEN: refresh,
            },
        )

    api.on_tokens_updated = _save_tokens

    coordinator = BossoCoordinator(hass, entry, api)
    await coordinator.async_config_entry_first_refresh()
    # Load the effects and predefined presets catalogs once (best-effort;
    # non-fatal if they fail). User-defined presets are NOT loaded here —
    # they're refreshed automatically on every coordinator poll cycle
    # (see BossoCoordinator._async_update_data) since they can change at
    # any time from other clients, unlike predefined presets.
    await coordinator.async_load_effects()
    await coordinator.async_load_predefined_presets()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok