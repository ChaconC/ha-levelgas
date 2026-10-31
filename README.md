# Levelgas for Home Assistant

[English](README.md) · [Español (México)](README.es-MX.md)

<img src="custom_components/levelgas/brand/icon.png" alt="Levelgas integration tank icon" width="96">

Monitor your Levelgas tanks in Home Assistant with raw and smoothed tank levels,
battery status, and sensor timestamps.

[![Validation](https://github.com/ChaconC/ha-levelgas/actions/workflows/validate.yaml/badge.svg)](https://github.com/ChaconC/ha-levelgas/actions/workflows/validate.yaml)
[![Latest release](https://img.shields.io/github/v/release/ChaconC/ha-levelgas)](https://github.com/ChaconC/ha-levelgas/releases/latest)
[![Home Assistant 2026.10+](https://img.shields.io/badge/Home_Assistant-2026.10%2B-18BCF2?logo=homeassistant&logoColor=white)](https://www.home-assistant.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

[Installation](#installation) · [Setup](#initial-setup) · [Options](#options) ·
[Smoothing](#how-smoothing-works) · [Troubleshooting](#troubleshooting) ·
[Contributing](#contributing)

> [!NOTE]
> This is an unofficial community integration that polls the Levelgas cloud API.
> Changes to that API may require an integration update.

## Features

- **Four sensors per tank:** raw level, smoothed level, battery, and last reading.
- **Smoother trends:** a rolling median reduces isolated sensor spikes.
- **Configurable updates:** choose the polling interval, median window, and timezone.
- **Persistent history:** smoothing survives restarts and integration updates; both level sensors support Home Assistant history and long-term statistics.
- **Session recovery:** expired sessions renew automatically; rejected credentials trigger a Home Assistant repair.
- **No added telemetry:** credentials and sessions are stored in Home Assistant's configuration storage.

<img src="docs/assets/sensors.png" alt="Home Assistant sensors showing tank level, smoothed tank level, last reading, and battery" width="428">

| Sensor | What it shows |
| --- | --- |
| Tank level | Raw percentage reported by Levelgas |
| Tank level smoothed | Rolling median of distinct readings, with a default window of five |
| Battery | Sensor battery percentage |
| Last reading | Sensor timestamp interpreted using the configured timezone |

## Installation

### Requirements

- **Home Assistant 2026.10 or later.**
- A Levelgas account with an email, password, and at least one tank.

### Option 1: HACS or Marketplace

[![Open Levelgas in HACS or Marketplace](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=ChaconC&repository=ha-levelgas&category=integration)

1. Open the repository using the button above and add it when prompted.
2. Install **Levelgas**.
3. Restart Home Assistant if requested.
4. Continue with [initial setup](#initial-setup).

<details>
<summary>Add the custom repository manually</summary>

1. Open **HACS → ⋮ → Custom repositories**, or **Settings → Marketplace** on Home Assistant 2026.11+.
2. Add `https://github.com/ChaconC/ha-levelgas` with type **Integration**.
3. Install **Levelgas** and restart Home Assistant if requested.

</details>

### Option 2: Manual installation

1. Download `levelgas.zip` from the [latest release](https://github.com/ChaconC/ha-levelgas/releases/latest).
2. Extract it into `/config/custom_components/levelgas/`.
3. Restart Home Assistant.
4. Continue with [initial setup](#initial-setup).

> [!IMPORTANT]
> `manifest.json` must be directly inside `/config/custom_components/levelgas/`,
> without an extra nested directory.

## Initial setup

[![Set up Levelgas in Home Assistant](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=levelgas)

1. Use the button above, or open **Settings → Devices & services → Add integration → Levelgas**.
2. Enter your Levelgas email and password.
3. Select a tank if your account has more than one. A single tank is selected automatically.
4. Repeat setup to add another tank.

Configuration happens through the Home Assistant UI; no YAML is needed.

## Options

Open the integration's options under **Settings → Devices & services**.

| Option | Default | Accepted values |
| --- | --- | --- |
| Polling interval | 2 hours | 1–24 hours |
| Median window | 5 distinct readings | Odd numbers from 3–31 |
| Sensor timezone | `America/Mexico_City` | A valid timezone name matching the Levelgas app for your tank |

> [!IMPORTANT]
> The API returns timestamps without a UTC offset. Set the sensor timezone to
> the timezone used by the Levelgas app for your tank. Changing it clears the
> smoothing buffer and seeds a new one from the API history.

## How smoothing works

The smoothed level uses a rolling median to limit isolated false drops such as
`69 → 30 → 72`. The raw level remains available for comparison.

- **Recent API history initializes the filter** as soon as the integration starts.
- **Only distinct sensor timestamps count.** Polling the same reading twelve times still adds only one sample.
- **The sample buffer persists** across restarts and integration updates.
- **Sensor attributes expose the sample count, window start, and last sensor time.**

> [!TIP]
> Smoothing also delays a real refill. With a full five-reading window, three
> readings at the new level are needed for that level to become the median.
> Use the raw sensor when checking a refill. The smoothed level is not a
> consumption forecast.

> [!NOTE]
> API history seeds the filter but is **not backfilled into Home Assistant
> Recorder**. Home Assistant starts recording these entities when the integration
> is installed.

### Example dashboard card

Adjust the entity IDs to match your tank:

```yaml
type: history-graph
title: Gas tank trend
hours_to_show: 168
entities:
  - entity: sensor.levelgas_tank_level
    name: Raw
  - entity: sensor.levelgas_tank_level_smoothed
    name: Smoothed
```

## Troubleshooting

| Symptom | Behavior or next step |
| --- | --- |
| Sensors are unavailable | API failures make sensors unavailable. Invalid or missing percentages are never replaced with zero. |
| Credentials are rejected | Open **Settings → System → Repairs** and sign in again to resume updates. Expired sessions are renewed once automatically. |
| Last reading looks old | A successful poll keeps the actual sensor timestamp. The sensor may not have sent a new reading. |
| Reading time is incorrect | Check the sensor timezone in the integration's options. |
| Smoothed level lags after a refill | This is expected for a median filter. Compare the raw level and see [how smoothing works](#how-smoothing-works). |

For other problems, [open an issue](https://github.com/ChaconC/ha-levelgas/issues).

## Contributing

Pull requests run Python lint and formatting checks, tests, integration metadata
validation, an installation archive build, HACS validation, and hassfest.
Dependency installation also checks that `uv.lock` matches `pyproject.toml`.

See the [development guide](CONTRIBUTING.md) for local commands and required PR
checks, the [changelog](CHANGELOG.md) for release notes, and the [MIT license](LICENSE).

## Uninstall

1. Delete each Levelgas entry under **Settings → Devices & services**. This also deletes its stored smoothing buffer.
2. Uninstall **Levelgas** in Marketplace or HACS.
3. Restart Home Assistant if requested.

Existing Recorder history follows Home Assistant's normal retention policy.
