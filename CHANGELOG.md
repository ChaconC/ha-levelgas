# Changelog

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
