"""Upload de fichiers vers un dossier Google Drive privé via OAuth2 utilisateur."""
import logging
from pathlib import Path

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

import config
import google_auth

logger = logging.getLogger(__name__)


def _drive_service():
    return build("drive", "v3", credentials=google_auth.get_credentials())


def _get_or_create_folder(service, name: str, parent_id: str) -> str:
    """Retourne l'ID du sous-dossier `name` sous `parent_id`, le crée si absent."""
    query = (
        f"name='{name}' and '{parent_id}' in parents"
        " and mimeType='application/vnd.google-apps.folder'"
        " and trashed=false"
    )
    logger.info("query " + query)
    resp = (
        service.files()
        .list(q=query, fields="files(id)", supportsAllDrives=True, includeItemsFromAllDrives=True)
        .execute()
    )
    files = resp.get("files", [])
    logger.info("files ")
    logger.info(files)
    if files:
        return files[0]["id"]

    folder = (
        service.files()
        .create(
            body={"name": name, "mimeType": "application/vnd.google-apps.folder", "parents": [parent_id]},
            fields="id",
            supportsAllDrives=True,
        )
        .execute()
    )
    logger.info("Dossier Drive créé : %s (id=%s)", name, folder["id"])
    return folder["id"]


def _resolve_path(service, path: str) -> str:
    """
    Résout le chemin `/class_code/car/track` sous DRIVE_FOLDER_ID.
    Crée les sous-dossiers manquants. Retourne l'ID du dossier feuille.
    """
    folder_id = config.DRIVE_FOLDER_ID
    for part in path.split("/"):
        folder_id = _get_or_create_folder(service, part, folder_id)
    return folder_id


def upload_file(local_path: Path, drive_path: str) -> dict:
    """
    Upload `local_path` dans le sous-dossier Drive `drive_path` (format
    "class_code/car/track"). Les dossiers intermédiaires sont créés si besoin.

    Retourne un dict avec id, name, webViewLink.
    """
    service = _drive_service()
    folder_id = _resolve_path(service, drive_path)

    metadata = {
        "name": local_path.name,
        "parents": [folder_id],
    }
    media = MediaFileUpload(str(local_path), resumable=True)

    file = (
        service.files()
        .create(
            body=metadata,
            media_body=media,
            fields="id, name, webViewLink",
            supportsAllDrives=True,
        )
        .execute()
    )
    logger.info("Uploadé sur Drive: %s (%s)", file.get("name"), file.get("id"))
    return file


# Test manuel : `python gdrive.py "downloads/Mercedes AMGGT3Evo 2025-setup.zip" "/LMGT3/Mercedes AMG LMGT3/Le Mans"`
if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)
    local_path = Path(sys.argv[1])
    drive_path = sys.argv[2]
    result = upload_file(local_path, drive_path)
    print(result)