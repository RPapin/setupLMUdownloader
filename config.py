"""Chargement centralisé de la configuration depuis les variables d'environnement."""
import os
from pathlib import Path

from dotenv import load_dotenv

# Charge le .env situé à côté de ce fichier
load_dotenv(Path(__file__).parent / ".env", encoding="utf-8")

# --- Discord ---
DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
DISCORD_GUILD_ID = os.environ.get("DISCORD_GUILD_ID")  # optionnel

# --- hymosetups (compte payant) ---
HYMO_USER = os.environ["HYMO_USER"]
HYMO_PASS = os.environ["HYMO_PASS"]
HYMO_BASE_URL = "https://www.hymosetups.com"
HYMO_SETUP_URL = HYMO_BASE_URL + "/setups/le-mans-ultimate"

# --- Google ---
GOOGLE_CREDENTIALS_PATH = os.environ.get("GOOGLE_CREDENTIALS_PATH", "credentials.json")
DRIVE_FOLDER_ID = os.environ["DRIVE_FOLDER_ID"]
SHEET_ID = os.environ["SHEET_ID"]

# --- Chemins de travail ---
BASE_DIR = Path(__file__).parent
DOWNLOAD_DIR = BASE_DIR / "downloads"          # fichiers téléchargés (temporaire)
AUTH_STATE_PATH = BASE_DIR / "auth_state.json"  # session Playwright persistée

DOWNLOAD_DIR.mkdir(exist_ok=True)

HEADLESS = os.environ["HEADLESS"].lower() == "true"