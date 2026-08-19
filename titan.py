"""
Téléchargement de setups depuis app.tracktitan.io via Playwright.
"""
import asyncio
import logging
import re
import zipfile
from pathlib import Path
from time import sleep

from playwright.async_api import async_playwright, Page
from playwright_stealth import Stealth

import config

# navigator_platform_override aligné sur l'user-agent Linux utilisé ci-dessous
# (un mismatch UA/platform serait lui-même un signal de détection).
_stealth = Stealth(navigator_platform_override="Linux x86_64")

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


async def _log_failed_api_request(req, api_errors: list[str]) -> None:
    """
    Logge le détail (statut + corps) de toute requête tracktitan.io en échec (>=400)
    et l'accumule dans `api_errors`. Permet de distinguer un vrai refus applicatif
    (ex: 403 "permission denied" sur /download) d'un blocage anti-bot, plutôt qu'un
    simple TimeoutError opaque sur l'event "download".
    """
    if "tracktitan.io" not in req.url:
        return
    try:
        resp = await req.response()
        if not resp or resp.status < 400:
            return
        try:
            body = (await resp.text())[:1000]
        except Exception:
            body = "<unreadable>"
        logger.warning("Requête échouée %s %s -> status=%s body=%r", req.method, req.url, resp.status, body)
        api_errors.append(f"{req.method} {req.url} -> {resp.status} {body}")
    except Exception as exc:
        logger.debug("Impossible de logger la requête %s: %s", req.url, exc)


async def _screenshot_on_error(page: Page, name: str) -> None:
    """Sauvegarde un screenshot dans DOWNLOAD_DIR pour diagnostiquer les blocages."""
    try:
        dest = config.DOWNLOAD_DIR / f"debug_{name}.png"
        await page.screenshot(path=str(dest), full_page=True)
        logger.error("Screenshot sauvegardé : %s", dest)
    except Exception:
        pass


async def _dismiss_welcome_modal(page: Page) -> None:
    """Ferme toute modale ouverte (ModalContent ou HeadlessUI portal)."""
    portal = page.locator("#headlessui-portal-root")
    try:
        if await portal.count() == 0:
            return
    except Exception:
        return

    # Tentative 1 : bouton de fermeture explicite (X / aria-label Close)
    close_btn = portal.locator(
        'button[aria-label="Fermer"]'
    )
    try:
        if await close_btn.count() > 0:
            await close_btn.first.click(timeout=2_000)
            await portal.wait_for(state="hidden", timeout=3_000)
            logger.info("Modale fermée via bouton close.")
            return
    except Exception:
        pass

    # Tentative 2 : Escape (fonctionne pour la plupart des dialogs HeadlessUI)
    try:
        await page.keyboard.press("Escape")
        await portal.wait_for(state="hidden", timeout=3_000)
        logger.info("Modale fermée via Escape.")
        return
    except Exception:
        pass

    # Tentative 3 (fallback) : la modale (ex: preview vidéo replay) ne se
    # ferme pas via Escape/bouton — on la retire de force du DOM pour ne
    # plus bloquer les clics (elle est de toute façon hors du workflow).
    try:
        if await portal.count() > 0:
            await portal.evaluate("el => el.remove()")
            logger.warning("Modale portal-root supprimée de force (DOM).")
    except Exception:
        pass


async def _click_dismissing_modals(page: Page, locator) -> None:
    """
    Clique sur `locator`. Le clic "réel" de Playwright déplace la souris sur
    l'élément avant de cliquer : ce survol rouvre la modale de preview vidéo
    (ex: "Replays 3D") à chaque tentative, donc fermer la modale puis
    reréessayer un clic normal boucle indéfiniment. On bascule alors sur un
    clic JS direct (`el.click()`), qui ne simule aucun survol et n'est donc
    jamais intercepté par l'overlay.
    """
    try:
        await locator.click(timeout=6_000)
        return
    except Exception as exc:
        logger.warning("Clic réel intercepté (%s) ; fermeture des modales puis clic JS...", exc)

    await _dismiss_welcome_modal(page)
    try:
        await locator.evaluate("el => el.click()")
    except Exception as exc:
        raise RuntimeError(f"Impossible de cliquer sur l'élément (clic JS) : {exc}") from exc


