from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR.parent / "site"
PROFILES_DIR = BASE_DIR / "profiles"
LEGACY_PROFILE_PATH = BASE_DIR / "profile.json"
TEMPLATE_PATH = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
ASSETS_DIR = BASE_DIR / "assets"
VALID_PROFILE_ROUTES = ("software", "data-entry", "production")
