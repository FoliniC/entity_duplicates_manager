from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
import asyncio
from .api import SAICMGAPIClient
from .coordinator import SAICMGDataUpdateCoordinator
from .const import DOMAIN, LOGGER, PLATFORMS
from .services import async_setup_services, async_unload_services


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up MG SAIC from a config entry with a startup delay."""
    LOGGER.info("MG SAIC: Waiting 30 seconds before starting setup to avoid boot delay.")
    await asyncio.sleep(30)
    return await _async_setup_entry(hass, entry)


async def _async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Actual setup implementation."""
    hass.data.setdefault(DOMAIN, {})

    username = entry.data["username"]
    password = entry.data["password"]
    vin = entry.data.get("vin")
    region = entry.data.get("region")
    username_is_email = entry.data.get("country_code") is None

    client = SAICMGAPIClient(
        username,
        password,
        vin,
        username_is_email,
        region,
        entry.data.get("country_code"),
    )

    try:
        await client.login()

        if not vin:
            LOGGER.error("No VIN specified in Config Entry")
            return False

        vehicles = await client.get_vehicle_info()
        if not any(v.vin == vin for v in vehicles):
            LOGGER.error("VIN %s not found in account vehicles", vin)
            return False

        hass.data[DOMAIN][entry.entry_id] = client

        coordinator = SAICMGDataUpdateCoordinator(hass, client, entry)
        try:
            await coordinator.async_setup()
        except Exception as e:
            LOGGER.warning("Coordinator setup failed, retrying later: %s", e)
            raise ConfigEntryNotReady(f"Timeout or connection error during coordinator setup: {e}") from e

        hass.data[DOMAIN][f"{entry.entry_id}_coordinator"] = coordinator
        hass.data[DOMAIN].setdefault("coordinators_by_vin", {})
        hass.data[DOMAIN]["coordinators_by_vin"][vin] = coordinator

        entry.async_on_unload(entry.add_update_listener(update_listener))

        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        await async_setup_services(hass, client, coordinator)

        LOGGER.info("MG SAIC integration setup completed successfully.")
        return True
    except ConfigEntryNotReady:
        raise
    except Exception as e:
        LOGGER.error("Failed to set up MG SAIC integration: %s", e)
        raise ConfigEntryNotReady(f"Error connecting to SAIC services: {e}") from e


async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Handle options update."""
    coordinator = hass.data[DOMAIN][f"{entry.entry_id}_coordinator"]
    await coordinator.async_update_options(entry.options)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]:
            await async_unload_services(hass)

    return unload_ok
