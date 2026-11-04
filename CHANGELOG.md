# Changelog

## 1.0.3 (2026-11-04)

- Resolve the sensor timezone asynchronously during setup and reuse it for readings and smoothing, avoiding timezone database reads on Home Assistant's event loop.
- Preserve existing smoothing history and timezone-change reseeding behavior.

## 1.0.2 (2026-11-04)

- Declare Mexico as the supported country for HACS and Marketplace catalog submission.

## 1.0.1 (2026-10-31)

First public release.

- Publish the native Levelgas integration with a manual-install ZIP and HACS support.
- Add English and Mexican Spanish setup guides with clearer sensor and smoothing documentation.
- Fix test discovery and require lint, tests, HACS validation, and hassfest before merging.
- Update GitHub Actions dependencies for validation and release packaging.

## 1.0.0 (unreleased)

- Native Levelgas account setup, tank selection and reauthentication.
- Raw tank percentage, battery, reading timestamp and median-smoothed level.
- Two-hour polling by default, with configurable interval and timezone.
- Persistent smoothing history seeded from the API and deduplicated by sensor time.
- HACS and Home Assistant Marketplace custom-repository packaging.
