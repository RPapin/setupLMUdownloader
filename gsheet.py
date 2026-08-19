"""Mise à jour du Google Sheet de suivi des setups téléchargés."""
import logging
import re
from datetime import datetime, timezone

import gspread
from gspread.utils import ValueRenderOption

import combos
import config
import google_auth

logger = logging.getLogger(__name__)

LOG_HEADERS = ["Date", "Site", "Voiture", "Circuit", "Version", "Class", "Fichier", "Lien Drive", "Demandé par"]

SITE_MATRIX_NAMES = {
    "hymo": "Matrix Hymo",
    "titan": "Matrix Titan",
    "gosetup": "Matrix GoSetup",
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
    if len(data) < 3:
        return {}

    car_names = data[1][1:]  # row 1 = class header, row 2 = car names
    versions = {}
    for row in data[2:]:
        track_name = row[0]
        for i, cell in enumerate(row[1:]):
            if cell and cell != "❌" and i < len(car_names):
                versions[(car_names[i], track_name)] = cell
    return versions


def get_matrix_links(site: str) -> dict[tuple[str, str], str]:
    """
    Lit la matrice du site et retourne {(car_drive, track_drive): drive_link}
    en parsant les formules =HYPERLINK("url";"version") stockées dans les cellules.
    """
    sh = _open_spreadsheet()
    sheet_name = SITE_MATRIX_NAMES[site]
    try:
        ws = sh.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        return {}

    data = ws.get_all_values(value_render_option=ValueRenderOption.formula)
    if len(data) < 3:
        return {}

    car_names = data[1][1:]  # row 1 = class header, row 2 = car names
    links = {}
    for row in data[2:]:
        track_name = row[0]
        for i, cell in enumerate(row[1:]):
            if cell and cell != "❌" and i < len(car_names):
                match = re.search(r'HYPERLINK\("([^"]+)"', cell)
                if match:
                    links[(car_names[i], track_name)] = match.group(1)
    return links


def _open_spreadsheet():
    return gspread.authorize(google_auth.get_credentials()).open_by_key(config.SHEET_ID)


def _get_log_worksheet(sh):
    ws = sh.sheet1
    if not ws.get_all_values():
        ws.append_row(LOG_HEADERS)
    return ws


def _get_or_create_matrix_sheet(sh, site: str):
    """Retourne l'onglet Matrix du site, le crée/agrandit et l'initialise avec ❌ si besoin."""
    sheet_name = SITE_MATRIX_NAMES[site]
    car_names = [c["car_drive"] for c in combos.CARS]
    track_names = [t["track_drive"] for t in combos.TRACKS]
    n_cars, n_tracks = len(car_names), len(track_names)
    needed_rows, needed_cols = n_tracks + 2, n_cars + 1

    try:
        ws = sh.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=sheet_name, rows=needed_rows, cols=needed_cols)
        existing_cells = {}
        logger.info("Onglet '%s' créé (%d voitures × %d circuits)", sheet_name, n_cars, n_tracks)
    else:
        # Onglet existant : on préserve les cellules déjà remplies (versions/liens),
        # puis on agrandit la grille si combos.py a grossi depuis sa création.
        existing_data = ws.get_all_values(value_render_option=ValueRenderOption.formula)
        existing_cells = {}
        if len(existing_data) >= 3:
            existing_car_names = existing_data[1][1:]
            for row in existing_data[2:]:
                if not row:
                    continue
                track_name = row[0]
                for i, cell in enumerate(row[1:]):
                    if cell and cell != "❌" and i < len(existing_car_names):
                        existing_cells[(existing_car_names[i], track_name)] = cell

        if ws.row_count < needed_rows or ws.col_count < needed_cols:
            ws.resize(rows=max(ws.row_count, needed_rows), cols=max(ws.col_count, needed_cols))
            logger.info(
                "Onglet '%s' agrandi (%d voitures × %d circuits)", sheet_name, n_cars, n_tracks
            )

    # (Re)construit les en-têtes et les lignes de données à partir de combos.py,
    # en réinjectant les cellules déjà remplies (idempotent, sûr pour un onglet existant).
    class_header = [""]
    current_class = None
    for car in combos.CARS:
        if car["class_code"] != current_class:
            class_header.append(car["class_code"])
            current_class = car["class_code"]
        else:
            class_header.append("")

    car_header = [""] + car_names
    data_rows = []
    for track in track_names:
        row = [track]
        for car in car_names:
            row.append(existing_cells.get((car, track), "❌"))
        data_rows.append(row)

    ws.update([class_header, car_header] + data_rows, value_input_option="USER_ENTERED")

    # Merge class header cells across each class group (idempotent)
    merge_requests = []
    class_start_col = None
    current_class = None
    for i, car in enumerate(combos.CARS):
        if car["class_code"] != current_class:
            if current_class is not None:
                end_col = i + 1  # car i is at column i+1 (col 0 = track names)
                if end_col - class_start_col > 1:
                    merge_requests.append({
                        "mergeCells": {
                            "range": {
                                "sheetId": ws.id,
                                "startRowIndex": 0,
                                "endRowIndex": 1,
                                "startColumnIndex": class_start_col,
                                "endColumnIndex": end_col,
                            },
                            "mergeType": "MERGE_ALL",
                        }
                    })
            current_class = car["class_code"]
            class_start_col = i + 1

    # Last class group
    end_col = n_cars + 1
    if current_class is not None and end_col - class_start_col > 1:
        merge_requests.append({
            "mergeCells": {
                "range": {
                    "sheetId": ws.id,
                    "startRowIndex": 0,
                    "endRowIndex": 1,
                    "startColumnIndex": class_start_col,
                    "endColumnIndex": end_col,
                },
                "mergeType": "MERGE_ALL",
            }
        })

    # Clear any stale merges on the header row first (car order/count may have
    # changed since the sheet was created), then reapply the current merges.
    unmerge_request = {
        "unmergeCells": {
            "range": {
                "sheetId": ws.id,
                "startRowIndex": 0,
                "endRowIndex": 1,
                "startColumnIndex": 0,
                "endColumnIndex": ws.col_count,
            }
        }
    }
    requests = [unmerge_request] + merge_requests
    sh.batch_update({"requests": requests})

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
        row = track_names.index(track_drive) + 3  # +3: row1=class, row2=cars, row3+=data
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
