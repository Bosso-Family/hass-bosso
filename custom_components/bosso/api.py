# """API client for the Bosso cloud.

# Handles:
# - Username/password login (returns access + refresh tokens)
# - Automatic token refresh on 401
# - Device discovery (with pagination)
# - Device on/off and brightness via PATCH /controller/device/{id}/state/
# - Color/CCT via POST /controller/apply-to-home/
# """
# from __future__ import annotations

# import asyncio
# import logging
# from typing import Any

# import aiohttp
# from aiohttp import ClientError, ClientResponseError, ClientSession, ClientTimeout

# from .const import (
#     API_BASE,
#     APPLY_TO_HOME_PATH,
#     DEVICE_CONFIG_PATH,
#     DEVICE_STATE_PATH,
#     DEVICES_PATH,
#     EFFECTS_PATH,
#     LOGIN_PATH,
#     PRESET_DETAIL_PATH,
#     PRESETS_LIST_PATH,
#     REFRESH_PATH,
# )

# _LOGGER = logging.getLogger(__name__)

# # Per-request timeout. The Bosso cloud should respond well under this.
# # If a request hangs longer, fail fast so HA isn't stuck in setup forever.
# REQUEST_TIMEOUT = ClientTimeout(total=15, connect=5)


# class BossoAuthError(Exception):
#     """Raised when login or refresh fails permanently (user must re-auth)."""


# class BossoApiError(Exception):
#     """Raised on API errors that aren't auth-related (network, 5xx, etc.)."""


# class BossoApiClient:
#     """Async client for the Bosso REST API."""

#     def __init__(
#         self,
#         session: ClientSession,
#         access_token: str | None = None,
#         refresh_token: str | None = None,
#     ) -> None:
#         """Initialize the client."""
#         self._session = session
#         self._access_token = access_token
#         self._refresh_token = refresh_token
#         # Callback to persist tokens whenever they change.
#         self.on_tokens_updated = None

#     @property
#     def access_token(self) -> str | None:
#         return self._access_token

#     @property
#     def refresh_token(self) -> str | None:
#         return self._refresh_token

#     # ------------------------------------------------------------------ Auth
#     async def async_login(self, email: str, password: str) -> None:
#         """Log in with email/password — used during config flow.

#         Bosso backend expects the field to be called `email`, not `username`.

#         Raises:
#             BossoAuthError: invalid credentials.
#             BossoApiError: network failure, timeout, or unexpected response.
#         """
#         url = f"{API_BASE}{LOGIN_PATH}"
#         try:
#             async with self._session.post(
#                 url,
#                 json={"email": email, "password": password},
#                 headers={"Accept": "application/json"},
#                 timeout=REQUEST_TIMEOUT,
#             ) as resp:
#                 if resp.status in (400, 401, 403):
#                     raise BossoAuthError(f"Login failed: {resp.status}")
#                 if not resp.ok:
#                     body = await resp.text()
#                     raise BossoApiError(
#                         f"Login error {resp.status}: {body[:200]}"
#                     )
#                 data = await resp.json()
#         except asyncio.TimeoutError as err:
#             raise BossoApiError(f"Login timed out after {REQUEST_TIMEOUT.total}s") from err
#         except ClientResponseError as err:
#             raise BossoApiError(f"Login HTTP error: {err}") from err
#         except ClientError as err:
#             raise BossoApiError(f"Login network error: {err}") from err

#         if "access" not in data or "refresh" not in data:
#             raise BossoApiError(f"Unexpected login response shape: {list(data.keys())}")

#         self._access_token = data["access"]
#         self._refresh_token = data["refresh"]
#         self._notify_tokens_updated()

#     async def _async_refresh(self) -> None:
#         """Use the refresh token to get a new access token.

#         Raises:
#             BossoAuthError: refresh token is invalid/expired (user must re-auth).
#             BossoApiError: transient network failure.
#         """
#         if not self._refresh_token:
#             raise BossoAuthError("No refresh token available")

