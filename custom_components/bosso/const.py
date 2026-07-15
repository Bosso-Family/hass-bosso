# """Constants for the Smart Lighting integration."""
# from __future__ import annotations

# DOMAIN = "smart_lighting"

# # Bosso API base URL.
# # Production:
# API_BASE = "https://be.bosso.biz/api/v1"
# # Staging (for local testing — comment out the line above and uncomment this):
# # API_BASE = "https://staging.be.bosso.biz/api/v1"

# # Auth endpoints — TODO confirm exact paths with backend team
# LOGIN_PATH = "/auth/login/"
# REFRESH_PATH = "/auth/token/refresh/"

# # Device endpoints
# DEVICES_PATH = "/controller/device/"
# DEVICE_STATE_PATH = "/controller/device/{device_id}/state/"
# APPLY_TO_HOME_PATH = "/controller/apply-to-home/"

# # Metainfo endpoints
# EFFECTS_PATH = "/metainfo/effects/"

# # Preset endpoints
# PRESETS_LIST_PATH = "/preset/name-id/"
# PRESET_DETAIL_PATH = "/preset/{preset_id}/"
# DEVICE_CONFIG_PATH = "/controller/device/{device_id}/config/"

# # Special "no preset selected" sentinel for the select entities
# PRESET_NONE_LABEL = "None"

# # Special effect ID meaning "no effect / solid color"
# EFFECT_ID_SOLID = 0
# EFFECT_NAME_SOLID = "Solid"

# # Polling interval — how often we re-fetch device state from cloud.
# SCAN_INTERVAL_SECONDS = 30

# # Bosso brightness range matches HA exactly (0-255), so no conversion needed.

# # CCT mapping: Bosso `cct` is 0-255, HA uses Kelvin.
# # TODO: Confirm with hardware team. Assuming 0 = warmest, 255 = coolest.
# CCT_MIN_KELVIN = 2700  # cct=0
# CCT_MAX_KELVIN = 6500  # cct=255

# # Config entry data keys
# CONF_ACCESS_TOKEN = "access_token"
# CONF_REFRESH_TOKEN = "refresh_token"
# # Note: We use Home Assistant's built-in CONF_EMAIL constant for the email field.


"""Constants for the Bosso Lights integration."""
from __future__ import annotations


DOMAIN = "bosso"

# Bosso API base URLs.
# v1 — auth, effects, and fallback for device/preset endpoints
#API_BASE = "https://staging.be.bosso.biz/api/v1"
API_BASE = "https://be.bosso.biz/api/v1"
# v2 — primary for device and preset endpoints
API_BASE_V2 = "https://be.bosso.biz/api/v2"
#API_BASE_V2 = "https://staging.be.bosso.biz/api/v2"


# Auth endpoints — TODO confirm exact paths with backend team
LOGIN_PATH = "/auth/login/"
REFRESH_PATH = "/auth/token/refresh/"

# Device endpoints
DEVICES_PATH = "/controller/device/"
DEVICE_STATE_PATH = "/controller/device/{device_id}/state/"
APPLY_TO_HOME_PATH = "/controller/apply-to-home/"

# Metainfo endpoints
EFFECTS_PATH = "/metainfo/effects/"

# Preset endpoints
PRESETS_LIST_PATH = "/preset/name-id/"
PRESET_DETAIL_PATH = "/preset/{preset_id}/"
DEVICE_CONFIG_PATH = "/controller/device/{device_id}/config/"

# Special "no preset selected" sentinel for the select entities
PRESET_NONE_LABEL = "None"

# Special effect ID meaning "no effect / solid color"
EFFECT_ID_SOLID = 0
EFFECT_NAME_SOLID = "Solid"

# Polling interval — how often we re-fetch device state from cloud.
SCAN_INTERVAL_SECONDS = 30

# Bosso brightness range matches HA exactly (0-255), so no conversion needed.

# CCT mapping: Bosso `cct` is 0-255, HA uses Kelvin.
# TODO: Confirm with hardware team. Assuming 0 = warmest, 255 = coolest.
CCT_MIN_KELVIN = 2700  # cct=0
CCT_MAX_KELVIN = 6500  # cct=255

# Config entry data keys
CONF_ACCESS_TOKEN = "access_token"
CONF_REFRESH_TOKEN = "refresh_token"
# Note: We use Home Assistant's built-in CONF_EMAIL constant for the email field.
