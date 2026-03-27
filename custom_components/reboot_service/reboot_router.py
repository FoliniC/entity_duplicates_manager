# File: /usr/share/hassio/homeassistant/custom_components/reboot_service/reboot_router.py
import requests
import json

# from homeassistant.helpers.config_validation import CONFIG_SCHEMA
import logging
import voluptuous as vol
from homeassistant.helpers import config_validation as cv
from homeassistant.const import CONF_PASSWORD
from bs4 import BeautifulSoup
import time
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from aiohttp import ClientTimeout
from datetime import datetime

_LOGGER = logging.getLogger(__name__)
DOMAIN = "reboot_service"

# Cache globale per evitare chiamate ripetute
_SSID_CACHE = {
    "value": None,
    "timestamp": None,
    "ttl": 25,  # secondi - cache valida per 25 secondi
}

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_PASSWORD): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


# Helper function per matching flessibile degli SSID
def _find_ssid_in_scan(requested_ssid, scan_results, wifi_profiles):
    """
    Trova l'SSID nello scan con matching flessibile.
    Ritorna: (ssid_trovato, dati_network) o (None, None)
    """
    # 1. Matching esatto (case-sensitive)
    if requested_ssid in scan_results:
        _LOGGER.info(f"{DOMAIN} - Exact match found: {requested_ssid}")
        return requested_ssid, scan_results[requested_ssid]

    # 2. Matching case-insensitive
    for ssid_in_scan in scan_results.keys():
        if ssid_in_scan.lower() == requested_ssid.lower():
            _LOGGER.info(
                f"{DOMAIN} - Case-insensitive match: '{requested_ssid}' -> '{ssid_in_scan}'"
            )
            return ssid_in_scan, scan_results[ssid_in_scan]

    # 3. Matching parziale (contiene)
    for ssid_in_scan in scan_results.keys():
        if requested_ssid.lower() in ssid_in_scan.lower():
            _LOGGER.info(
                f"{DOMAIN} - Partial match: '{requested_ssid}' found in '{ssid_in_scan}'"
            )
            return ssid_in_scan, scan_results[ssid_in_scan]

    # 4. Cerca usando il BSSID dal profilo
    if requested_ssid in wifi_profiles:
        profile_bssid = wifi_profiles[requested_ssid].get("bssid", "").lower()
        if profile_bssid:
            for ssid_in_scan, data in scan_results.items():
                scan_bssid = data.get("bssid", "").lower()
                if scan_bssid == profile_bssid:
                    _LOGGER.info(
                        f"{DOMAIN} - BSSID match: '{requested_ssid}' -> '{ssid_in_scan}' (BSSID: {profile_bssid})"
                    )
                    return ssid_in_scan, data

    _LOGGER.warning(f"{DOMAIN} - No match found for '{requested_ssid}' in scan results")
    return None, None


