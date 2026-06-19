"""Chargement centralisé de la configuration depuis les variables d'environnement."""
import os
from pathlib import Path

from dotenv import load_dotenv

# BASE_DIR défini en premier car utilisé pour les chemins par défaut ci-dessous
BASE_DIR = Path(__file__).parent
CREDENTIAL_DIR = BASE_DIR / "credentials"

load_dotenv(BASE_DIR / ".env", encoding="utf-8")

# --- Discord ---
DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
DISCORD_GUILD_ID = os.environ.get("DISCORD_GUILD_ID")  # optionnel

# --- hymosetups (compte payant) ---
HYMO_USER = os.environ["HYMO_USER"]
HYMO_PASS = os.environ["HYMO_PASS"]
HYMO_BASE_URL = "https://www.hymosetups.com"
HYMO_SETUP_URL = HYMO_BASE_URL + "/setups/le-mans-ultimate"

# --- TITAN (compte payant) ---
TITAN_USER = os.environ["TITAN_USER"]
TITAN_PASS = os.environ["TITAN_PASS"]
TITAN_BASE_URL = "https://app.tracktitan.io"
TITAN_SETUP_URL = TITAN_BASE_URL + "/setups/leMansUltimate?"

# --- GoSetup (comptes payants — rotation pour économiser les crédits) ---
GOSETUP_BASE_URL = "https://gosetups.gg"
GOSETUP_SETUP_URL = GOSETUP_BASE_URL + "/my-account/downloads/?"
GOSETUP_ACCOUNTS: list[tuple[str, str]] = [
    (os.environ["GOSETUP_USER_1"], os.environ["GOSETUP_PASS_1"]),
]
if os.environ.get("GOSETUP_USER_2") and os.environ.get("GOSETUP_PASS_2"):
    GOSETUP_ACCOUNTS.append((os.environ["GOSETUP_USER_2"], os.environ["GOSETUP_PASS_2"]))
if os.environ.get("GOSETUP_USER_3") and os.environ.get("GOSETUP_PASS_3"):
    GOSETUP_ACCOUNTS.append((os.environ["GOSETUP_USER_3"], os.environ["GOSETUP_PASS_3"]))

# --- Google OAuth2 ---
# client_secrets.json : créer des credentials "Desktop app" dans Google Cloud Console
GOOGLE_CLIENT_SECRETS_PATH = CREDENTIAL_DIR / "client_secret.json"

GOOGLE_TOKEN_PATH = Path(os.environ["GOOGLE_CREDENTIALS_PATH"]) # token-google-rempap.json : généré au 1er `python google_auth.py`, à copier sur la VM ensuite
DRIVE_FOLDER_ID = os.environ["DRIVE_FOLDER_ID"]
SHEET_ID = os.environ["SHEET_ID"]

# --- Chemins de travail ---
DOWNLOAD_DIR = BASE_DIR / "downloads"          # fichiers téléchargés (temporaire)

DOWNLOAD_DIR.mkdir(exist_ok=True)

HEADLESS = os.environ["HEADLESS"].lower() == "true"
