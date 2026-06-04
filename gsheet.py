"""Mise à jour du Google Sheet de suivi des setups téléchargés."""
import logging
from datetime import datetime, timezone

import gspread
from google.oauth2.service_account import Credentials

import config

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]

# En-têtes attendus de la 1re ligne du Sheet
HEADERS = ["Date", "Voiture", "Circuit", "Fichier", "Lien Drive", "Demandé par"]


def _worksheet():
    creds = Credentials.from_service_account_file(
        config.GOOGLE_CREDENTIALS_PATH, scopes=SCOPES
    )
    client = gspread.authorize(creds)
    sh = client.open_by_key(config.SHEET_ID)
    ws = sh.sheet1

    # Crée la ligne d'en-tête si la feuille est vide
    if not ws.get_all_values():
        ws.append_row(HEADERS)
    return ws


def add_entry(car: str, track: str, filename: str, drive_link: str, requested_by: str = "") -> None:
    """Ajoute une ligne au tableau de suivi."""
    ws = _worksheet()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    ws.append_row(
        [now, car, track, filename, drive_link, requested_by],
        value_input_option="USER_ENTERED",
    )
    logger.info("Ligne ajoutée au Sheet: %s / %s", car, track)


# Test manuel : `python gsheet.py`
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    add_entry("Test Car", "Test Track", "test.zip", "https://drive.google.com/...", "test")
    print("Ligne de test ajoutée.")
