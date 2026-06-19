"""
Téléchargement de setups depuis gosetup.com via Playwright.
"""
import asyncio
import logging
from pathlib import Path

from playwright.async_api import async_playwright, Page

import config

logger = logging.getLogger(__name__)

# Rotation entre les comptes GoSetup pour économiser les crédits
_account_index = 0


def _next_account() -> tuple[str, str]:
    global _account_index
    account = config.GOSETUP_ACCOUNTS[_account_index % len(config.GOSETUP_ACCOUNTS)]
    _account_index += 1
    return account


async def _login(page: Page, user: str, password: str) -> None:
    logger.info("Connexion à GoSetup (compte %s)...", user)
    await page.goto(f"{config.GOSETUP_BASE_URL}/my-account/downloads/", wait_until="domcontentloaded")
    await page.fill('input[name="username"]', user)
    await page.fill('input[name="password"]', password)
    await page.click('button[type="submit"]')
    await page.wait_for_load_state("networkidle")
    logger.info("Connexion GoSetup réussie.")


async def download_setup(car: str, track: str, current_version: str | None = None) -> tuple[Path | None, str]:
    """
    Télécharge le setup correspondant au combo voiture/circuit.

    Si current_version est fourni et correspond à la version sur le site,
    retourne (None, version) sans télécharger.
    Sinon retourne (chemin_fichier, version).
    Lève une exception si rien n'est trouvé / téléchargé.
    """
    logger.info("Téléchargement setup GoSetup: car=%s track=%s", car, track)

    user, password = _next_account()

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
            await _login(page, user, password)

            await page.goto(config.GOSETUP_SETUP_URL + f"brx_d3ee75={car}&brx_e8e98e={track}", wait_until="domcontentloaded")

            version = await page.locator("div.brxe-250a05.brxe-shortcode").inner_text()
            version = version.lstrip("Vv").strip()
            print("version : " + version)
            if current_version is not None and version == current_version:
                logger.info("Setup déjà à jour (version %s), téléchargement ignoré.", version)
                return None, version

            # Go to LMU tab
            await page.locator("div#brxe-42ca6b").click()
            await page.locator("div.brxe-0d6307.brxe-shortcode.btn-download a").click()
            async with page.expect_download() as download_info:
                await page.locator("button.swal2-confirm.gos-dl-confirm").click()
            download = await download_info.value

            dest = config.DOWNLOAD_DIR / f"gosetup_{car}_{track}_V{version}.zip"
            await download.save_as(str(dest))

            logger.info("Setup GoSetup téléchargé: %s", dest)
            return dest, version

        finally:
            await context.close()
            await browser.close()


# Test manuel rapide : `python gosetup.py "porsche-911-gt3-r-992" "lemans"`
if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)
    _car = sys.argv[1] if len(sys.argv) > 1 else "Ford+Mustang+LMGT3"
    _track = sys.argv[2] if len(sys.argv) > 2 else "spa"
    path, ver = asyncio.run(download_setup(_car, _track))
    print("Téléchargé ->", path, ver)