import requests
import logging
from homeassistant.helpers import config_validation as cv

# from homeassistant.util.yaml.loader import load_yaml
import voluptuous as vol
from homeassistant.const import CONF_PASSWORD
from .reboot_router import reboot_router
from .reboot_router import get_ssid
from .reboot_router import change_ssid
import sys

DOMAIN = "reboot_service"

ATTR_NAME = "name"
DEFAULT_NAME = "World"
_LOGGER = logging.getLogger(__name__)


CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Required("server", default="192.168.0.100"): cv.string,
                vol.Required("port", default="88"): cv.string,
                vol.Required("wifi_profiles", default=[]): vol.All(
                    cv.ensure_list,
                    [
                        vol.Schema(
                            {
                                vol.Required("ssid"): cv.string,
                                vol.Required("password"): cv.string,
                                vol.Required("bssid"): cv.string,
                            }
                        )
                    ],
                ),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


def setup(hass, config):
    """Set up is called when Home Assistant is loading our component."""

    try:
        _LOGGER.info(f"{DOMAIN} - reboot_router register 1111111")

        # _LOGGER.error(f"Python Path: {sys.path}")
        # _LOGGER.error(f"Virtual Environment: {sys.prefix}")

        conf = config[DOMAIN]
        password = conf[CONF_PASSWORD]
        server = conf.get("server", "192.168.0.103")
        port = conf.get("port", "88")
        # _LOGGER.info(f"{DOMAIN} - reboot_router password: {password}")
        if not password:
            _LOGGER.error(f"{DOMAIN} - Password is required")
            return False

        # Use the password in your custom component logic
        hass.states.set(f"{DOMAIN}.KuWfiAdmin", password)
        # _LOGGER.info(f"{DOMAIN} - reboot_router KuWfiAdmin password: {password} ")
        # Store the password in hass.data
        hass.data[DOMAIN] = {
            "password": password,
            "server": server,
            "port": port,
            "wifi_profiles": {
                p["ssid"]: {"password": p["password"], "bssid": p["bssid"]}
                for p in conf["wifi_profiles"]
            },
        }

        # hass.services.register(DOMAIN, "reboot", reboot_router)
        hass.services.register(
            DOMAIN, "reboot_router", lambda call: reboot_router(hass, call)
        )
        hass.services.register(DOMAIN, "get_ssid", lambda call: get_ssid(hass, call))
        hass.services.register(
            DOMAIN, "change_ssid", lambda call: change_ssid(hass, call)
        )
        _LOGGER.info(f"{DOMAIN} - Services registered successfully")

        # Return boolean to indicate that initialization was successful.
        return True
    except KeyError as e:
        _LOGGER.error(f"{DOMAIN} - Missing configuration key: {e}")
        return False
    except Exception as e:
        _LOGGER.error(f"{DOMAIN} - Setup failed: {str(e)}", exc_info=True)
        return False
