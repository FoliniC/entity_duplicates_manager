"""Class to perform requests to Tuya Cloud APIs."""

import aiohttp
import asyncio
import hashlib
import hmac
import json
import logging
import time


DEVICES_UPDATE_INTERVAL = 300
DEVICES_UPDATE_INTERVAL_FORCED = 10

TUYA_ENDPOINTS = {
    # Regions code
    "Central Europe Data Center": "eu",
    "China Data Center": "cn",
    "Eastern America Data Center": "ea",
    "India Data Center": "in",
    "Western America Data Center": "us",
    "Western Europe Data Center": "we",
    "Singapore Data Center": "sg",
}


# Signature algorithm.
def calc_sign(msg, key):
    """Calculate signature for request."""
    sign = (
        hmac.new(
            msg=bytes(msg, "latin-1"),
            key=bytes(key, "latin-1"),
            digestmod=hashlib.sha256,
        )
        .hexdigest()
        .upper()
    )
    return sign


class CustomAdapter(logging.LoggerAdapter):
    """Adapter logger for cloud api."""

    def process(self, msg, kwargs):
        return f"[{self.extra.get('prefix', '')}] {msg}", kwargs


class AioHttpSession:
    """
    A class to manage a shared aiohttp.ClientSession.
    Ensures that only one session is created, based on active usage counts.
    """

    _session: aiohttp.ClientSession = None
    _lock = asyncio.Lock()
    _active_requests = 0

    async def __get_session(self):
        """
        Create ClientSession if it doesn't exist yet.
        Increases the active requests to keep track of current session uses.

        Returns: aiohttp.ClientSession
        """
        if self._session is None:
            self._session = aiohttp.ClientSession()
        self._active_requests += 1
        return self._session

    async def __close_session(self):
        """Close session only if this is the last used of session."""
        self._active_requests -= 1

        async with self._lock:
            if self._session and self._active_requests <= 0:
                await self._session.close()
                self._session = None

    async def __aenter__(self):
        return await self.__get_session()

    async def __aexit__(self, exc_type, exc, tb):
        await self.__close_session()