async def _login(page: Page) -> None:
    """Se connecte à tracktitan avec les identifiants configurés."""
    logger.info("Connexion à tracktitan...")
    await page.goto(f"{config.TITAN_BASE_URL}/login", wait_until="domcontentloaded")
    logger.info("Page login chargée : title=%r url=%s", await page.title(), page.url)
    try:
        # Timeout élevé : le Vercel Security Checkpoint peut prendre ~10-20 s à se résoudre
        await page.wait_for_selector('input[id="email"]', timeout=45_000)
    except Exception:
        await _screenshot_on_error(page, "titan_login")
        raise RuntimeError(
            f"Champ email introuvable sur la page de login (Cloudflare/Vercel ?) — "
            f"title={await page.title()!r} url={page.url}"
        )
    await page.fill('input[id="email"]', config.TITAN_USER)
    await page.fill('input[id="password"]', config.TITAN_PASS)
    await page.click('button[type="submit"]')
    # networkidle ne convient pas : Vercel garde des requêtes ouvertes indéfiniment.
    # On attend simplement que l'URL quitte /login.
    try:
        await page.wait_for_url(lambda url: "/login" not in url, timeout=45_000)
    except Exception:
        await _screenshot_on_error(page, "titan_post_login")
        raise RuntimeError(
            f"Redirection post-login échouée (mauvais identifiants ou Vercel ?) — "
            f"title={await page.title()!r} url={page.url}"
        )
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

    async with _stealth.use_async(async_playwright()) as p:
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
        page = await context.new_page()

        try:
            await _login(page)

            await page.goto(config.TITAN_SETUP_URL + f"car={car}&track={track}", wait_until="domcontentloaded")

            await page.wait_for_selector(
                'p[data-testid="setupcard-subscription-details"]',
                timeout=30_000,
            )
            locator = page.locator('a:has(p[data-testid="setupcard-subscription-details"])')
            count = await locator.count()
            logger.info("%d carte(s) subscription trouvée(s) pour %s / %s", count, car, track)
            if count == 0:
                raise RuntimeError(f"Aucune carte 'Included in Subscription' trouvée ({car} / {track})")
            await _dismiss_welcome_modal(page)
            await _click_dismissing_modals(page, locator.first)
            await page.wait_for_load_state("domcontentloaded")
            await _dismiss_welcome_modal(page)

            dl_btn = page.get_by_role(
                "button",
                name=re.compile(r"(Télécharger la dernière version|Download Latest Version)", re.IGNORECASE),
            )

            try:
                await dl_btn.wait_for(state="visible", timeout=20_000)
            except Exception:
                await _screenshot_on_error(page, "titan_download_btn")
                raise RuntimeError(
                    f"Bouton 'Download Latest Version' introuvable — "
                    f"title={await page.title()!r} url={page.url}"
                )

            popups: list[Page] = []
            api_errors: list[str] = []
            context.on("page", lambda new_page: popups.append(new_page))
            page.on(
                "requestfinished",
                lambda req: asyncio.create_task(_log_failed_api_request(req, api_errors)),
            )

            try:
                # expect_event sur le context (et pas page.expect_download) car en
                # headless le download peut être déclenché depuis un nouvel onglet
                # ouvert par le clic plutôt que sur la page courante.
                async with context.expect_event("download", timeout=30_000) as download_info:
                    await _click_dismissing_modals(page, dl_btn)
            except Exception:
                await _screenshot_on_error(page, "titan_download_timeout")
                extra = ""
                if popups:
                    popup = popups[-1]
                    try:
                        await popup.screenshot(
                            path=str(config.DOWNLOAD_DIR / "debug_titan_download_popup.png"),
                            full_page=True,
                        )
                        extra = f" | popup ouvert: title={await popup.title()!r} url={popup.url}"
                    except Exception:
                        extra = " | popup ouvert (impossible de capturer titre/url)"
                if api_errors:
                    extra += " | requêtes API échouées: " + " ; ".join(api_errors[-3:])
                raise RuntimeError(
                    f"Timeout en attendant le download — "
                    f"title={await page.title()!r} url={page.url}{extra}"
                )
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
