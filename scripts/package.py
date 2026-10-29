"""Build a manual-install ZIP using only integration runtime files."""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "custom_components" / "levelgas"


def package():
    destination = ROOT / "dist" / "levelgas.zip"
    destination.parent.mkdir(exist_ok=True)
    with ZipFile(destination, "w", ZIP_DEFLATED) as archive:
        for path in sorted(SOURCE.rglob("*")):
            relative = path.relative_to(SOURCE)
            if (
                path.is_file()
                and path.suffix in {".py", ".json", ".png"}
                and not any(
                    part.startswith(".") or part == "__pycache__" for part in relative.parts
                )
            ):
                archive.write(path, relative)
    print(destination)


if __name__ == "__main__":
    package()
