# Integration design

`api.py` implements the HTTPS JSON API used by Levelgas Android 9.4.1. Login
returns an account hash and session token. Subsequent requests use HTTP Basic
authentication with that pair and the public app identifier. Tank reads are
read-only. HTTP and application-level failures are checked separately, with one
bounded session-renewal attempt.

`config_flow.py` validates account access, selects a tank by its stable hash, and
rejects duplicate configuration. Reauthentication must retain access to that same
tank. Options configure polling, the smoothing window and timezone.

`coordinator.py` polls once for all four sensors. HA owns the poll scheduler,
availability and retry behavior. Session refresh is persisted in the config entry
without triggering an options reload. The small history buffer uses HA's Store
under `.storage` and is removed when the config entry is removed.

`model.py` validates raw readings and translates wall-clock timestamps using the
configured IANA timezone. Missing values stay invalid instead of becoming zero.
The filter merges the API's recent history with locally observed readings, keys
samples by sensor timestamp, and computes a median over the latest five distinct
readings by default. The bounded buffer contains at most 31 points. A tank or
timezone change resets the buffer before reseeding it.

`sensor.py` exposes three raw sensors and the smoothed level. Percentage sensors
use measurement statistics; the reading timestamp is a timezone-aware datetime.
The timestamp represents the device reading, never the polling time. Historical
points initialize smoothing and are not inserted into Recorder retroactively.

The integration is packaged for HACS/Marketplace as a single
`custom_components/levelgas` directory. It has no MQTT, add-on, phone, or external
runtime requirement. Account credentials, APKs, decompiled code and diagnostic
captures are excluded from Git and distribution archives.
