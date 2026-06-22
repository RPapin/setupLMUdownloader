"""
Point d'entrée : bot Discord avec commande slash /setup.

Workflow de /setup :
  1. l'utilisateur choisit le site source, une voiture et un circuit
  2. download du setup via Playwright (Cloudflare)
  3. upload sur Google Drive
  4. ajout d'une ligne au Google Sheet de suivi
  5. réponse à l'utilisateur avec le lien Drive
"""
import asyncio
import logging

import discord
from discord import app_commands

import config
import combos
import hymo
import titan
import gosetup
import gdrive
import gsheet

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("lmu-bot")

# Un seul download à la fois (RAM limitée + évite de surcharger les sites)
_download_lock = asyncio.Lock()

SITES = [
    # app_commands.Choice(name="Hymo Setups", value="hymo"),
    app_commands.Choice(name="Track Titan (HYMO)", value="titan"),
    app_commands.Choice(name="GoSetup", value="gosetup"),
]


class LMUBot(discord.Client):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        if config.DISCORD_GUILD_ID:
            guild = discord.Object(id=int(config.DISCORD_GUILD_ID))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()


client = LMUBot()


async def car_autocomplete(interaction: discord.Interaction, current: str):
    return [
        app_commands.Choice(name=f"[{c['class_code']}] {c['car_drive']}", value=c["car_drive"])
        for c in combos.CARS
        if current.lower() in c["car_drive"].lower() or current.lower() in c["class_code"].lower()
    ][:25]


async def track_autocomplete(interaction: discord.Interaction, current: str):
    return [
        app_commands.Choice(name=t["track_drive"], value=t["track_drive"])
        for t in combos.TRACKS
        if current.lower() in t["track_drive"].lower()
    ][:25]


@client.tree.command(name="setup", description="Télécharge un setup LMU et l'archive.")
@app_commands.describe(site="Source du setup", voiture="Voiture", circuit="Circuit")
@app_commands.choices(site=SITES)
@app_commands.autocomplete(voiture=car_autocomplete, circuit=track_autocomplete)
async def setup_command(
    interaction: discord.Interaction,
    site: app_commands.Choice[str],
    voiture: str,
    circuit: str,
):
    await interaction.response.defer(thinking=True)

    if _download_lock.locked():
        await interaction.followup.send(
            "⏳ Un téléchargement est déjà en cours, réessaie dans un instant."
        )
        return

    async with _download_lock:
        try:
            car_info = next((c for c in combos.CARS if c["car_drive"] == voiture), None)
            track_info = next((t for t in combos.TRACKS if t["track_drive"] == circuit), None)

            if car_info is None or track_info is None:
                await interaction.followup.send(
                    f"❌ Combo introuvable : **{voiture}** @ **{circuit}**."
                )
                return

            class_code = car_info["class_code"]
            car_drive = car_info["car_drive"]
            track_drive = track_info["track_drive"]
            site_value = site.value

            if site_value == "hymo":
                car_id = car_info["car_hymo"]
                track_id = track_info["track_hymo"]
                downloader = hymo.download_setup
            elif site_value == "gosetup":
                car_id = car_info["car_gosetup"]
                track_id = track_info["track_gosetup"]
                downloader = gosetup.download_setup
            else:
                car_id = car_info["car_titan"]
                track_id = track_info["track_titan"]
                downloader = titan.download_setup

            matrix_versions = await asyncio.to_thread(gsheet.get_matrix_versions, site_value)
            current_version = matrix_versions.get((car_drive, track_drive))

            await interaction.followup.send(
                f"🔍 [{site.name}] Vérification : **{car_drive}** @ **{track_drive}**..."
            )

            local_path, version_setup = await downloader(
                car_id, track_id, current_version=current_version
            )
            # If the setup is already in the drive we return the link of the setup
            if local_path is None:
                matrix_links = await asyncio.to_thread(gsheet.get_matrix_links, site_value)
                existing_link = matrix_links.get((car_drive, track_drive), "")
                msg = (
                    f"✅ Setup **{car_drive}** @ **{track_drive}** déjà à jour "
                    f"(version `{version_setup}`) sur **{site.name}**."
                )
                if existing_link:
                    msg += f"\n🔗 {existing_link}"
                await interaction.followup.send(msg)
                return
            # else we add the link to the drive
            drive_path = f"{class_code}/{car_drive}/{track_drive}"
            file = await asyncio.to_thread(gdrive.upload_file, local_path, drive_path)
            drive_link = file.get("webViewLink", "")

            await asyncio.to_thread(
                gsheet.add_entry,
                car_drive,
                track_drive,
                version_setup,
                class_code,
                local_path.name,
                drive_link,
                str(interaction.user),
                site_value,
            )

            await interaction.followup.send(
                f"✅ Setup **{voiture}** @ **{circuit}** prêt ! [{site.name}]\n"
                f"🏷️ Version : `{version_setup}`\n"
                f"📄 `{local_path.name}`\n"
                f"🔗 {drive_link}"
            )

            try:
                local_path.unlink(missing_ok=True)
            except OSError:
                pass

        except Exception as exc:  # noqa: BLE001
            logger.exception("Échec du workflow /setup")
            await interaction.followup.send(
                f"❌ Échec : `{exc}`\nVérifie les logs du bot pour le détail."
            )


@client.event
async def on_ready():
    logger.info("Connecté en tant que %s (id=%s)", client.user, client.user.id)


if __name__ == "__main__":
    client.run(config.DISCORD_TOKEN)