# @CONFIG_SCHEMA
def reboot_router(hass, call):
    try:
        _LOGGER.info(f"{DOMAIN} - reboot_router started")
        # Esegue il codice per riavviare il router
        # _LOGGER.debug("%s # Rebooting router")
        # Creo una sessione di requests
        s = requests.Session()

        # Retrieve configuration from hass.data
        config = hass.data[DOMAIN]
        password = config["password"]
        server = config["server"]
        port = config["port"]
        proxies = {
            # "http": "http://192.168.0.8:8888",
            # "https": "http://192.168.0.8:8888"
        }
        # Recupero il nome del server e la porta dai dati del servizio
        # server = call.data.get("server", "192.168.0.100")
        # port = call.data.get("port", "88")
        _LOGGER.info(f"{DOMAIN} - reboot_router server: {server} ")
        # Imposto l'url per ottenere il cookie della password
        url1 = f"http://{server}:{port}/cgi-bin/get_password_cookie.sh"
        ##config = load_yaml("configuration.yaml")
        ##password = config["reboot_server"]["password"]
        # password = hass.data[DOMAIN]['password']
        _LOGGER.info(f"{DOMAIN} - reboot_router KuWfiAdmin password: {password} ")
        # Imposto la password da passare tramite post
        data = {"password": password}

        # Invio la richiesta post all'url1 con la password
        r1 = s.post(url1, data=data, timeout=10, proxies=proxies)
        _LOGGER.info("reboot_router Richiesta post " + url1)

        # Verifico se la richiesta è andata a buon fine
        if r1.status_code == 200:
            _LOGGER.info("reboot_router Richiesta post riuscita" + r1.text)
            print("Richiesta post riuscita")
            print("contenuto risposta: " + r1.text)
            # cookie_dict = {}
            set_cookie = r1.text
            for cookie in set_cookie.split("Set-Cookie:"):
                if cookie:
                    try:
                        name, value = cookie.split("=", 1)
                        value = value.split(";", 1)[0]
                        # cookie_dict[name] = value
                        _LOGGER.info(
                            "Setting cookie with name: " + name + " value: " + value
                        )
                        s.cookies.set(name, value)
                    except ValueError:
                        _LOGGER.warning(f"{DOMAIN} - Malformed cookie: {cookie}")
        else:
            print("Richiesta post fallita")
            _LOGGER.info("reboot_router Richiesta post fallita")
            return None

        # Imposto l'url per riavviare il sistema
        url2 = f"http://{server}:{port}/cgi-bin/reboot.sh?boot=now"
        # url2 = f"http://{server}:{port}/cgi-bin/reboot.sh"
        _LOGGER.info("reboot_router Richiesta get" + url2)
        # Invio la richiesta get all'url2 con la sessione che contiene il cookie della password
        r2 = s.get(url2, timeout=10, proxies=proxies)

        # Verifico se la richiesta è andata a buon fine
        if r2.status_code == 200:
            _LOGGER.info(
                "reboot_router Richiesta get riuscita" + r2.text + "!" + r2.url
            )
            print("Richiesta get riuscita")
            print("contenuto risposta: " + r2.text)
        else:
            _LOGGER.info("reboot_router Richiesta get fallita")
            print("Richiesta get fallita")
            return None

        # Invalida cache dopo reboot
        _SSID_CACHE["value"] = None
        _SSID_CACHE["timestamp"] = None

        _LOGGER.info(f"{DOMAIN} - reboot_router terminata")
        return None
        # hass.services.register(DOMAIN, "reboot", reboot_router)
        _LOGGER.info(f"{DOMAIN} - reboot_router register 333333333")
    except requests.exceptions.RequestException as e:
        _LOGGER.error(f"{DOMAIN} - Network error during reboot: {str(e)}")
    except KeyError as e:
        _LOGGER.error(f"{DOMAIN} - Missing configuration key: {str(e)}")
    except Exception as e:
        _LOGGER.error(f"{DOMAIN} - Unexpected error in reboot_router: {str(e)}")
    finally:
        # Home Assistant services should return None
        return None


