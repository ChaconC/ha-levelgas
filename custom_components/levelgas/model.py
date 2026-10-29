"""Validate readings and smooth distinct sensor measurements."""

from datetime import datetime, timezone
from statistics import median
from zoneinfo import ZoneInfo


def percent(value):
    """Do not turn missing readings into a misleading zero."""
    if type(value) is not int or not 0 <= value <= 100:
        raise ValueError("Invalid sensor percentage")
    return value


def sensor_time(value, zone):
    if not isinstance(value, str):
        raise ValueError("Missing sensor time")
    result = datetime.strptime(value, "%Y-%m-%d %H:%M:%S").replace(tzinfo=ZoneInfo(zone))
    if result.astimezone(timezone.utc).astimezone(ZoneInfo(zone)).replace(
        tzinfo=None
    ) != result.replace(tzinfo=None):
        raise ValueError("Nonexistent local sensor time")
    return result


def normalize_tank(tank, zone):
    if not isinstance(tank, dict) or tank.get("status") != 1:
        raise ValueError("Tank is not active")
    for field in ("tankHash", "tankName"):
        if not isinstance(tank.get(field), str) or not tank[field]:
            raise ValueError("Missing tank identity")
    return {
        "tank_hash": tank["tankHash"],
        "tank_name": tank["tankName"],
        "tank_level": percent(tank.get("gasLevel")),
        "battery": percent(tank.get("batteryLevel")),
        "last_reading": sensor_time(tank.get("lastUpdateInfo"), zone),
    }


class Smoother:
    """Rolling median of unique timestamps, with a bounded persistent history."""

    def __init__(self, count, zone, saved=None):
        if type(count) is not int or count < 3 or count > 31 or count % 2 != 1:
            raise ValueError("Smoothing window must be an odd integer from 3 to 31")
        ZoneInfo(zone)
        self.count = count
        self.zone = zone
        self.tank_hash = None
        self.samples = {}
        if (
            isinstance(saved, dict)
            and saved.get("timezone") == zone
            and isinstance(saved.get("tank_hash"), str)
        ):
            self.tank_hash = saved["tank_hash"]
            for point in saved.get("samples", []) if isinstance(saved.get("samples"), list) else []:
                try:
                    date = datetime.fromisoformat(point["date"])
                    if date.tzinfo is not None:
                        self.samples[date] = percent(point["level"])
                except KeyError, TypeError, ValueError:
                    continue

    def update(self, current, history=None):
        if current["tank_hash"] != self.tank_hash:
            self.samples = {}
            self.tank_hash = current["tank_hash"]
        newest = current["last_reading"]
        for point in history if isinstance(history, list) else []:
            try:
                date = sensor_time(point["date"], self.zone)
                level = percent(point["reading"])
                if date <= newest:
                    self.samples[date] = level
            except KeyError, TypeError, ValueError:
                continue
        self.samples[newest] = current["tank_level"]
        dates = sorted(d for d in self.samples if d <= newest)[-31:]
        self.samples = {d: self.samples[d] for d in dates}
        window = dates[-self.count :]
        return {
            "tank_level_smoothed": float(median(self.samples[d] for d in window)),
            "smoothing_sample_count": len(window),
            "smoothing_window_start": window[0].isoformat(),
        }

    def snapshot(self):
        return {
            "tank_hash": self.tank_hash,
            "timezone": self.zone,
            "samples": [
                {"date": d.isoformat(), "level": v} for d, v in sorted(self.samples.items())
            ],
        }
