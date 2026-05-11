# Bosso Lights for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/Bosso-Family/hass-bosso.svg)](https://github.com/Bosso-Family/hass-bosso/releases)
[![License](https://img.shields.io/github/license/Bosso-Family/hass-bosso.svg)](LICENSE)

Home Assistant integration for [Bosso](https://bosso.biz) smart lights. Control your devices, change colors, apply effects and presets — all from your Home Assistant dashboard, automations, and voice assistants.

## Features

- **On/off, brightness, RGB color, color temperature** — full control through the standard Home Assistant light card
- **Lighting effects** — pick from your account's effect catalog (Solid, Rainbow, etc.)
- **Predefined presets** — Bosso's built-in mood presets shown as a dropdown
- **User-defined presets** — your custom saved presets, also as a dropdown
- **Multi-device support** — every Bosso device in your account becomes a separate Home Assistant device
- **Cloud sync** — changes from the Bosso app, Google Home, or Home Assistant all stay in sync

## Installation

### Option 1 — HACS (recommended)

This is the preferred way. Updates roll out automatically.

1. Make sure [HACS](https://hacs.xyz) is installed in your Home Assistant.
2. In Home Assistant, go to **HACS → Integrations**.
3. Click the three-dot menu (top-right) → **Custom repositories**.
4. Add this repository: `https://github.com/Bosso-Family/hass-bosso`
5. Category: **Integration**
6. Click **Add**.
7. Find **Bosso Lights** in the HACS integrations list and click **Install**.
8. Restart Home Assistant.

> Once we're listed in the HACS default repositories, step 3-6 won't be needed — you'll just search "Bosso" directly in HACS.

### Option 2 — Manual installation

1. Download the latest release from the [Releases page](https://github.com/Bosso-Family/hass-bosso/releases).
2. Unzip and copy the `custom_components/bosso/` folder into your Home Assistant `config/custom_components/` directory.
3. Restart Home Assistant.

## Setup

After installing the integration:

1. Go to **Settings → Devices & Services**.
2. Click **+ Add Integration** (bottom-right).
3. Search for **"Bosso Lights"** and click it.
4. Enter your Bosso account email and password.
5. Click **Submit**.

Your Bosso devices will appear automatically. Each device gets:

- A `light.<device_name>` entity for on/off, brightness, color, and effects
- A `select.<device_name>_predefined_preset` entity for built-in presets
- A `select.<device_name>_user_preset` entity for your saved presets

## Usage examples

### From the dashboard

Open the device card to see the light controls and preset dropdowns side-by-side.

### From an automation

```yaml
# Turn on the front door lights at sunset
- alias: Front door lights at sunset
  trigger:
    - platform: sun
      event: sunset
  action:
    - service: light.turn_on
      target:
        entity_id: light.front_door_lights
      data:
        brightness: 200
        rgb_color: [255, 200, 100]
```

```yaml
# Apply a "Movie Night" preset when a button is pressed
- alias: Movie night preset
  trigger:
    - platform: state
      entity_id: input_button.movie_night
      to: "pressed"
  action:
    - service: select.select_option
      target:
        entity_id: select.living_room_user_preset
      data:
        option: "Movie Night"
```

### From voice assistants

If you have Google Assistant or Alexa connected to Home Assistant, your Bosso lights are automatically exposed and can be controlled by voice. "Hey Google, turn on the front door lights" works out of the box.

## Troubleshooting

### "Invalid email or password"

Verify your credentials work in the Bosso mobile app first. Note the integration uses your account **email**, not a username.

### "Could not reach Bosso servers"

Check that your Home Assistant has internet access and can reach `be.bosso.biz`. If you're behind a corporate proxy, you may need to configure HA accordingly.

### Devices don't appear after login

Open the Bosso mobile app and confirm your devices are visible there. The integration only sees devices that exist in your Bosso account.

### State updates feel slow

The integration polls the Bosso cloud every 30 seconds for state changes made outside Home Assistant. Changes made *from* Home Assistant update immediately. If you need real-time updates from external sources, consider keeping your dashboard interactions within Home Assistant.

### Enable debug logging

Add this to your `configuration.yaml` and restart:

```yaml
logger:
  default: warning
  logs:
    custom_components.bosso: debug
```

Then check **Settings → System → Logs** when the issue happens.

## Reporting issues

When opening a [GitHub issue](https://github.com/Bosso-Family/hass-bosso/issues), please include:

- Home Assistant version
- Integration version (see `manifest.json`)
- Steps to reproduce
- Relevant debug logs (with email and tokens redacted)

## Privacy

This integration sends the following data to the Bosso cloud:

- Your account email and password (only during initial setup, to obtain access tokens)
- Commands you send to your devices (on/off, brightness, color, etc.)

Your access and refresh tokens are stored locally in your Home Assistant config and are never shared.

For full details, see the [Bosso Privacy Policy](https://bosso.biz/privacy).

## Contributing

Pull requests welcome. For major changes, please open an issue first to discuss what you'd like to change.

## License

[Apache 2.0](LICENSE)

---

This is a third-party integration not officially affiliated with Home Assistant. "Home Assistant" is a trademark of Nabu Casa Inc.
