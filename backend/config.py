import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DOWNLOADS_DIR = DATA_DIR / "downloads"
CACHE_DIR = DATA_DIR / "cache"
REGISTRY_FILE = DATA_DIR / "registry.json"
STATIC_DIR = BASE_DIR / "static"

DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_SHEETS = [
    {
        "id": "1VUkgSQvxW0803m4nX-LQddoDTIQQCAudk25kAk0Fft4",
        "url": "https://docs.google.com/spreadsheets/d/1VUkgSQvxW0803m4nX-LQddoDTIQQCAudk25kAk0Fft4/edit?usp=sharing",
        "label": "Calling Sheet - September 2026",
    },
    {
        "id": "1-99JfloH45bUZAkLH8jukV099kg-Zx32kFz0nvw8exE",
        "url": "https://docs.google.com/spreadsheets/d/1-99JfloH45bUZAkLH8jukV099kg-Zx32kFz0nvw8exE/edit?usp=sharing",
        "label": "Calling Sheet - Jan 2026",
    }
]

