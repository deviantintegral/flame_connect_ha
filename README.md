# FlameConnect

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![hacs][hacsbadge]][hacs]
![Project Maintenance][maintenance-shield]

A Home Assistant custom integration for controlling fireplaces via the [Flame Connect](https://github.com/deviantintegral/flameconnect) cloud API.

**Develop in the cloud:** Open it directly in GitHub Codespaces - no local setup required!

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/deviantintegral/flameconnect_ha?quickstart=1)

## Features

- **Full fireplace control**: Power, flame effects, heat, lights, timers, and more
- **Multi-device support**: Each registered fireplace appears as its own device
- **Secure authentication**: Email and password are used once during setup, then only OAuth tokens are stored
- **Manual refresh**: Data refreshes on demand via a button entity (24-hour automatic background refresh keeps tokens alive)
- **RGBW light control**: Media light, overhead light, and log effect with full color support

**This integration sets up the following platforms:**

Platform | Description
-- | --
`switch` | Power, flame effect, pulsating effect, ambient sensor, timer
`climate` | Heat control with temperature and preset modes
`light` | Media light, overhead light, log effect (RGBW)
`select` | Flame color, brightness, media theme
`number` | Flame speed, timer duration, sound volume, sound file
`sensor` | Connection state, software version, error codes (diagnostic, disabled by default)
`button` | Refresh data on demand

## Installation

### HACS (Recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=deviantintegral&repository=flameconnect_ha&category=integration)

1. Click "Download" to install the integration
2. **Restart Home Assistant**

<details>
<summary><b>Manual Installation</b></summary>

1. Download the `custom_components/flameconnect/` folder from this repository
2. Copy it to your Home Assistant's `custom_components/` directory
3. Restart Home Assistant

</details>

## Setup

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=flameconnect)

Or manually:

1. Go to **Settings** > **Devices & Services**
2. Click **"+ Add Integration"**
3. Search for "FlameConnect"
4. Enter your Flame Connect email and password
5. Click Submit

Your credentials are used once to authenticate with the Flame Connect cloud service. Only the resulting OAuth tokens are stored - your email and password are never saved.

## Entities

Each fireplace device exposes the following entities:

### Switches

- **Power** - Main fireplace power (on = manual mode, off = standby)
- **Flame effect** - Toggle flame visual effect
- **Pulsating effect** - Toggle pulsating flame effect
- **Ambient sensor** - Toggle ambient temperature sensor
- **Timer** - Enable/disable the fireplace timer

### Climate

- **Heat** - Temperature control with preset modes (Normal, Boost, Eco, Fan only, Schedule). Only available when heat control is enabled on the fireplace.

### Lights

- **Media light** - RGBW media accent light with theme effects
- **Overhead light** - RGBW overhead light
- **Log effect** - RGBW log effect light

### Selects

- **Flame color** - Choose flame color (Yellow red, Blue, Red, etc.)
- **Brightness** - High or Low
- **Media theme** - Media light theme (White, Blue, Purple, Prism, etc.)

### Numbers

- **Flame speed** - Flame animation speed (1-5)
- **Timer duration** - Timer duration in minutes (1-480)
- **Sound volume** - Sound volume (disabled by default)
- **Sound file** - Sound file selection (disabled by default)

### Sensors (Diagnostic, disabled by default)

- **Connection state** - Fireplace connection status
- **Software version** - UI, control, and relay firmware versions
- **Error codes** - Fireplace error byte values

### Button

- **Refresh data** - Manually refresh all fireplace data from the cloud API

## Data Refresh

The integration automatically refreshes data every 24 hours to keep OAuth tokens alive. For on-demand updates, use the **Refresh data** button entity. Each fireplace has its own refresh button.

## Troubleshooting

### Re-authentication

If your OAuth tokens expire, Home Assistant will display a repair notification. Click through the repair flow to re-enter your credentials and restore connectivity.

### Debug Logging

Add to `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.flameconnect: debug
```

## Contributing

Contributions are welcome! Please open an issue or pull request.

### Development Setup

#### Cloud Development (Recommended)

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/deviantintegral/flameconnect_ha?quickstart=1)

#### Local Development

Requirements: Docker Desktop, VS Code with [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

1. Clone this repository
2. Open in VS Code
3. Click "Reopen in Container" when prompted

### Validation

```bash
script/check   # Type-check + lint + spell
script/test    # Run tests
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Made with care by [@deviantintegral][user_profile]**

---

[commits-shield]: https://img.shields.io/github/commit-activity/y/deviantintegral/flameconnect_ha.svg?style=for-the-badge
[commits]: https://github.com/deviantintegral/flameconnect_ha/commits/main
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/deviantintegral/flameconnect_ha.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40deviantintegral-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/deviantintegral/flameconnect_ha.svg?style=for-the-badge
[releases]: https://github.com/deviantintegral/flameconnect_ha/releases
[user_profile]: https://github.com/deviantintegral
