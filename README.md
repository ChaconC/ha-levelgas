# Levelgas for Home Assistant

<img src="custom_components/levelgas/brand/icon.png" alt="Levelgas integration tank icon" width="96">

Native integration for Levelgas tank monitors. Connect with your Levelgas email
and password, select a tank, and get four sensors in **Settings → Devices & services**.
The phone is only needed for the original device setup. No MQTT broker or add-on is required.

| Sensor | Value |
| --- | --- |
| Tank level | Raw percentage reported by Levelgas |
| Battery | Sensor battery percentage |
| Last reading | Actual sensor timestamp, with an explicit timezone |
| Tank level smoothed | Rolling median of five distinct readings |

## Install through Marketplace or HACS

Requires **Home Assistant 2026.10 or later** and an email/password Levelgas account.

1. Add `https://github.com/ChaconC/ha-levelgas` as a **custom repository**, type **Integration**.
   On HA 2026.11+, use **Settings → Marketplace**. On HA 2026.10, use **HACS → ⋮ → Custom repositories**.
2. Install **Levelgas** and restart Home Assistant if requested.
3. Open **Settings → Devices & services → Add integration → Levelgas**.
4. Enter your Levelgas credentials. If the account has several tanks, select one.
   Repeat setup to add another tank.

[Open the Levelgas setup flow](https://my.home-assistant.io/redirect/config_flow_start/?domain=levelgas)

The GitHub repository must be published publicly before the custom-repository URL
works. Catalog submission is separate and is not required for custom repositories.

### Manual installation

Extract the release's `levelgas.zip` **into** `/config/custom_components/levelgas/`,
so `manifest.json` is directly inside that directory. Restart HA and add the integration.

## Polling and the smoothed curve

The default poll interval is **two hours**. Configure the interval (1–24 hours),
median window (odd number, 3–31), and sensor timezone in the integration's options.

Levelgas's API supplies recent history, which initializes the median immediately.
Only distinct sensor timestamps count as samples. Polling the same reading twelve
times still counts once. The sample buffer survives restarts and integration
updates. Changing timezone clears the old buffer and seeds it from the API again.

The median limits isolated false drops such as `69 → 30 → 72`. It also delays a
real refill: with a full five-reading window, three readings at the new level are
needed for that level to become the median. The raw level remains available for
comparison. This is a smoothed level, not a consumption forecast.

The smoothed sensor reports its sample count, window start, and last sensor time
as attributes. Both level sensors support HA history and long-term statistics.
The API history seeds the filter; it is **not backfilled into HA Recorder**.
HA starts recording the entities when this integration is installed.

Example dashboard card (adjust entity IDs if HA chose different names):

```yaml
type: history-graph
title: Gas tank trend
hours_to_show: 168
entities:
  - entity: sensor.levelgas_tepepan_tank_level
    name: Raw
  - entity: sensor.levelgas_tepepan_tank_level_smoothed
    name: Smoothed
```

## Timestamp and availability

The API returns a wall-clock timestamp without an offset. Its interpretation is
configurable and defaults to `America/Mexico_City`. Set it to the timezone used by
the Levelgas app for your tank, rather than assuming it is UTC.

API failures mark sensors unavailable. Invalid or missing percentages never become
zero. Expired sessions are renewed once; rejected credentials start HA's
reauthentication flow. An unchanged sensor timestamp is retained, even when a
poll succeeds, so old sensor data is visible as old.

## Privacy and support

This is an independent community integration, not an official Levelgas product.
It uses the HTTPS API observed in Levelgas Android 9.4.1; backend changes may need
an integration update. The shared app identifier in source is not an account
credential. Your account credentials and session stay in HA's configuration
storage. Protect HA backups accordingly. No telemetry is added.

The integration icon is an original generic tank illustration, not the manufacturer's logo.
See [development and publishing](CONTRIBUTING.md), [release notes](CHANGELOG.md),
and [license](LICENSE).

## Remove

Remove the Levelgas entry under Devices & services first; this also removes its
private smoothing buffer. Then uninstall the repository in Marketplace/HACS and
restart HA if requested. Recorder history follows HA's normal retention policy.