#         url = f"{API_BASE}{REFRESH_PATH}"
#         try:
#             async with self._session.post(
#                 url,
#                 json={"refresh": self._refresh_token},
#                 headers={"Accept": "application/json"},
#                 timeout=REQUEST_TIMEOUT,
#             ) as resp:
#                 if resp.status in (400, 401, 403):
#                     raise BossoAuthError(f"Refresh failed: {resp.status}")
#                 if not resp.ok:
#                     body = await resp.text()
#                     raise BossoApiError(
#                         f"Refresh error {resp.status}: {body[:200]}"
#                     )
#                 data = await resp.json()
#         except asyncio.TimeoutError as err:
#             raise BossoApiError(f"Refresh timed out after {REQUEST_TIMEOUT.total}s") from err
#         except ClientResponseError as err:
#             raise BossoApiError(f"Refresh HTTP error: {err}") from err
#         except ClientError as err:
#             raise BossoApiError(f"Refresh network error: {err}") from err

#         self._access_token = data["access"]
#         if "refresh" in data:
#             self._refresh_token = data["refresh"]
#         self._notify_tokens_updated()
#         _LOGGER.debug("Bosso access token refreshed")

#     def _notify_tokens_updated(self) -> None:
#         if self.on_tokens_updated:
#             self.on_tokens_updated(self._access_token, self._refresh_token)

#     # --------------------------------------------------------- Core request
#     async def _request(
#         self,
#         method: str,
#         path: str,
#         *,
#         json_body: dict[str, Any] | None = None,
#         params: dict[str, Any] | None = None,
#         _retry: bool = True,
#     ) -> Any:
#         """Make an authenticated request, refreshing the token on 401.

#         Raises:
#             BossoAuthError: 401 after refresh attempt, or 403.
#             BossoApiError: network failure, timeout, 5xx, etc.
#         """
#         if not self._access_token:
#             raise BossoAuthError("Not authenticated")

#         url = f"{API_BASE}{path}"
#         headers = {
#             "Accept": "application/json",
#             "Authorization": f"Bearer {self._access_token}",
#         }
#         if json_body is not None:
#             headers["Content-Type"] = "application/json"

#         # NOTE: don't log Authorization header — it contains the bearer token.
#         _LOGGER.debug("Bosso %s %s body=%s", method, url, json_body)
#         try:
#             async with self._session.request(
#                 method,
#                 url,
#                 headers=headers,
#                 json=json_body,
#                 params=params,
#                 timeout=REQUEST_TIMEOUT,
#             ) as resp:
#                 if resp.status == 401 and _retry:
#                     _LOGGER.debug("Got 401 — refreshing token and retrying")
#                     await self._async_refresh()
#                     return await self._request(
#                         method,
#                         path,
#                         json_body=json_body,
#                         params=params,
#                         _retry=False,
#                     )

#                 if resp.status in (401, 403):
#                     raise BossoAuthError(
#                         f"Auth error on {method} {path}: {resp.status}"
#                     )

#                 if not resp.ok:
#                     body = await resp.text()
#                     raise BossoApiError(
#                         f"API error {resp.status} on {method} {path}: {body[:200]}"
#                     )

#                 if resp.status == 204:
#                     return None
#                 return await resp.json()
#         except asyncio.TimeoutError as err:
#             raise BossoApiError(
#                 f"Request timed out: {method} {path}"
#             ) from err
#         except ClientResponseError as err:
#             raise BossoApiError(
#                 f"HTTP error on {method} {path}: {err}"
#             ) from err
#         except ClientError as err:
#             raise BossoApiError(
#                 f"Network error on {method} {path}: {err}"
#             ) from err

#     # ----------------------------------------------------- Device endpoints
#     async def async_list_devices(self) -> list[dict[str, Any]]:
#         """List all devices, paginating through all pages."""
#         devices: list[dict[str, Any]] = []
#         page = 1
#         while True:
#             data = await self._request(
#                 "GET", DEVICES_PATH, params={"page": page}
#             )
#             devices.extend(data.get("results", []))
#             if page >= data.get("total_pages", 1):
#                 break
#             page += 1
#         _LOGGER.debug("Fetched %d Bosso devices", len(devices))
#         return devices