def get_ssid(hass, call):
    """Get the SSID from the router's repeater page."""
    try:
        _LOGGER.info(f"{DOMAIN} - get_ssid started")
        # Create a session
        s = requests.Session()

        # Retrieve configuration from hass.data
        config = hass.data[DOMAIN]
        password = config["password"]
        server = config["server"]
        port = config["port"]

        # Small step: allinea l'autenticazione a change_ssid (browser_time + headers)
        browser_time_value = str(int(time.time()))
        s.cookies.set(name="browser_time", value=browser_time_value, path="/")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Content-type": "application/x-www-form-urlencoded",
            "Origin": f"http://{server}:{port}",
            "Referer": f"http://{server}:{port}/login1.asp",
            "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
        }

        # First authenticate to get the cookie
        url1 = f"http://{server}:{port}/cgi-bin/get_password_cookie.sh"
        # nel sorgente originale a volte viene inviato come stringa "password=..."
        r1 = s.post(url1, headers=headers, data=f"password={password}")
        if r1.status_code != 200:
            _LOGGER.error(f"{DOMAIN} - Authentication failed")
            return None

        # Process cookies
        set_cookie = r1.text
        for cookie in set_cookie.split("Set-Cookie:"):
            if cookie:
                try:
                    name, value = cookie.split("=", 1)
                    value = value.split(";", 1)[0]
                    s.cookies.set(name, value)
                except ValueError:
                    _LOGGER.warning(f"{DOMAIN} - Malformed cookie: {cookie}")

        # Get the repeater page
        url2 = f"http://{server}:{port}/wifirepeater2.asp"
        r2 = s.get(url2, headers=headers)
        if r2.status_code == 200:
            # Parse the HTML to find the SSID input field
            soup = BeautifulSoup(r2.text, "html.parser")
            ssid_input = soup.find("input", {"id": "stassid"})

            if ssid_input and "value" in ssid_input.attrs:
                ssid_value = ssid_input["value"].strip()
                _LOGGER.info(f"{DOMAIN} - Found SSID: {ssid_value}")

                # Update cache
                _SSID_CACHE["value"] = ssid_value
                _SSID_CACHE["timestamp"] = datetime.now()

                # Update the sensor state
                # Small step: mantieni l'API sync del codice originale
                try:
                    hass.states.set("sensor.router_ssid", ssid_value)
                except Exception:
                    # fallback async se disponibile
                    try:
                        hass.states.async_set("sensor.router_ssid", ssid_value)
                    except Exception:
                        pass
                return ssid_value
            else:
                # Migliora logging: SSID atteso, titolo pagina, snippet
                expected_obj = hass.states.get("sensor.router_ssid")
                expected_ssid = expected_obj.state if expected_obj else "unknown"
                title = (
                    soup.title.string.strip()
                    if soup.title and soup.title.string
                    else ""
                )
                snippet = r2.text[:200].replace("\n", " ").strip()
                _LOGGER.error(
                    f"{DOMAIN} - SSID input field not found. Expected current SSID: '{expected_ssid}'. Page title: '{title}'. Snippet: '{snippet}'"
                )
                return None
        else:
            _LOGGER.error(f"{DOMAIN} - Failed to fetch repeater page")
            return None
    except requests.exceptions.RequestException as e:
        _LOGGER.error(f"{DOMAIN} - Network error in get_ssid: {str(e)}")
    except KeyError as e:
        _LOGGER.error(f"{DOMAIN} - Missing configuration key: {str(e)}")
    except Exception as e:
        _LOGGER.error(f"{DOMAIN} - get_ssid failed: {e}")
    finally:
        # Home Assistant services should return None
        return None


