"""
Téléchargement de setups depuis hymosetups.com via Playwright.
"""
import asyncio
import logging
from pathlib import Path
from time import sleep

import dotenv
from playwright.async_api import async_playwright, Page, BrowserContext

import config

logger = logging.getLogger(__name__)


async def _ensure_logged_in(context: BrowserContext, page: Page) -> None:
    """Se connecte à hymosetups si la session restaurée n'est pas/plus valide."""
    await page.goto(config.HYMO_BASE_URL, wait_until="domcontentloaded")

    already_logged = await page.locator("text=Logout").count() > 0
    if already_logged:
        logger.info("Session hymosetups déjà active.")
        return

    logger.info("Connexion à hymosetups...")

    await page.goto(f"{config.HYMO_BASE_URL}/login", wait_until="domcontentloaded")

    await page.fill('input[id="login-email"]', config.HYMO_USER)
    await page.fill('input[id="login-password"]', config.HYMO_PASS)

    await page.click('button[type="submit"]')
    sleep(5)
    # Attendre la fin de la navigation post-login
    await page.wait_for_load_state("networkidle")

    # Sauvegarder l'état (cookies + cf_clearance) pour réutilisation future
    await context.storage_state(path=str(config.AUTH_STATE_PATH))
    logger.info("Connexion réussie, session sauvegardée.")


async def download_setup(car: str, track: str) -> tuple[Path, str]:
    """
    Télécharge le setup correspondant au combo voiture/circuit.

    Retourne le chemin du fichier téléchargé.
    Lève une exception si rien n'est trouvé / téléchargé.
    """
    logger.info("Téléchargement setup: car=%s track=%s", car, track)

    async with async_playwright() as p:
        # headless=True en prod. Mettre False en local pour debugger Cloudflare.
        browser = await p.chromium.launch(
            headless=config.HEADLESS,
            args=["--no-sandbox", "--disable-dev-shm-usage"],  # utile en VM/conteneur
        )

        # Restaure la session si elle existe (évite de relogger + passe Cloudflare)
        storage = (
            str(config.AUTH_STATE_PATH)
            if config.AUTH_STATE_PATH.exists()
            else None
        )
        context = await browser.new_context(
            accept_downloads=True,
            storage_state=storage,
            # Un user-agent réaliste aide face à Cloudflare
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        page = await context.new_page()

        try:
            await _ensure_logged_in(context, page)

            await page.goto(config.HYMO_SETUP_URL + f"/{car}/{track}", wait_until="domcontentloaded")
            # Ajout de la version
            version = await page.locator("tbody tr:first-child td:nth-child(5)").inner_text()
            version = version.lstrip("Vv")
            #remove du v
            await page.locator('a[aria-label="Install setup"]').nth(1).click()

            async with page.expect_download() as download_info:
                await page.get_by_role("button", name="Download ZIP").click()
            download = await download_info.value

            # Nom de fichier propre basé sur le combo
            dest = config.DOWNLOAD_DIR / f"{car}_{track}_V{version}.zip"
            await download.save_as(str(dest))

            logger.info("Setup téléchargé: %s", dest)
            return dest, version

        finally:
            # IMPORTANT (RAM limitée) : toujours fermer le navigateur
            await context.close()
            await browser.close()


# Test manuel rapide : `python hymo.py "Mercedes-AMG GT3" "Le Mans"`
if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)
    _car = sys.argv[1] if len(sys.argv) > 1 else "mercedes-amg-lmgt3"
    _track = sys.argv[2] if len(sys.argv) > 2 else "lemans"
    path = asyncio.run(download_setup(_car, _track))
    print("Téléchargé ->", path)