class TuyaCloudApi:
    """Class to send API calls."""

    def __init__(self, region_code, client_id, secret, user_id):
        """Initialize the class."""
        self._logger = CustomAdapter(
            logging.getLogger(__name__), {"prefix": user_id[:3] + "..." + user_id[-3:]}
        )

        self._session = AioHttpSession()
        self._client_id = client_id
        self._secret = secret
        self._user_id = user_id
        self._access_token = ""
        self._token_expire_time: int = 0
        # Serialize token refreshes: concurrent cloud polls must wait for the
        # in-flight refresh instead of signing their request with an empty
        # token (Tuya answers "Error 1010: token invalid").
        self._token_lock = asyncio.Lock()

        if region_code == "ea":
            self._base_url = "https://openapi-ueaz.tuyaus.com"
        elif region_code == "we":
            self._base_url = "https://openapi-weaz.tuyaeu.com"
        elif region_code == "sg":
            self._base_url = "https://openapi-sg.iotbing.com"
        else:
            self._base_url = f"https://openapi.tuya{region_code}.com"

        self.device_list = {}
        self.cached_device_list = {}

        self._last_devices_update = int(time.time())

    def generate_payload(self, method, timestamp, url, headers, body=None, signing_token=None):
        """Generate signed payload for requests."""
        if signing_token is None:
            signing_token = self._access_token
        payload = self._client_id + signing_token + timestamp

        payload += method + "\n"
        # Content-SHA256
        if body is not None:
            body_str = json.dumps(body)
        else:
            body_str = ""
        payload += hashlib.sha256(body_str.encode("utf-8")).hexdigest()
        payload += (
            "\n"
            + "".join(
                [
                    "%s:%s\n" % (key, headers[key])  # Headers
                    for key in headers.get("Signature-Headers", "").split(":")
                    if key in headers
                ]
            )
            + "\n/"
            + url.split("//", 1)[-1].split("/", 1)[-1]  # Url
        )
        # self._logger.debug("PAYLOAD: %s", payload)
        return payload

    async def async_make_request(self, method, url, body=None, headers={}, sign_token=None):
        """Perform requests.

        sign_token: sign the request with this token instead of the currently
        held one. Used with an empty string for the token endpoint itself,
        which Tuya requires to be signed without an access token.
        """
        if sign_token is None:
            # Obtain a valid token before signing. Concurrent callers block on
            # the refresh lock instead of signing with an empty token, which
            # Tuya rejects with "Error 1010: token invalid".
            if not self.token_validate:
                if (res := await self.async_get_access_token()) != "ok":
                    self._logger.warning("Refresh Token failed due to: %s", res)
                    return {
                        "success": False,
                        "code": "TOKEN_REFRESH_FAILED",
                        "msg": str(res),
                        "url": url,
                        "method": method,
                    }
            sign_token = self._access_token

        timestamp = str(int(time.time() * 1000))
        payload = self.generate_payload(
            method, timestamp, url, headers, body, signing_token=sign_token
        )
        default_par = {
            "client_id": self._client_id,
            "access_token": sign_token,
            "sign": calc_sign(payload, self._secret),
            "t": timestamp,
            "sign_method": "HMAC-SHA256",
        }
        full_url = self._base_url + url

        # Log request details
        safe_headers = {k: v for k, v in dict(default_par, **headers).items() if k not in ("access_token", "sign")}
        self._logger.debug("CLOUD API REQ - Method: %s - URL: %s - Headers: %s - Body: %s", method, full_url, safe_headers, body)

        async with self._session as session:
            try:
                if method == "GET":
                    async with session.get(
                        full_url, headers=dict(default_par, **headers)
                    ) as resp:
                        resp_text = await resp.text()
                        self._logger.debug("CLOUD API RESP - Status: %s - Body: %s", resp.status, resp_text)
                        if resp.status >= 400:
                            return {"success": False, "code": resp.status, "msg": f"HTTP {resp.status}: {resp_text}", "url": full_url, "method": method}
                        try:
                            resp_json = await resp.json()
                        except Exception:
                            resp_json = {"success": False, "code": "PARSE_ERROR", "msg": resp_text, "url": full_url, "method": method}
                        # Add debug info to error responses
                        if not resp_json.get("success") and resp_json.get("code") not in (None, "ok"):
                            resp_json["_debug"] = {"url": full_url, "method": method, "payload_base": self._client_id + (self._access_token or "") + timestamp}
                        return resp_json

                if method == "POST":
                    async with session.post(
                        full_url,
                        headers=dict(default_par, **headers, **{"Content-Type": "application/json"}),
                        data=json.dumps(body),
                    ) as resp:
                        resp_text = await resp.text()
                        self._logger.debug("CLOUD API RESP - Status: %s - Body: %s", resp.status, resp_text)
                        if resp.status >= 400:
                            return {"success": False, "code": resp.status, "msg": f"HTTP {resp.status}: {resp_text}", "url": full_url, "method": method}
                        try:
                            resp_json = await resp.json()
                        except Exception:
                            resp_json = {"success": False, "code": "PARSE_ERROR", "msg": resp_text, "url": full_url, "method": method}
                        if not resp_json.get("success") and resp_json.get("code") not in (None, "ok"):
                            resp_json["_debug"] = {"url": full_url, "method": method, "payload_base": self._client_id + (self._access_token or "") + timestamp}
                        return resp_json

                if method == "PUT":
                    async with session.put(
                        full_url,
                        headers=dict(default_par, **headers, **{"Content-Type": "application/json"}),
                        data=json.dumps(body),
                    ) as resp:
                        resp_text = await resp.text()
                        self._logger.debug("CLOUD API RESP - Status: %s - Body: %s", resp.status, resp_text)
                        if resp.status >= 400:
                            return {"success": False, "code": resp.status, "msg": f"HTTP {resp.status}: {resp_text}", "url": full_url, "method": method}
                        try:
                            resp_json = await resp.json()
                        except Exception:
                            resp_json = {"success": False, "code": "PARSE_ERROR", "msg": resp_text, "url": full_url, "method": method}
                        if not resp_json.get("success") and resp_json.get("code") not in (None, "ok"):
                            resp_json["_debug"] = {"url": full_url, "method": method, "payload_base": self._client_id + (self._access_token or "") + timestamp}
                        return resp_json
            except (aiohttp.ClientConnectionError, TimeoutError) as ex:
                self._logger.debug(f"Failed to send request to tuya cloud: {ex}")
                return False

    async def async_get_access_token(self) -> str | None:
        """Obtain a valid access token.

        The refresh is serialized with a lock: concurrent callers wait for the
        in-flight refresh instead of signing their request with an empty
        token. The held token is never cleared while the request is in
        flight, so a cancelled refresh leaves the instance recoverable.
        """
        async with self._token_lock:
            # Another coroutine may have refreshed the token while we waited
            # for the lock.
            if self.token_validate:
                return "ok"

            # The token endpoint must be signed without an access token.
            resp = await self.async_make_request(
                "GET", "/v1.0/token?grant_type=1", sign_token=""
            )

            if not resp:
                # Reset to 0 (expired) rather than -1, so a later request can
                # retry the refresh instead of being blocked forever.
                self._token_expire_time = 0
                self._logger.debug("Failed to retrieve a valid token")
                return "Failed to retrieve a valid token"

            if not resp["success"]:
                self._token_expire_time = 0
                return f"Error {resp['code']}: {resp['msg']}"

            req_results = resp["result"]

            expire_time = int(req_results.get("expire_time", 3600))
            self._access_token = req_results["access_token"]
            self._token_expire_time = int(time.time()) + expire_time
            return "ok"

    async def async_get_devices_list(self, force_update=False) -> str | None:
        """Obtain the list of devices associated to a user. - force_update will ignore last update check."""
        interval = (
            DEVICES_UPDATE_INTERVAL_FORCED if force_update else DEVICES_UPDATE_INTERVAL
        )
        if (
            self.device_list
            and int(time.time()) - (self._last_devices_update + interval) < 0
        ):
            return self._logger.debug(f"Devices has been updated a minutes ago.")

        if not (
            resp := await self.async_make_request(
                "GET", url=f"/v1.0/users/{self._user_id}/devices"
            )
        ):
            return self._logger.debug(f"Failed to retrieve a devices list")

        if not resp["success"]:
            return f"Error {resp['code']}: {resp['msg']}"

        # DEBUG: Log full cloud response
        self._logger.error(f"[CLOUD-DEBUG] Full device list response: {resp['result']}")
        self._logger.error(f"[CLOUD-DEBUG] Number of devices from cloud: {len(resp['result'])}")
        for dev in resp['result']:
            self._logger.error(f"[CLOUD-DEBUG] Device: id={dev.get('id')}, name={dev.get('name')}, online={dev.get('online')}, category={dev.get('category')}, product_id={dev.get('product_id')}, product_name={dev.get('product_name')}")

        self.device_list.update({dev["id"]: dev for dev in resp["result"]})

        self._last_devices_update = int(time.time())
        return "ok"

    async def async_get_devices_dps_query(self):
        """Update All the devices dps_data."""
        # Get Devices DPS Data.
        await asyncio.wait(
            asyncio.create_task(self.async_get_device_functions(devid))
            for devid in self.device_list
        )
        return "ok"

    async def async_get_device_specifications(self, device_id) -> tuple[dict, str]:
        """Obtain the DP ID mappings for a device."""

        if not (
            resp := await self.async_make_request(
                "GET", url=f"/v1.1/devices/{device_id}/specifications"
            )
        ):
            self._logger.debug("Failed to retrieve a device specifications")
            return {}, "Failed to retrieve a device specifications"

        if not resp["success"]:
            return {}, f"Error {resp['code']}: {resp['msg']}"

        return resp["result"], "ok"

    async def async_get_device_query_properties(self, device_id) -> tuple[dict, str]:
        """Obtain the DP ID mappings for a device correctly! Note: This won't works if the subscription expired."""

        if not (
            resp := await self.async_make_request(
                "GET", url=f"/v2.0/cloud/thing/{device_id}/shadow/properties"
            )
        ):
            self._logger.debug("Failed to retrieve a device properties")
            return {}, "Failed to retrieve a device properties"

        if not resp["success"]:
            return {}, f"Error {resp['code']}: {resp['msg']}"

        return resp["result"], "ok"

    async def async_get_device_query_things_data_model(
        self, device_id
    ) -> tuple[dict, str]:
        """Obtain the DP ID mappings for a device."""

        if not (
            resp := await self.async_make_request(
                "GET", url=f"/v2.0/cloud/thing/{device_id}/model"
            )
        ):
            self._logger.debug("Failed to retrieve a device data model")
            return {}, "Failed to retrieve a device data model"

        if not resp["success"]:
            return {}, f"Error {resp['code']}: {resp['msg']}"

        return resp["result"], "ok"

    async def async_get_device_functions(self, device_id, force_update=False) -> dict[str, dict]:
        """Pull Devices Properties and Specifications to devices_list"""
        cached = device_id in self.cached_device_list
        if cached and (dps_data := self.cached_device_list[device_id].get("dps_data")) and not force_update:
            self.device_list[device_id]["dps_data"] = dps_data
            return dps_data

        device_data = {}
        get_data = [
            self.async_get_device_specifications(device_id),
            self.async_get_device_query_properties(device_id),
            self.async_get_device_query_things_data_model(device_id),
        ]
        try:
            specs, query_props, query_model = await asyncio.gather(*get_data)
        except (Exception,) as ex:
            self._logger.debug(f"Failed to get DPS functions for {device_id} - {ex}")
            return

        if query_props[1] == "ok":
            device_data = {
                str(p["dp_id"]): p for p in query_props[0].get("properties") or []
            }
        if specs[1] == "ok":
            for func in specs[0].get("functions", {}):
                if str(func.get("dp_id")) in device_data:
                    device_data[str(func["dp_id"])].update(func)
                elif dp_id := func.get("dp_id"):
                    device_data[str(dp_id)] = func
        if query_model[1] == "ok":
            model_data = json.loads(query_model[0]["model"])
            services = model_data.get("services", [{}])[0]
            properties = services.get("properties")
            for dp_data in properties if properties else {}:
                refactored = {
                    "id": dp_data.get("abilityId"),
                    # "code": dp_data.get("code"),
                    "accessMode": dp_data.get("accessMode"),
                    # values: json.loads later
                    "values": str(dp_data.get("typeSpec")).replace("'", '"'),
                }
                if str(dp_data["abilityId"]) in device_data:
                    device_data[str(dp_data["abilityId"])].update(refactored)
                else:
                    refactored["code"] = dp_data.get("code")
                    device_data[str(dp_data["abilityId"])] = refactored

        if "28841002" in str(query_props[1]):
            # No permissions This affect auto configure feature.
            self.device_list[device_id]["localtuya_note"] = str(query_props[1])

        if device_data:
            self.device_list[device_id]["dps_data"] = device_data
            self.cached_device_list.update({device_id: self.device_list[device_id]})

        return device_data

    async def async_get_device_factory_info(self, device_id) -> dict | None:
        """Get factory info (MAC, SN, UUID) for a device."""
        # Try single device first (works like Tuya GUI)
        for dev_id in [device_id]:
            if not (
                resp := await self.async_make_request(
                    "GET", url=f"/v1.0/iot-03/devices/factory-infos?device_ids={dev_id}"
                )
            ):
                self._logger.debug(f"Failed to get factory info for {dev_id}")
                continue

            if not resp.get("success"):
                # Include debug info in response for UI
                debug_resp = dict(resp)
                debug_resp["_debug"] = {
                    "url": f"/v1.0/iot-03/devices/factory-infos?device_ids={dev_id}",
                    "device_id": dev_id,
                    "code": resp.get("code"),
                    "msg": resp.get("msg"),
                }
                self._logger.debug(f"Failed to get factory info for {dev_id}: {resp}")
                return debug_resp
            ...

        # Fallback: try batch if single fails
        if not (
            resp := await self.async_make_request(
                "GET", url=f"/v1.0/iot-03/devices/factory-infos?device_ids={device_id}"
            )
        ):
            self._logger.debug(f"Failed to get factory info for {device_id}")
            return None

        if not resp.get("success"):
            debug_resp = dict(resp)
            debug_resp["_debug"] = {
                "url": f"/v1.0/iot-03/devices/factory-infos?device_ids={device_id}",
                "device_id": device_id,
                "code": resp.get("code"),
                "msg": resp.get("msg"),
            }
            self._logger.debug(f"Failed to get factory info for {device_id}: {resp}")
            return debug_resp

        result = resp.get("result", [])
        if not result:
            return None

        device_info = result[0]
        return {
            "mac": device_info.get("mac"),
            "sn": device_info.get("sn"),
            "uuid": device_info.get("uuid"),
            "result": result,
        }

    async def async_connect(self):
        """Connect to cloudAPI"""
        if (res := await self.async_get_access_token()) and res != "ok":
            self._logger.warning("Cloud API connection failed: %s", res)
            return "authentication_failed", res
        # Don't require device list - factory info API works independently
        await self.async_get_devices_list()  # Try but don't fail
        self._logger.info("Cloud API connection succeeded.")
        return True, "ok"

    @property
    def token_validate(self):
        """Return whether token is expired or not"""
        cur_time = int(time.time())
        expire_time = self._token_expire_time - 30

        return expire_time >= cur_time

    async def async_get_spaces(self) -> list:
        """Get list of spaces from Tuya Cloud.
        
        Returns:
            list: List of space IDs from Tuya Cloud API
            """
        self._logger.info(f"[CLOUD-API] async_get_spaces: calling /v2.0/cloud/space/child")
        if not (
            resp := await self.async_make_request("GET", "/v2.0/cloud/space/child")
        ):
            self._logger.info(f"[CLOUD-API] async_get_spaces: no response from API")
            return []

        self._logger.info(f"[CLOUD-API] async_get_spaces: raw response: {resp}")

        if not resp.get("success"):
            self._logger.info(f"[CLOUD-API] async_get_spaces failed: {resp.get('code')}: {resp.get('msg')}")
            return []

        # Return the space IDs from the response
        # Response format: {"result": {"data": [{"id": "...", "name": "..."}], "page_size": 200}}
        result_data = resp.get("result", {})
        spaces = result_data.get("data", [])
        self._logger.info(f"[CLOUD-API] async_get_spaces: result_data={result_data}")
        self._logger.info(f"[CLOUD-API] async_get_spaces: spaces={spaces} (type={type(spaces)})")
        
        if isinstance(spaces, list) and spaces and isinstance(spaces[0], dict):
            # API returns objects with id/name, extract IDs
            space_ids = [s.get("id") for s in spaces if s.get("id")]
            self._logger.info(f"[CLOUD-API] async_get_spaces: extracted space IDs: {space_ids}")
            return space_ids
        elif isinstance(spaces, list):
            self._logger.info(f"[CLOUD-API] async_get_spaces: returning spaces as-is: {spaces}")
            return spaces
        
        self._logger.info(f"[CLOUD-API] async_get_spaces: unexpected format, returning empty list")
        return []

    async def async_get_space_resources(self, space_id) -> list:
        """Get resources for a specific space.
        
        Args:
            space_id: The ID of the space to get resources for
            
        Returns:
            list: List of resource objects from Tuya Cloud API
        """
        if not (
            resp := await self.async_make_request("GET", f"/v2.0/cloud/space/{space_id}/resource")
        ):
            return self._logger.debug(f"Failed to retrieve resources for space {space_id} from Tuya Cloud")

        if not resp["success"]:
            return self._logger.debug(f"Failed to retrieve resources for space {space_id}: {resp.get('code')}: {resp.get('msg')}")

        # Return the resources list from the response
        # Response format: {"result": {"data": [{"res_id": "device_id", "res_type": 0}, ...], "last_row_key": ..., "page_size": 200}}
        result_data = resp.get("result", {})
        resources = result_data.get("data", [])
        self._logger.info(f"[CLOUD-API] async_get_space_resources: result_data={result_data}")
        self._logger.info(f"[CLOUD-API] async_get_space_resources: resources={resources} (type={type(resources)})")
        
        # Transform to include device_id for compatibility with existing code
        for resource in resources:
            if "res_id" in resource:
                resource["device_id"] = resource["res_id"]
                resource["resource_type"] = resource.get("res_type", 0)
        
        self._logger.info(f"[CLOUD-API] async_get_space_resources: transformed resources: {resources}")
        return resources

    async def async_filter_new_devices(self, resources: list) -> list:
        """Filter resources to find new devices that are not already configured.
        
        Args:
            resources: List of resource objects from space API
            
        Returns:
            list: Filtered list of new device resources
        """
        if not resources:
            return []
            
        # Get already configured devices
        configured_devices = self.device_list
        
        # Filter for new devices
        new_devices = []
        for resource in resources:
            # Check if this is a device resource (not a service, etc.)
            if isinstance(resource, dict):
                # Try different possible device ID field names
                device_id = (
                    resource.get("device_id") or 
                    resource.get("id") or 
                    resource.get("deviceId") or
                    resource.get("deviceId")
                )
                
                if device_id and device_id not in configured_devices:
                    # Add space context to the device resource
                    resource["space_id"] = resource.get("space_id", "unknown")
                    resource["_is_new"] = True
                    new_devices.append(resource)
            
        self._logger.debug(f"Filtered {len(resources)} resources to {len(new_devices)} new devices")
        return new_devices

    async def async_get_space_details(self, space_id) -> dict:
        """Get detailed information about a specific space.
        
        Args:
            space_id: The ID of the space to get details for
            
        Returns:
            dict: Space details from Tuya Cloud API
        """
        # Try to get detailed space information
        if not (
            resp := await self.async_make_request("GET", f"/v2.0/cloud/space/{space_id}")
        ):
            return self._logger.debug(f"Failed to get details for space {space_id}")

        if not resp["success"]:
            return self._logger.debug(f"Failed to get details for space {space_id}: {resp.get('code')}: {resp.get('msg')}")

        # Return space details
        space_details = resp.get("result", {})
        self._logger.debug(f"Retrieved details for space {space_id}")
        return space_details
