"""Validate readings and smooth distinct sensor measurements."""

from datetime import datetime, timezone
from statistics import median


def percent(value):
    """Do not turn missing readings into a misleading zero."""
    if type(value) is not int or not 0 <= value <= 100:
        raise ValueError("Invalid sensor percentage")
    return value


def sensor_time(value, tzinfo):
    if not isinstance(value, str):
        raise ValueError("Missing sensor time")
    result = datetime.strptime(value, "%Y-%m-%d %H:%M:%S").replace(tzinfo=tzinfo)
    if result.astimezone(timezone.utc).astimezone(tzinfo).replace(tzinfo=None) != result.replace(
        tzinfo=None
    ):
        raise ValueError("Nonexistent local sensor time")
    return result


def normalize_tank(tank, tzinfo):
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
        "last_reading": sensor_time(tank.get("lastUpdateInfo"), tzinfo),
    }


class Smoother:
    """Rolling median of unique timestamps, with a bounded persistent history."""

    def __init__(self, count, tzinfo, saved=None):
        if type(count) is not int or count < 3 or count > 31 or count % 2 != 1:
            raise ValueError("Smoothing window must be an odd integer from 3 to 31")
        self.count = count
        self.tzinfo = tzinfo
        self.zone = tzinfo.key
        self.tank_hash = None
        self.samples = {}
        if (
            isinstance(saved, dict)
            and saved.get("timezone") == self.zone
            and isinstance(saved.get("tank_hash"), str)
        ):
            self.tank_hash = saved["tank_hash"]
            for point in saved.get("samples", []) if isinstance(saved.get("samples"), list) else []:
                try:
                    date = datetime.fromisoformat(point["date"])
                    if date.tzinfo is not None:
                        self.samples[date.astimezone(timezone.utc)] = percent(point["level"])
                except KeyError, TypeError, ValueError:
                    continue

    def update(self, current, history=None):
        if current["tank_hash"] != self.tank_hash:
            self.samples = {}
            self.tank_hash = current["tank_hash"]
        newest = current["last_reading"].astimezone(timezone.utc)
        for point in history if isinstance(history, list) else []:
            try:
                date = sensor_time(point["date"], self.tzinfo).astimezone(timezone.utc)
                level = percent(point["reading"])
                if date <= newest:
                    self.samples[date] = level
            except KeyError, TypeError, ValueError:
                continue
        self.samples[newest] = current["tank_level"]
        points = sorted(self.samples.items())
        # Report the median as of this reading, even when the API replays an older poll.
        window = [point for point in points if point[0] <= newest][-self.count :]
        self.samples = dict(points[-31:])
        return {
            "tank_level_smoothed": float(median(level for _, level in window)),
            "smoothing_sample_count": len(window),
            "smoothing_window_start": window[0][0].astimezone(self.tzinfo).isoformat(),
        }

    def snapshot(self):
        return {
            "tank_hash": self.tank_hash,
            "timezone": self.zone,
            "samples": [
                {"date": d.astimezone(self.tzinfo).isoformat(), "level": v}
                for d, v in sorted(self.samples.items())
            ],
        }