#     async def async_set_device_state(
#         self, device_id: int, state: dict[str, Any]
#     ) -> dict[str, Any] | None:
#         """PATCH device state (on/off, brightness)."""
#         path = DEVICE_STATE_PATH.format(device_id=device_id)
#         return await self._request("PATCH", path, json_body=state)

#     async def async_apply_to_home(
#         self, payload: dict[str, Any]
#     ) -> dict[str, Any] | None:
#         """POST to apply-to-home for color/CCT changes."""
#         return await self._request("POST", APPLY_TO_HOME_PATH, json_body=payload)

#     async def async_list_effects(self) -> list[dict[str, Any]]:
#         """Fetch the catalog of available lighting effects."""
#         effects: list[dict[str, Any]] = []
#         page = 1
#         while True:
#             data = await self._request(
#                 "GET", EFFECTS_PATH, params={"page": page}
#             )
#             effects.extend(data.get("results", []))
#             if page >= data.get("total_pages", 1):
#                 break
#             page += 1
#         _LOGGER.debug("Fetched %d Bosso effects", len(effects))
#         return effects

#     async def async_list_presets(
#         self, predefined: bool
#     ) -> list[dict[str, Any]]:
#         """Fetch the catalog of presets (paginated).

#         Args:
#             predefined: True for built-in presets, False for user-defined.
#         """
#         presets: list[dict[str, Any]] = []
#         page = 1
#         predefined_str = "true" if predefined else "false"
#         while True:
#             data = await self._request(
#                 "GET",
#                 PRESETS_LIST_PATH,
#                 params={"predefined": predefined_str, "page": page},
#             )
#             presets.extend(data.get("results", []))
#             if page >= data.get("total_pages", 1):
#                 break
#             page += 1
#         _LOGGER.debug(
#             "Fetched %d Bosso %s presets",
#             len(presets),
#             "predefined" if predefined else "user-defined",
#         )
#         return presets

#     async def async_get_preset(self, preset_id: int) -> dict[str, Any]:
#         """Fetch the full data for one preset."""
#         path = PRESET_DETAIL_PATH.format(preset_id=preset_id)
#         return await self._request("GET", path)

#     async def async_get_device_config(self, device_id: int) -> dict[str, Any]:
#         """Fetch the device's hardware config (LED counts per channel)."""
#         path = DEVICE_CONFIG_PATH.format(device_id=device_id)
#         return await self._request("GET", path)




"""API client for the Bosso cloud.

Handles:
- Username/password login (returns access + refresh tokens)
- Automatic token refresh on 401
- Device discovery (with pagination)
- Device on/off and brightness via PATCH /controller/device/{id}/state/
- Color/CCT via POST /controller/apply-to-home/

API versioning strategy:
- Auth (/auth/login/, /auth/token/refresh/) → v1 only
- Effects (/metainfo/effects/) → v1 only
- Device endpoints → v2 first, fallback to v1
- Preset endpoints → v2 first, fallback to v1
- Apply-to-home → v2 first (with payload transform), fallback to v1
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp
from aiohttp import ClientError, ClientResponseError, ClientSession, ClientTimeout

from .const import (
    API_BASE,
    API_BASE_V2,
    APPLY_TO_HOME_PATH,
    DEVICE_CONFIG_PATH,
    DEVICE_STATE_PATH,
    DEVICES_PATH,
    EFFECTS_PATH,
    LOGIN_PATH,
    PRESET_DETAIL_PATH,
    PRESETS_LIST_PATH,
    REFRESH_PATH,
)

_LOGGER = logging.getLogger(__name__)

# Per-request timeout. The Bosso cloud should respond well under this.
# If a request hangs longer, fail fast so HA isn't stuck in setup forever.
REQUEST_TIMEOUT = ClientTimeout(total=15, connect=5)


class BossoAuthError(Exception):
    """Raised when login or refresh fails permanently (user must re-auth)."""


class BossoApiError(Exception):
    """Raised on API errors that aren't auth-related (network, 5xx, etc.)."""


