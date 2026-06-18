"""
Téléchargement de setups depuis app.tracktitan.io via Playwright.
"""
import asyncio
import logging
import re
import zipfile
from pathlib import Path

from playwright.async_api import async_playwright, Page

import config

logger = logging.getLogger(__name__)


def _extract_version_from_zip(zip_path: Path) -> str:
    """
    Extrait la version depuis le nom du premier .svm dans le ZIP.
    Format attendu : "HYMO 1.2.4 AMR BAH WR.svm" → "1.2.4"
    """
    with zipfile.ZipFile(zip_path) as zf:
        svm_files = [name for name in zf.namelist() if name.endswith(".svm")]
    if not svm_files:
        logger.warning("Aucun fichier .svm trouvé dans %s", zip_path)
        return "unknown"
    filename = Path(svm_files[0]).name
    match = re.search(r'\b(\d+\.\d+\.\d+)\b', filename)
    if not match:
        logger.warning("Version introuvable dans le nom de fichier : %s", filename)
        return "unknown"
    return match.group(1)


async def _screenshot_on_error(page: Page, name: str) -> None:
    """Sauvegarde un screenshot dans DOWNLOAD_DIR pour diagnostiquer les blocages."""
    try:
        dest = config.DOWNLOAD_DIR / f"debug_{name}.png"
        await page.screenshot(path=str(dest), full_page=True)
        logger.error("Screenshot sauvegardé : %s", dest)
    except Exception:
        pass


async def _dismiss_welcome_modal(page: Page) -> None:
    """Ferme la modale 'Herzlich Willkommen' si elle est présente après login."""
    modal = page.locator('[class*="ModalContent"]')
    try:
        await modal.wait_for(timeout=3_000)
        close_btn = modal.locator('button[type="button"]')
        await close_btn.click()
        logger.info("Modale de bienvenue fermée.")
    except Exception:
        pass  # modale absente, rien à faire


async def _login(page: Page) -> None:
    """Se connecte à tracktitan avec les identifiants configurés."""
    logger.info("Connexion à tracktitan...")
    await page.goto(f"{config.TITAN_BASE_URL}/login", wait_until="domcontentloaded")
    logger.info("Page login chargée : title=%r url=%s", await page.title(), page.url)
    try:
        await page.wait_for_selector('input[id="email"]', timeout=15_000)
    except Exception:
        await _screenshot_on_error(page, "titan_login")
        raise RuntimeError(
            f"Champ email introuvable sur la page de login (Cloudflare ?) — "
            f"title={await page.title()!r} url={page.url}"
        )
    await page.fill('input[id="email"]', config.TITAN_USER)
    await page.fill('input[id="password"]', config.TITAN_PASS)
    await page.click('button[type="submit"]')
    await page.wait_for_load_state("networkidle")
    await _dismiss_welcome_modal(page)
    logger.info("Connexion tracktitan réussie.")


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
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
            ],
        )
        context = await browser.new_context(
            accept_downloads=True,
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
        )
        # Masque navigator.webdriver pour réduire la détection Cloudflare
        await context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        page = await context.new_page()

        try:
            await _login(page)

            await page.goto(config.TITAN_SETUP_URL + f"car={car}&track={track}", wait_until="domcontentloaded")

            await page.wait_for_selector(
                'p[data-testid="setupcard-subscription-details"]',
                timeout=15_000,
            )
            locator = page.locator('a:has(p[data-testid="setupcard-subscription-details"])')
            count = await locator.count()
            logger.info("%d carte(s) subscription trouvée(s) pour %s / %s", count, car, track)
            if count == 0:
                raise RuntimeError(f"Aucune carte 'Included in Subscription' trouvée ({car} / {track})")
            await locator.first.click()

            async with page.expect_download() as download_info:
                await page.get_by_role("button", name="Download Latest Version").click()
            download = await download_info.value

            tmp_dest = config.DOWNLOAD_DIR / f"{car}_{track}.zip"
            await download.save_as(str(tmp_dest))

            version = _extract_version_from_zip(tmp_dest)

            if current_version is not None and version == current_version:
                logger.info("Setup déjà à jour (version %s), suppression du fichier.", version)
                tmp_dest.unlink(missing_ok=True)
                return None, version

            dest = config.DOWNLOAD_DIR / f"hymo_{car}_{track}_V{version}.zip"
            tmp_dest.rename(dest)

            logger.info("Setup téléchargé: %s", dest)
            return dest, version

        finally:
            await context.close()
            await browser.close()


# Test manuel rapide : `python titan.py "Vantage_AMR_GT3Evo_2024" "Bahrainwec"`
if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)
    _car = sys.argv[1] if len(sys.argv) > 1 else "Vantage_AMR_GT3Evo_2024"
    _track = sys.argv[2] if len(sys.argv) > 2 else "Bahrainwec"
    path, ver = asyncio.run(download_setup(_car, _track))
    print("Téléchargé ->", path, ver)
