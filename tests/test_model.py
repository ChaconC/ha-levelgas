from zoneinfo import ZoneInfo

import pytest

from custom_components.levelgas.model import Smoother, normalize_tank

MEXICO_TZ = ZoneInfo("America/Mexico_City")
NEW_YORK_TZ = ZoneInfo("America/New_York")


def tank(day=28, value=69):
    return {
        "tankHash": "abc",
        "tankName": "Tepepan",
        "gasLevel": value,
        "batteryLevel": 70,
        "lastUpdateInfo": f"2026-10-{day} 18:01:24",
        "status": 1,
    }


def test_sensor_time_and_zero_values():
    value = normalize_tank(tank(), MEXICO_TZ)
    assert value["tank_level"] == 69
    assert value["battery"] == 70
    assert value["last_reading"].isoformat() == "2026-10-28T18:01:24-06:00"
    assert normalize_tank(tank(value=0), MEXICO_TZ)["tank_level"] == 0


@pytest.mark.parametrize("bad", [None, -1, 101, "69", True, float("nan")])
def test_bad_levels_are_not_zero(bad):
    with pytest.raises(ValueError):
        normalize_tank(tank(value=bad), MEXICO_TZ)
    with pytest.raises(ValueError):
        normalize_tank({**tank(), "batteryLevel": bad}, MEXICO_TZ)


def test_invalid_timestamp_and_inactive_tank():
    for change in [{"lastUpdateInfo": "2026-02-30 18:01:24"}, {"status": 0}]:
        with pytest.raises(ValueError):
            normalize_tank({**tank(), **change}, MEXICO_TZ)


def test_median_rejects_dip_and_deduplicates_sensor_timestamps():
    s = Smoother(5, MEXICO_TZ)
    current = normalize_tank(tank(), MEXICO_TZ)
    history = [
        {"reading": v, "date": f"2026-10-{d} 18:01:24"}
        for d, v in [(24, 72), (25, 71), (26, 30), (27, 70)]
    ]
    result = s.update(current, history)
    assert result["tank_level_smoothed"] == 70
    assert result["smoothing_sample_count"] == 5
    for _ in range(12):
        assert s.update(current)["tank_level_smoothed"] == 70
    assert len(s.snapshot()["samples"]) == 5


def test_restart_refill_and_tank_isolation():
    s = Smoother(5, MEXICO_TZ)
    for day in range(20, 25):
        s.update(normalize_tank(tank(day, 30), MEXICO_TZ))
    restored = Smoother(5, MEXICO_TZ, s.snapshot())
    for day, expected in [(25, 30), (26, 30), (27, 90)]:
        result = restored.update(normalize_tank(tank(day, 90), MEXICO_TZ))
        assert result["tank_level_smoothed"] == expected
    result = restored.update(normalize_tank({**tank(value=10), "tankHash": "other"}, MEXICO_TZ))
    assert result["tank_level_smoothed"] == 10


def test_invalid_history_and_future_points_ignored():
    s = Smoother(5, MEXICO_TZ, {"corrupt": True})
    result = s.update(
        normalize_tank(tank(), MEXICO_TZ),
        [
            {"reading": None, "date": "2026-10-27 18:01:24"},
            {"reading": 100, "date": "2026-10-29 18:01:24"},
            {"reading": 0, "date": "2026-10-28 18:01:24"},
            {"reading": 30, "date": "invalid"},
        ],
    )
    assert result["tank_level_smoothed"] == 69
    assert result["smoothing_sample_count"] == 1


@pytest.mark.parametrize("count", [0, 2, 4, 33, 5.5, True])
def test_window_validation(count):
    with pytest.raises(ValueError):
        Smoother(count, MEXICO_TZ)


def test_timezone_change_reseeds_history_without_duplicate_measurements():
    s = Smoother(5, MEXICO_TZ)
    for day, value in [(24, 80), (25, 70), (26, 60), (27, 50), (28, 40)]:
        s.update(normalize_tank(tank(day, value), MEXICO_TZ))
    changed = Smoother(5, NEW_YORK_TZ, s.snapshot())
    history = [
        {"date": f"2026-10-{day} 18:01:24", "reading": value}
        for day, value in [(24, 80), (25, 70), (26, 60), (27, 50)]
    ]
    result = changed.update(normalize_tank(tank(28, 40), NEW_YORK_TZ), history)
    assert result["tank_level_smoothed"] == 60
    assert len(changed.snapshot()["samples"]) == 5