class BossoApiClient:
    """Async client for the Bosso REST API."""

    def __init__(
        self,
        session: ClientSession,
        access_token: str | None = None,
        refresh_token: str | None = None,
    ) -> None:
        """Initialize the client."""
        self._session = session
        self._access_token = access_token
        self._refresh_token = refresh_token
        # Callback to persist tokens whenever they change.
        self.on_tokens_updated = None

    @property
    def access_token(self) -> str | None:
        return self._access_token

    @property
    def refresh_token(self) -> str | None:
        return self._refresh_token

    # ------------------------------------------------------------------ Auth
    async def async_login(self, email: str, password: str) -> None:
        """Log in with email/password — used during config flow.

        Bosso backend expects the field to be called `email`, not `username`.

        Raises:
            BossoAuthError: invalid credentials.
            BossoApiError: network failure, timeout, or unexpected response.
        """
        url = f"{API_BASE}{LOGIN_PATH}"
        try:
            async with self._session.post(
                url,
                json={"email": email, "password": password},
                headers={"Accept": "application/json"},
                timeout=REQUEST_TIMEOUT,
            ) as resp:
                if resp.status in (400, 401, 403):
                    raise BossoAuthError(f"Login failed: {resp.status}")
                if not resp.ok:
                    body = await resp.text()
                    raise BossoApiError(
                        f"Login error {resp.status}: {body[:200]}"
                    )
                data = await resp.json()
        except asyncio.TimeoutError as err:
            raise BossoApiError(f"Login timed out after {REQUEST_TIMEOUT.total}s") from err
        except ClientResponseError as err:
            raise BossoApiError(f"Login HTTP error: {err}") from err
        except ClientError as err:
            raise BossoApiError(f"Login network error: {err}") from err

        if "access" not in data or "refresh" not in data:
            raise BossoApiError(f"Unexpected login response shape: {list(data.keys())}")

        self._access_token = data["access"]
        self._refresh_token = data["refresh"]
        self._notify_tokens_updated()

    async def _async_refresh(self) -> None:
        """Use the refresh token to get a new access token.

        Raises:
            BossoAuthError: refresh token is invalid/expired (user must re-auth).
            BossoApiError: transient network failure.
        """
        if not self._refresh_token:
            raise BossoAuthError("No refresh token available")

        url = f"{API_BASE}{REFRESH_PATH}"
        try:
            async with self._session.post(
                url,
                json={"refresh": self._refresh_token},
                headers={"Accept": "application/json"},
                timeout=REQUEST_TIMEOUT,
            ) as resp:
                if resp.status in (400, 401, 403):
                    raise BossoAuthError(f"Refresh failed: {resp.status}")
                if not resp.ok:
                    body = await resp.text()
                    raise BossoApiError(
                        f"Refresh error {resp.status}: {body[:200]}"
                    )
                data = await resp.json()
        except asyncio.TimeoutError as err:
            raise BossoApiError(f"Refresh timed out after {REQUEST_TIMEOUT.total}s") from err
        except ClientResponseError as err:
            raise BossoApiError(f"Refresh HTTP error: {err}") from err
        except ClientError as err:
            raise BossoApiError(f"Refresh network error: {err}") from err

        self._access_token = data["access"]
        if "refresh" in data:
            self._refresh_token = data["refresh"]
        self._notify_tokens_updated()
        _LOGGER.debug("Bosso access token refreshed")

    def _notify_tokens_updated(self) -> None:
        if self.on_tokens_updated:
            self.on_tokens_updated(self._access_token, self._refresh_token)

    # --------------------------------------------------------- Core request
    async def _request(
        self,
        method: str,
        path: str,
        *,
        base_url: str = API_BASE,
        json_body: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        _retry: bool = True,
    ) -> Any:
        """Make an authenticated request, refreshing the token on 401.

        Raises:
            BossoAuthError: 401 after refresh attempt, or 403.
            BossoApiError: network failure, timeout, 5xx, etc.
        """
        if not self._access_token:
            raise BossoAuthError("Not authenticated")

        url = f"{base_url}{path}"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self._access_token}",
        }
        if json_body is not None:
            headers["Content-Type"] = "application/json"

        _LOGGER.debug("Bosso %s %s body=%s", method, url, json_body)
        try:
            async with self._session.request(
                method,
                url,
                headers=headers,
                json=json_body,
                params=params,
                timeout=REQUEST_TIMEOUT,
            ) as resp:
                if resp.status == 401 and _retry:
                    _LOGGER.debug("Got 401 — refreshing token and retrying")
                    await self._async_refresh()
                    return await self._request(
                        method,
                        path,
                        base_url=base_url,
                        json_body=json_body,
                        params=params,
                        _retry=False,
                    )

                if resp.status in (401, 403):
                    raise BossoAuthError(
                        f"Auth error on {method} {path}: {resp.status}"
                    )

                if not resp.ok:
                    body = await resp.text()
                    raise BossoApiError(
                        f"API error {resp.status} on {method} {path}: {body[:200]}"
                    )

                if resp.status == 204:
                    return None
                return await resp.json()
        except asyncio.TimeoutError as err:
            raise BossoApiError(
                f"Request timed out: {method} {path}"
            ) from err
        except ClientResponseError as err:
            raise BossoApiError(
                f"HTTP error on {method} {path}: {err}"
            ) from err
        except ClientError as err:
            raise BossoApiError(
                f"Network error on {method} {path}: {err}"
            ) from err

    async def _request_v2_with_fallback(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Try request on v2 first; if non-200/non-auth error, fallback to v1.

        Auth errors (401/403) are NOT retried on v1 — those mean the token
        is bad, not that the endpoint is missing. Only BossoApiError (4xx
        other than auth, 5xx, timeout, network) triggers the v1 fallback.
        """
        _LOGGER.info(
            "[API-V2] Trying %s %s%s", method, API_BASE_V2, path,
        )
        try:
            result = await self._request(
                method, path, base_url=API_BASE_V2,
                json_body=json_body, params=params,
            )
            _LOGGER.info(
                "[API-V2] ✅ %s %s%s — success", method, API_BASE_V2, path,
            )
            return result
        except BossoAuthError:
            # Auth problem — don't mask it by falling back
            raise
        except BossoApiError as v2_err:
            _LOGGER.warning(
                "[API-V2] ❌ %s %s%s failed: %s",
                method, API_BASE_V2, path, v2_err,
            )
            _LOGGER.info(
                "[API-V1-FALLBACK] Retrying %s %s%s",
                method, API_BASE, path,
            )
            result = await self._request(
                method, path, base_url=API_BASE,
                json_body=json_body, params=params,
            )
            _LOGGER.info(
                "[API-V1-FALLBACK] ✅ %s %s%s — success",
                method, API_BASE, path,
            )
            return result

    # ----------------------------------------------------- Device endpoints
    async def async_list_devices(self) -> list[dict[str, Any]]:
        """List all devices, paginating through all pages. v2 → v1 fallback."""
        devices: list[dict[str, Any]] = []
        page = 1
        while True:
            data = await self._request_v2_with_fallback(
                "GET", DEVICES_PATH, params={"page": page}
            )
            devices.extend(data.get("results", []))
            if page >= data.get("total_pages", 1):
                break
            page += 1
        _LOGGER.debug("Fetched %d Bosso devices", len(devices))
        return devices

    async def async_set_device_state(
        self, device_id: int, state: dict[str, Any]
    ) -> dict[str, Any] | None:
        """PATCH device state (on/off, brightness). v2 → v1 fallback."""
        path = DEVICE_STATE_PATH.format(device_id=device_id)
        return await self._request_v2_with_fallback("PATCH", path, json_body=state)

    async def async_apply_to_home(
        self, payload: dict[str, Any]
    ) -> dict[str, Any] | None:
        """POST to apply-to-home for color/CCT changes.

        v2 payload change: "device" (single dict) → "devices" (list of dicts).
        Also adds "type": "legacy" for v2.
        If v2 fails, falls back to v1 with the original payload format.
        """
        # ---- Build v2 payload: transform "device" → "devices" list ----
        v2_payload = dict(payload)  # shallow copy
        device_obj = v2_payload.pop("device", None)
        if device_obj is not None:
            v2_payload["devices"] = [device_obj]
        # v2 requires "type": "legacy"
        v2_payload["type"] = "legacy"

        _LOGGER.info(
            "[API-V2] Trying POST %s%s with v2 payload (devices list, type=legacy)",
            API_BASE_V2, APPLY_TO_HOME_PATH,
        )
        _LOGGER.debug(
            "[API-V2] apply-to-home v2 payload: %s", v2_payload,
        )
        try:
            result = await self._request(
                "POST", APPLY_TO_HOME_PATH, base_url=API_BASE_V2,
                json_body=v2_payload,
            )
            _LOGGER.info(
                "[API-V2] ✅ POST %s%s apply-to-home — success",
                API_BASE_V2, APPLY_TO_HOME_PATH,
            )
            return result
        except BossoAuthError:
            raise
        except BossoApiError as v2_err:
            _LOGGER.warning(
                "[API-V2] ❌ POST %s%s apply-to-home failed: %s",
                API_BASE_V2, APPLY_TO_HOME_PATH, v2_err,
            )
            _LOGGER.info(
                "[API-V1-FALLBACK] Retrying POST %s%s with v1 payload (single device)",
                API_BASE, APPLY_TO_HOME_PATH,
            )
            _LOGGER.debug(
                "[API-V1-FALLBACK] apply-to-home v1 payload: %s", payload,
            )
            # Fallback: use original v1 payload as-is (with "device", no "type")
            result = await self._request(
                "POST", APPLY_TO_HOME_PATH, base_url=API_BASE,
                json_body=payload,
            )
            _LOGGER.info(
                "[API-V1-FALLBACK] ✅ POST %s%s apply-to-home — success",
                API_BASE, APPLY_TO_HOME_PATH,
            )
            return result

    async def async_list_effects(self) -> list[dict[str, Any]]:
        """Fetch the catalog of available lighting effects. v1 ONLY."""
        _LOGGER.info("[API-V1] GET %s%s (effects — v1 only)", API_BASE, EFFECTS_PATH)
        effects: list[dict[str, Any]] = []
        page = 1
        while True:
            data = await self._request(
                "GET", EFFECTS_PATH, params={"page": page}
            )
            effects.extend(data.get("results", []))
            if page >= data.get("total_pages", 1):
                break
            page += 1
        _LOGGER.info("[API-V1] ✅ Fetched %d effects", len(effects))
        return effects

    async def async_list_presets(
        self, predefined: bool
    ) -> list[dict[str, Any]]:
        """Fetch the catalog of presets (paginated). v2 → v1 fallback.

        Args:
            predefined: True for built-in presets, False for user-defined.
        """
        presets: list[dict[str, Any]] = []
        page = 1
        predefined_str = "true" if predefined else "false"
        while True:
            data = await self._request_v2_with_fallback(
                "GET",
                PRESETS_LIST_PATH,
                params={"predefined": predefined_str, "page": page},
            )
            presets.extend(data.get("results", []))
            if page >= data.get("total_pages", 1):
                break
            page += 1
        _LOGGER.debug(
            "Fetched %d Bosso %s presets",
            len(presets),
            "predefined" if predefined else "user-defined",
        )
        return presets

    async def async_get_preset(self, preset_id: int) -> dict[str, Any]:
        """Fetch the full data for one preset. v2 → v1 fallback."""
        path = PRESET_DETAIL_PATH.format(preset_id=preset_id)
        return await self._request_v2_with_fallback("GET", path)

    async def async_get_device_config(self, device_id: int) -> dict[str, Any]:
        """Fetch the device's hardware config (LED counts per channel). v2 → v1 fallback."""
        path = DEVICE_CONFIG_PATH.format(device_id=device_id)
        return await self._request_v2_with_fallback("GET", path)
