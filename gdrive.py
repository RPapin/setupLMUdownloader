"""Upload de fichiers vers un dossier Google Drive privé via compte de service."""
import logging
from pathlib import Path

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

import config

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def _drive_service():
    creds = Credentials.from_service_account_file(
        config.GOOGLE_CREDENTIALS_PATH, scopes=SCOPES
    )
    return build("drive", "v3", credentials=creds)


def upload_file(local_path: Path) -> dict:
    """
    Upload un fichier dans le dossier Drive configuré.

    Retourne un dict avec id, name, webViewLink.
    Le dossier doit être partagé en Éditeur avec l'email du service account.
    """
    service = _drive_service()

    metadata = {
        "name": local_path.name,
        "parents": [config.DRIVE_FOLDER_ID],
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


# Test manuel : `python gdrive.py chemin/vers/fichier`
if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)
    p = Path(sys.argv[1])
    result = upload_file(p)
    print(result)
