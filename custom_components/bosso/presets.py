"""Pure helper functions for building preset payloads.

These are kept separate from the rest of the integration so they can be
unit-tested without spinning up Home Assistant. No HA imports here.
"""
from __future__ import annotations

import logging
from typing import Any

_LOGGER = logging.getLogger(__name__)


def calc_led_count(device_config: dict[str, Any]) -> int:
    """Sum the per-channel LED counts. None values count as 0."""
    total = 0
    for key in (
        "data_1_led_count",
        "data_2_led_count",
        "data_3_led_count",
        "data_4_led_count",
    ):
        value = device_config.get(key)
        if value:
            total += value
    return total


def has_valid_i_array(i_array: Any) -> bool:
    """Return True if `i_array` is a non-empty list."""
    return isinstance(i_array, list) and len(i_array) > 0


def resize_i_array(i_array: list[Any], led_count: int) -> list[Any]:
    """Resize an i array to match a target LED count (tile/truncate)."""
    if led_count <= 0:
        return list(i_array)

    original_length = len(i_array)
    if original_length == 0:
        return []

    if led_count == original_length:
        return list(i_array)

    if led_count < original_length:
        return list(i_array[:led_count])

    diff = led_count - original_length
    times = diff // original_length
    remainder = diff % original_length

    extended: list[Any] = []
    for _ in range(times):
        extended.extend(i_array)
    extended.extend(i_array[:remainder])

    return list(i_array) + extended


def get_device_i_array(preset_data: dict[str, Any]) -> Any:
    """Extract the i array from the preset data.

    The API may return the i array in different locations depending
    on the preset type / API version:
      1. v1 — nested under ``device``:   ``preset_data["device"]["i"]``
      2. v2 — nested under ``devices``:  ``preset_data["devices"][0]["i"]``
         (v2 returns a list of device objects)
      3. Fallback — at the top level:    ``preset_data["i"]``

    We check all locations, most specific first.
    """
    # v1 format: "device": {"i": [...]}
    device = preset_data.get("device")
    if isinstance(device, dict):
        nested_i = device.get("i")
        if isinstance(nested_i, list) and len(nested_i) > 0:
            _LOGGER.debug("get_device_i_array: found i-array in v1 'device' key (len=%d)", len(nested_i))
            return nested_i

    # v2 format: "devices": [{"device": 1, "i": [...]}, ...]
    devices = preset_data.get("devices")
    if isinstance(devices, list) and len(devices) > 0:
        first_device = devices[0]
        if isinstance(first_device, dict):
            nested_i = first_device.get("i")
            if isinstance(nested_i, list) and len(nested_i) > 0:
                _LOGGER.debug("get_device_i_array: found i-array in v2 'devices[0]' key (len=%d)", len(nested_i))
                return nested_i

    # Fallback: top-level "i" key
    top_i = preset_data.get("i")
    if isinstance(top_i, list) and len(top_i) > 0:
        _LOGGER.debug("get_device_i_array: found i-array at top-level 'i' key (len=%d)", len(top_i))
    else:
        _LOGGER.debug("get_device_i_array: no i-array found in device/devices/top-level")
    return top_i


def get_zones_i_array(preset_data: dict[str, Any]) -> list[Any]:
    """Concatenate the i arrays from all zones, in list order.

    Zones with no/invalid `i` are skipped. Returns an empty list if no
    zone has a valid `i` array.
    """
    zones = preset_data.get("zones") or []
    combined: list[Any] = []
    for zone in zones:
        zone_i = zone.get("i")
        if has_valid_i_array(zone_i):
            combined.extend(zone_i)
    return combined


def build_preset_apply_payload(
    device_id: int,
    preset_data: dict[str, Any],
    led_count: int,
) -> dict[str, Any]:
    """Build the apply-to-home payload for a preset.

    Three cases:

    Case 1 - preset has a valid device-level i array (device.i):
        Resize it to the device's LED count, send i-based payload.

    Case 2 - device.i is empty/missing, but one or more zones[].i are
        valid: Concatenate all zones' i arrays into a single source
        array, resize to the device's LED count, send as device.i.

    Case 3 - neither device.i nor any zone.i is valid:
        Send the full preset state (color, fx, palette, etc.).
    """
    device_i_array = get_device_i_array(preset_data)

    # ---- Case 1: device-level i array --------------------------------
    source_i_array = device_i_array if has_valid_i_array(device_i_array) else None
    source_label = "device"

    # ---- Case 2: zone-level i arrays (concatenated) --------------------
    if source_i_array is None:
        zones_i_array = get_zones_i_array(preset_data)
        if has_valid_i_array(zones_i_array):
            source_i_array = zones_i_array
            source_label = "zones (concatenated)"

    if source_i_array is not None:
        resized = resize_i_array(source_i_array, led_count)
        _LOGGER.debug(
            "%s i-array resized: original=%d, target=%d, final=%d",
            source_label,
            len(source_i_array),
            led_count,
            len(resized),
        )
        # Include all preset fields alongside the i-array. Some presets
        # have an i-array of empty strings but still rely on fx/col/etc.
        # for the actual look (e.g. "Aquaman" fx=77). Sending everything
        # is safe: for real i-array presets the extra fields are ignored,
        # for effect-with-blank-i presets they're essential.
        return {
            "device": {"device": device_id, "i": resized},
            "fx": preset_data.get("fx"),
            "sx": preset_data.get("sx"),
            "ix": preset_data.get("ix"),
            "pal": preset_data.get("pal"),
            "col": preset_data.get("col"),
            "c1x": preset_data.get("c1x"),
            "c2x": preset_data.get("c2x"),
            "c3x": preset_data.get("c3x"),
            "rev": preset_data.get("rev"),
            "mi": preset_data.get("mi"),
            "is_cct_enabled": True,
            "cct": preset_data.get("cct", 127),
        }

    # ---- Case 3: full preset payload --------------------------------
    return {
        "device": {"device": device_id, "i": []},
        "fx": preset_data.get("fx"),
        "sx": preset_data.get("sx"),
        "ix": preset_data.get("ix"),
        "pal": preset_data.get("pal"),
        "col": preset_data.get("col"),
        "c1x": preset_data.get("c1x"),
        "c2x": preset_data.get("c2x"),
        "c3x": preset_data.get("c3x"),
        "rev": preset_data.get("rev"),
        "mi": preset_data.get("mi"),
        "is_cct_enabled": True,
        "cct": preset_data.get("cct", 127),
    }