def change_ssid(hass, call):
    """Change the router's SSID and password."""
    try:
        _LOGGER.info(f"{DOMAIN} - Starting SSID change")
        s = requests.Session()

        # Retrieve configuration from hass.data
        config = hass.data[DOMAIN]
        password = config["password"]
        server = config["server"]
        port = config["port"]
        wifi_profiles = config["wifi_profiles"]
        _LOGGER.info(f"apscan riuscita {password}! len:{server}")
        proxies = {
            # "http": "http://192.168.0.8:8888",
            # "https": "http://192.168.0.8:8888"
        }
        url1 = f"http://{server}:{port}/cgi-bin/get_password_cookie.sh"
        data = {"password": password}
        browser_time_value = str(int(time.time()))
        s.cookies.set(name="browser_time", value=browser_time_value, path="/")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Content-type": "application/x-www-form-urlencoded",
            "Origin": f"http://{config['server']}:{config['port']}",
            "Referer": f"http://{config['server']}:{config['port']}/login1.asp",
            "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        r1 = s.post(
            url1,
            headers=headers,
            data=f"password={password}",
            timeout=10,
            proxies=proxies,
        )
        # Verifico se la richiesta è andata a buon fine
        if r1.status_code == 200:
            _LOGGER.info(
                "reboot_router Richiesta get_password_cookie riuscita" + r1.text
            )
            set_cookie = r1.text
            # _LOGGER.info("cookie 222!" + r1.text + "!")
            for cookie in set_cookie.split("Set-Cookie:"):
                # _LOGGER.info(f"{DOMAIN} - 111111 cookie - {cookie}")
                if cookie:
                    try:
                        name, value = cookie.split("=", 1)
                        value = value.split(";", 1)[0]
                        # cookie_dict[name] = value
                        # _LOGGER.info("Setting cookie with name: " + name + " value: " + value)
                        # s.cookies.set(name, value)
                        # Check if cookie already exists with same value
                        existing_cookie = s.cookies.get(name)
                        if existing_cookie is None or existing_cookie != value:
                            s.cookies.set(name=name, value=value, path="/")
                            # _LOGGER.info(f"{DOMAIN} - Setting cookie - Name: {name}, Value: {value}")
                        else:
                            _LOGGER.debug(
                                f"{DOMAIN} - Cookie already exists with same value - Name: {name}"
                            )
                    except ValueError:
                        _LOGGER.warning(f"{DOMAIN} - Malformed cookie: {cookie}")
        else:
            _LOGGER.info("reboot_router Richiesta post fallita")
            return None

        # Get requested SSID from service call
        requested_ssid = call.data.get("ssid")
        if not requested_ssid:
            _LOGGER.error(f"{DOMAIN} - No SSID specified in service call")
            return False

        _LOGGER.info(f"{DOMAIN} - SSID change requested to: {requested_ssid}")

        # Gestione speciale per il comando "reboot"
        if requested_ssid == "reboot":
            _LOGGER.info(f"{DOMAIN} - Reboot command received, executing reboot")
            reboot_router(hass, call)
            return True

        boundary = "WebKitFormBoundaryCl5HzRt9gt9Yo1B9"

        _LOGGER.info("apscan riuscita XXXXXXXXXX")
        _LOGGER.info(f" - password {config['password']}")
        change_url = f"http://{server}:{port}/cgi-bin/apscan.sh?dev=wlan1"
        headers = {
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Content-type": "application/x-www-form-urlencoded",
            "Origin": f"http://{config['server']}:{config['port']}",
            "Referer": f"http://{config['server']}:{config['port']}/wifirepeater2.asp",
            "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        response = s.get(change_url, headers=headers, timeout=10, proxies=proxies)

        if response.status_code != 200:
            _LOGGER.error(
                f"{DOMAIN} - apscan failed with status {response.status_code}"
            )
            return False

        _LOGGER.info(f"apscan riuscita {response.text}! len:{len(response.text)}")

        # Send SSID change request
        try:
            apscan_results = json.loads(response.text)
        except json.JSONDecodeError:
            _LOGGER.error(
                f"{DOMAIN} - Could not decode JSON from scan results: {response.text}"
            )
            return False

        if len(response.text) < 5 or not apscan_results:
            _LOGGER.warning("apscan contenuto vuoto -> forzo 'wifi domotica'")
            requested_ssid = "wifi domotica"

        # Verifico se la richiesta è andata a buon fine
        ssid_to_use, network_data = _find_ssid_in_scan(
            requested_ssid, apscan_results, wifi_profiles
        )

        # Se non trovato, fallback a "wifi domotica"
        if not ssid_to_use:
            _LOGGER.warning(
                f"{DOMAIN} - Requested SSID '{requested_ssid}' not found in scan. Available: {list(apscan_results.keys())}"
            )
            _LOGGER.warning(f"{DOMAIN} - Falling back to 'wifi domotica'")
            requested_ssid = "wifi domotica"
            ssid_to_use, network_data = _find_ssid_in_scan(
                requested_ssid, apscan_results, wifi_profiles
            )

            if not ssid_to_use:
                _LOGGER.error(
                    f"{DOMAIN} - Fallback SSID 'wifi domotica' also not found!"
                )
                return False

        # Ottieni il profilo dalla configurazione
        # Usa l'SSID originale richiesto per cercare il profilo, non quello trovato nello scan
        profile = wifi_profiles.get(requested_ssid)
        if not profile:
            _LOGGER.error(
                f"{DOMAIN} - No profile configured for SSID: {requested_ssid}"
            )
            return False

        # Usa i dati dello scan se disponibili, altrimenti usa il profilo
        channel = network_data.get("channel", 6) if network_data else 6
        scanned_bssid = (
            network_data.get("bssid", profile.get("bssid", "00:00:00:00:00:00"))
            if network_data
            else profile.get("bssid", "00:00:00:00:00:00")
        )

        _LOGGER.info(
            f"{DOMAIN} - Final SSID to use: '{ssid_to_use}' (requested: '{requested_ssid}')"
        )
        _LOGGER.info(f"{DOMAIN} - Channel: {channel}, BSSID: {scanned_bssid}")

        # Prepara cookies per la richiesta finale
        s.cookies.clear()
        s.cookies.set("browser_time", browser_time_value)

        for cookie in set_cookie.split("Set-Cookie:"):
            if cookie:
                try:
                    name, value = cookie.split("=", 1)
                    value = value.split(";", 1)[0]
                    existing_cookie = s.cookies.get(name)
                    if existing_cookie is None or existing_cookie != value:
                        s.cookies.set(name=name, value=value, path="/")
                    else:
                        _LOGGER.debug(
                            f"{DOMAIN} - Cookie already exists with same value - Name: {name}"
                        )
                except ValueError:
                    _LOGGER.warning(f"{DOMAIN} - Malformed cookie: {cookie}")

        change_url = (
            f"http://{config['server']}:{config['port']}/cgi-bin/setathrepeater2.sh"
        )

        # Prepare the multipart form data payload
        payload = f"""------{boundary}
Content-Disposition: form-data; name="setrepeater"

1
------{boundary}
Content-Disposition: form-data; name="wwanip"

Connected! Got IP is:192.168.108.181
------{boundary}
Content-Disposition: form-data; name="wwanproto"

dhcp
------{boundary}
Content-Disposition: form-data; name="wwanip"

192.168.0.9
------{boundary}
Content-Disposition: form-data; name="wwannetmask"

255.255.255.0
------{boundary}
Content-Disposition: form-data; name="gateway"


------{boundary}
Content-Disposition: form-data; name="stassid"

{ssid_to_use}
------{boundary}
Content-Disposition: form-data; name="epwd"

{profile["password"]}
------{boundary}
Content-Disposition: form-data; name="essid"

{ssid_to_use}
------{boundary}
Content-Disposition: form-data; name="etype"

psk2+ccmp
------{boundary}
Content-Disposition: form-data; name="channel"

{channel}
------{boundary}
Content-Disposition: form-data; name="bssid"

{scanned_bssid}
------{boundary}
Content-Disposition: form-data; name="radio"

radio1
------{boundary}--
"""

        headers = {
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
            "DNT": "1",
            "Content-Type": f"multipart/form-data; boundary=----{boundary}",
            "Origin": f"http://{config['server']}:{config['port']}",
            "Referer": f"http://{config['server']}:{config['port']}/wifirepeater2.asp",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        # s.cookies.set("browser_time", "1744928083",)
        # s.cookies.set(name="browser_time",
        #    value=str(int(time.time())),
        #   path="/")
        # s.cookies.set("hash", "0A42E24A6C22C4C0BF38CB77D990EE6A0A2F96540BBCC4DFA960626513769A46")
        # s.cookies.set("hash", "507E6B78CC5986C8E9E4180CA803FA5CBA7E7CB81CDCB4AFF3BEF2D55EEFEB87")
        # s.cookies.set("exp", "1744921591")
        # s.cookies.set("exp", "1744932565")
        # _LOGGER.info(f"{DOMAIN} - before " + ' '.join([f"\\x{ord(c):02x}" for c in payload]))
        payload = payload.replace("\n", "\r\n")
        # _LOGGER.info(f"{DOMAIN} - after " + ' '.join([f"\\x{ord(c):02x}" for c in payload]))
        response = s.post(
            change_url, headers=headers, data=payload, timeout=3600, proxies=proxies
        )
        if response.status_code == 200:
            _LOGGER.info(f"{DOMAIN} - Successfully changed SSID to '{ssid_to_use}'")

            # Invalida cache dopo cambio SSID
            _SSID_CACHE["value"] = None
            _SSID_CACHE["timestamp"] = None

            return True
        else:
            _LOGGER.error(
                f"{DOMAIN} - SSID change failed with status {response.status_code}"
            )
            return False
    except requests.exceptions.RequestException as e:
        _LOGGER.error(f"{DOMAIN} - Network error during SSID change: {str(e)}")
        return False
    except Exception as e:
        _LOGGER.error(f"{DOMAIN} - Unexpected error in change_ssid: {str(e)}")
        return False


# Piccolo passo verso l'asincrono: wrapper async che eseguono in executor il codice originale
async def async_reboot_router(hass, call):
    return await hass.async_add_executor_job(reboot_router, hass, call)


async def async_get_ssid(hass, call):
    return await hass.async_add_executor_job(get_ssid, hass, call)


async def async_change_ssid(hass, call):
    return await hass.async_add_executor_job(change_ssid, hass, call)


# Funzione async per il binary sensor - fetch SSID usando aiohttp CON CACHE
async def _async_fetch_ssid(hass, force_refresh=False):
    """Fetch the SSID from the router's repeater page using aiohttp with caching."""

    # Controlla cache se non è un refresh forzato
    if (
        not force_refresh
        and _SSID_CACHE["value"] is not None
        and _SSID_CACHE["timestamp"] is not None
    ):
        elapsed = (datetime.now() - _SSID_CACHE["timestamp"]).total_seconds()
        if elapsed < _SSID_CACHE["ttl"]:
            _LOGGER.debug(
                f"{DOMAIN} - Returning cached SSID: {_SSID_CACHE['value']} (age: {elapsed:.1f}s)"
            )
            return _SSID_CACHE["value"]

    try:
        _LOGGER.debug(f"{DOMAIN} - _async_fetch_ssid started (cache miss or expired)")

        # Retrieve configuration from hass.data
        config = hass.data.get(DOMAIN)
        if not config:
            _LOGGER.error(f"{DOMAIN} - Configuration not found in hass.data")
            return None

        password = config["password"]
        server = config["server"]
        port = config["port"]

        # Get aiohttp session
        session = async_get_clientsession(hass)
        timeout = ClientTimeout(total=10)

        # Set browser_time cookie
        browser_time_value = str(int(time.time()))

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Content-type": "application/x-www-form-urlencoded",
            "Origin": f"http://{server}:{port}",
            "Referer": f"http://{server}:{port}/login1.asp",
            "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cookie": f"browser_time={browser_time_value}",
        }

        # First authenticate to get the cookie
        url1 = f"http://{server}:{port}/cgi-bin/get_password_cookie.sh"

        try:
            async with session.post(
                url1, headers=headers, data=f"password={password}", timeout=timeout
            ) as r1:
                if r1.status != 200:
                    _LOGGER.error(
                        f"{DOMAIN} - Authentication failed with status {r1.status}"
                    )
                    return None

                auth_response = await r1.text()

                # Process cookies from response
                cookies = {}
                for cookie in auth_response.split("Set-Cookie:"):
                    if cookie:
                        try:
                            name, value = cookie.split("=", 1)
                            value = value.split(";", 1)[0]
                            cookies[name] = value
                        except ValueError:
                            pass

                # Build cookie header
                cookie_header = "; ".join([f"{k}={v}" for k, v in cookies.items()])
                if cookie_header:
                    headers["Cookie"] = (
                        f"browser_time={browser_time_value}; {cookie_header}"
                    )

        except Exception as e:
            _LOGGER.error(f"{DOMAIN} - Authentication request failed: {str(e)}")
            return None

        # Get the repeater page
        url2 = f"http://{server}:{port}/wifirepeater2.asp"

        try:
            async with session.get(url2, headers=headers, timeout=timeout) as r2:
                if r2.status == 200:
                    html_content = await r2.text()

                    # Parse the HTML to find the SSID input field
                    soup = BeautifulSoup(html_content, "html.parser")
                    ssid_input = soup.find("input", {"id": "stassid"})

                    if ssid_input and "value" in ssid_input.attrs:
                        ssid_value = ssid_input["value"].strip()

                        # Aggiorna cache
                        _SSID_CACHE["value"] = ssid_value
                        _SSID_CACHE["timestamp"] = datetime.now()

                        _LOGGER.debug(f"{DOMAIN} - Found SSID: {ssid_value} (cached)")
                        return ssid_value
                    else:
                        _LOGGER.debug(
                            f"{DOMAIN} - SSID input field not found in repeater page"
                        )
                        return None
                else:
                    _LOGGER.error(
                        f"{DOMAIN} - Failed to fetch repeater page with status {r2.status}"
                    )
                    return None

        except Exception as e:
            _LOGGER.error(f"{DOMAIN} - Failed to fetch repeater page: {str(e)}")
            return None

    except KeyError as e:
        _LOGGER.error(
            f"{DOMAIN} - Missing configuration key in _async_fetch_ssid: {str(e)}"
        )
        return None
    except Exception as e:
        _LOGGER.error(f"{DOMAIN} - Unexpected error in _async_fetch_ssid: {str(e)}")
        return None
