"""
Credentials OAuth2 Google partagés entre gdrive.py et gsheet.py.

Première utilisation (en local) :
    python google_auth.py
    → ouvre un navigateur, connecte-toi avec ton compte Google, autorise l'app
    → token.json est sauvegardé à côté de ce fichier

Sur la VM (sans navigateur) :
    Copie token.json depuis ta machine locale vers la VM.
    Le token se rafraîchit automatiquement via le refresh_token (pas de navigateur).

Expiration du refresh token :
    En mode "Testing" sur Google Cloud Console → expire après 7 jours.
    Pour lever cette limite : Google Cloud Console → OAuth consent screen
    → passer en "In production" (pas de vérification nécessaire pour des scopes sensibles).
"""
import logging
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

import config

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]


def get_credentials() -> Credentials:
    """Retourne des credentials valides, rafraîchit ou lance le flow si nécessaire."""
    creds = None

    if config.GOOGLE_TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(
            str(config.GOOGLE_TOKEN_PATH), SCOPES
        )

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(config.GOOGLE_CLIENT_SECRETS_PATH), SCOPES
            )
            creds = flow.run_local_server(port=0)

        config.GOOGLE_TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
        logger.info("Token OAuth2 sauvegardé : %s", config.GOOGLE_TOKEN_PATH)

    return creds


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    get_credentials()
    print(f"Authentification réussie. Token sauvegardé dans : {config.GOOGLE_TOKEN_PATH}")
    print("Copie ce fichier sur la VM pour qu'elle puisse accéder à Drive et Sheets.")
