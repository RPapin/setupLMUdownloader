"""Mise à jour du Google Sheet de suivi des setups téléchargés."""
import logging
from datetime import datetime, timezone

import gspread

import combos
import config
import google_auth

logger = logging.getLogger(__name__)

LOG_HEADERS = ["Date", "Site", "Voiture", "Circuit", "Version", "Class", "Fichier", "Lien Drive", "Demandé par"]

SITE_MATRIX_NAMES = {
    "hymo": "Matrix Hymo",
    "titan": "Matrix Titan",
}


def get_matrix_versions(site: str) -> dict[tuple[str, str], str]:
    """
    Lit la matrice du site et retourne {(car_drive, track_drive): version}
    pour tous les setups déjà téléchargés (cellules non ❌).
    """
    sh = _open_spreadsheet()
    sheet_name = SITE_MATRIX_NAMES[site]
    try:
        ws = sh.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        return {}

    data = ws.get_all_values()
    if len(data) < 2:
        return {}

    car_names = data[0][1:]
    versions = {}
    for row in data[1:]:
        track_name = row[0]
        for i, cell in enumerate(row[1:]):
            if cell and cell != "❌" and i < len(car_names):
                versions[(car_names[i], track_name)] = cell
    return versions


def _open_spreadsheet():
    return gspread.authorize(google_auth.get_credentials()).open_by_key(config.SHEET_ID)


def _get_log_worksheet(sh):
    ws = sh.sheet1
    if not ws.get_all_values():
        ws.append_row(LOG_HEADERS)
    return ws


def _get_or_create_matrix_sheet(sh, site: str):
    """Retourne l'onglet Matrix du site, le crée et l'initialise avec ❌ si absent."""
    sheet_name = SITE_MATRIX_NAMES[site]
    car_names = [c["car_drive"] for c in combos.CARS]
    track_names = [t["track_drive"] for t in combos.TRACKS]
    n_cars, n_tracks = len(car_names), len(track_names)

    try:
        ws = sh.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(
            title=sheet_name,
            rows=n_tracks + 1,
            cols=n_cars + 1,
        )
        headers = [""] + car_names
        rows = [[name] + ["❌"] * n_cars for name in track_names]
        ws.update([headers] + rows)
        logger.info("Onglet '%s' créé (%d voitures × %d circuits)", sheet_name, n_cars, n_tracks)

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

    return ws


def _update_matrix_cell(ws, car_drive: str, track_drive: str, version: str, drive_link: str) -> None:
    car_names = [c["car_drive"] for c in combos.CARS]
    track_names = [t["track_drive"] for t in combos.TRACKS]

    try:
        col = car_names.index(car_drive) + 2
        row = track_names.index(track_drive) + 2
    except ValueError:
        logger.warning("Combo introuvable dans la matrice : %s / %s", car_drive, track_drive)
        return

    cell = gspread.utils.rowcol_to_a1(row, col)
    formula = f'=HYPERLINK("{drive_link}";"{version}")'
    ws.update([[formula]], cell, value_input_option="USER_ENTERED")
    logger.info("Matrice mise à jour : %s / %s → %s", car_drive, track_drive, version)


def add_entry(
    car_drive: str,
    track_drive: str,
    version: str,
    class_code: str,
    filename: str,
    drive_link: str,
    requested_by: str = "",
    site: str = "hymo",
) -> None:
    """Ajoute une ligne au log (sheet1) et met à jour la cellule de la matrice du site."""
    sh = _open_spreadsheet()

    ws_log = _get_log_worksheet(sh)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    ws_log.append_row(
        [now, site, car_drive, track_drive, version, class_code, filename, drive_link, requested_by],
        value_input_option="USER_ENTERED",
    )
    logger.info("Ligne ajoutée au Sheet: %s / %s [%s]", car_drive, track_drive, site)

    ws_matrix = _get_or_create_matrix_sheet(sh, site)
    _update_matrix_cell(ws_matrix, car_drive, track_drive, version, drive_link)


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
        site="hymo",
    )
    print("Test OK.")
