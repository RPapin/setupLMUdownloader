"""
Téléchargement de setups depuis hymosetups.com via Playwright.
"""
import asyncio
import logging
from pathlib import Path

from playwright.async_api import async_playwright, Page

import config

logger = logging.getLogger(__name__)


async def _login(page: Page) -> None:
    """Se connecte à hymosetups avec les identifiants configurés."""
    logger.info("Connexion à hymosetups...")
    await page.goto(f"{config.HYMO_BASE_URL}/login", wait_until="domcontentloaded")
    await page.fill('input[id="login-email"]', config.HYMO_USER)
    await page.fill('input[id="login-password"]', config.HYMO_PASS)
    await page.click('button[type="submit"]')
    await page.wait_for_load_state("networkidle")
    logger.info("Connexion hymosetups réussie.")


async def download_setup(car: str, track: str, current_version: str | None = None) -> tuple[Path | None, str]:
    """
    Télécharge le setup correspondant au combo voiture/circuit.

    Si current_version est fourni et correspond à la version sur le site,
    retourne (None, version) sans télécharger.
    Sinon retourne (chemin_fichier, version).
    Lève une exception si rien n'est trouvé / téléchargé.
    """
    logger.info("Téléchargement setup: car=%s track=%s", car, track)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=config.HEADLESS,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        context = await browser.new_context(
            accept_downloads=True,
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        page = await context.new_page()

        try:
            await _login(page)

            await page.goto(config.HYMO_SETUP_URL + f"/{car}/{track}", wait_until="domcontentloaded")
            version = await page.locator("tbody tr:first-child td:nth-child(5)").inner_text()
            version = version.lstrip("Vv")

            if current_version is not None and version == current_version:
                logger.info("Setup déjà à jour (version %s), téléchargement ignoré.", version)
                return None, version

            await page.locator('a[aria-label="Install setup"]').nth(1).click()

            async with page.expect_download() as download_info:
                await page.get_by_role("button", name="Download ZIP").click()
            download = await download_info.value

            dest = config.DOWNLOAD_DIR / f"{car}_{track}_V{version}.zip"
            await download.save_as(str(dest))

            logger.info("Setup téléchargé: %s", dest)
            return dest, version

        finally:
            await context.close()
            await browser.close()


# Test manuel rapide : `python hymo.py "Mercedes-AMG GT3" "Le Mans"`
if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)
    _car = sys.argv[1] if len(sys.argv) > 1 else "mercedes-amg-lmgt3"
    _track = sys.argv[2] if len(sys.argv) > 2 else "lemans"
    path, ver = asyncio.run(download_setup(_car, _track))
    print("Téléchargé ->", path, ver)
