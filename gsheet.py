"""Mise à jour du Google Sheet de suivi des setups téléchargés."""
import logging
from datetime import datetime, timezone

import gspread

import combos
import config
import google_auth

logger = logging.getLogger(__name__)

LOG_HEADERS = ["Date", "Voiture", "Circuit", "Version", "Class", "Fichier", "Lien Drive", "Demandé par"]
MATRIX_SHEET_NAME = "Matrix"


def _open_spreadsheet():
    return gspread.authorize(google_auth.get_credentials()).open_by_key(config.SHEET_ID)


def _get_log_worksheet(sh):
    ws = sh.sheet1
    if not ws.get_all_values():
        ws.append_row(LOG_HEADERS)
    return ws


def _get_or_create_matrix_sheet(sh):
    """Retourne l'onglet Matrix, le crée et l'initialise avec ❌ si absent.
    Applique le formatage (largeur colonnes + format texte) à chaque appel."""
    car_names = [c["car_drive"] for c in combos.CARS]
    track_names = [t["track_drive"] for t in combos.TRACKS]
    n_cars, n_tracks = len(car_names), len(track_names)

    try:
        ws = sh.worksheet(MATRIX_SHEET_NAME)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(
            title=MATRIX_SHEET_NAME,
            rows=n_tracks + 1,
            cols=n_cars + 1,
        )
        headers = [""] + car_names
        rows = [[name] + ["❌"] * n_cars for name in track_names]
        ws.update([headers] + rows)
        logger.info("Onglet Matrix créé (%d voitures × %d circuits)", n_cars, n_tracks)

    # Largeur des colonnes (150 px) — idempotent
    sh.batch_update({"requests": [{
        "updateDimensionProperties": {
            "range": {
                "sheetId": ws.id,
                "dimension": "COLUMNS",
                "startIndex": 0,
                "endIndex": n_cars + 1,
            },
            "properties": {"pixelSize": 150},
            "fields": "pixelSize",
        }
    }]})

    # Format texte sur tout l'onglet pour éviter l'interprétation en date
    ws.format("A1:Z1000", {"numberFormat": {"type": "TEXT"}})

    return ws


def _update_matrix_cell(ws, car_drive: str, track_drive: str, version: str) -> None:
    car_names = [c["car_drive"] for c in combos.CARS]
    track_names = [t["track_drive"] for t in combos.TRACKS]

    try:
        col = car_names.index(car_drive) + 2    # +1 colonne tracks, +1 base 1
        row = track_names.index(track_drive) + 2  # +1 ligne header, +1 base 1
    except ValueError:
        logger.warning("Combo introuvable dans la matrice : %s / %s", car_drive, track_drive)
        return

    ws.update_cell(row, col, version)
    logger.info("Matrice mise à jour : %s / %s → %s", car_drive, track_drive, version)


def add_entry(
    car_drive: str,
    track_drive: str,
    version: str,
    class_code: str,
    filename: str,
    drive_link: str,
    requested_by: str = "",
) -> None:
    """Ajoute une ligne au log (sheet1) et met à jour la cellule de la matrice."""
    sh = _open_spreadsheet()

    ws_log = _get_log_worksheet(sh)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    ws_log.append_row(
        [now, car_drive, track_drive, version, class_code, filename, drive_link, requested_by],
        value_input_option="USER_ENTERED",
    )
    logger.info("Ligne ajoutée au Sheet: %s / %s", car_drive, track_drive)

    ws_matrix = _get_or_create_matrix_sheet(sh)
    _update_matrix_cell(ws_matrix, car_drive, track_drive, version)


# Test manuel : `python gsheet.py`
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    add_entry(
        car_drive="Corvette Z06 LMGT3",
        track_drive="Le Mans",
        version="1.3.1",
        class_code="LMGT3",
        filename="test.zip",
        drive_link="https://drive.google.com/file/d/test",
        requested_by="test",
    )
    print("Test OK.")
