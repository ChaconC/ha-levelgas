"""Check local package metadata before GitHub's HACS and hassfest checks."""

import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = ROOT / "custom_components" / "levelgas"


def validate():
    manifest = json.loads((DOMAIN / "manifest.json").read_text())
    hacs = json.loads((ROOT / "hacs.json").read_text())
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert manifest["domain"] == DOMAIN.name == "levelgas"
    assert manifest["config_flow"] is True
    assert manifest["version"] == project["project"]["version"]
    assert manifest["codeowners"] == ["@ChaconC"]
    assert hacs["homeassistant"] == "2026.10.0"
    assert [
        p.name for p in DOMAIN.parent.iterdir() if p.is_dir() and not p.name.startswith("__")
    ] == ["levelgas"]
    for name in [
        "__init__.py",
        "config_flow.py",
        "sensor.py",
        "translations/en.json",
        "brand/icon.png",
    ]:
        assert (DOMAIN / name).is_file(), name
    english = json.loads((DOMAIN / "translations/en.json").read_text())
    assert set(english["entity"]["sensor"]) == {
        "tank_level",
        "battery",
        "last_reading",
        "tank_level_smoothed",
    }
    for path in DOMAIN.rglob("*.json"):
        json.loads(path.read_text())
    print("Local integration metadata and translations valid.")


if __name__ == "__main__":
    validate()
