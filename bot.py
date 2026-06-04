"""
Point d'entrée : bot Discord avec commande slash /setup.

Workflow de /setup :
  1. l'utilisateur choisit une voiture et un circuit
  2. download du setup sur hymosetups (Playwright / Cloudflare)
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
import gdrive
import gsheet

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("lmu-bot")

# Un seul download à la fois (RAM limitée + évite de surcharger hymosetups)
_download_lock = asyncio.Lock()


class LMUBot(discord.Client):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        # Sync rapide sur un serveur précis si DISCORD_GUILD_ID est défini,
        # sinon sync global (peut prendre jusqu'à 1h à se propager).
        if config.DISCORD_GUILD_ID:
            guild = discord.Object(id=int(config.DISCORD_GUILD_ID))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()


client = LMUBot()


# --- Autocomplétion des choix ---
async def car_autocomplete(interaction: discord.Interaction, current: str):
    return [
        app_commands.Choice(name=c, value=c)
        for c in combos.CARS
        if current.lower() in c.lower()
    ][:25]


async def track_autocomplete(interaction: discord.Interaction, current: str):
    return [
        app_commands.Choice(name=t, value=t)
        for t in combos.TRACKS
        if current.lower() in t.lower()
    ][:25]


@client.tree.command(name="setup", description="Télécharge un setup LMU et l'archive.")
@app_commands.describe(voiture="Voiture", circuit="Circuit")
@app_commands.autocomplete(voiture=car_autocomplete, circuit=track_autocomplete)
async def setup_command(interaction: discord.Interaction, voiture: str, circuit: str):
    # On répond tout de suite (le travail dépasse les 3 s autorisées par Discord)
    await interaction.response.defer(thinking=True)

    if _download_lock.locked():
        await interaction.followup.send(
            "⏳ Un téléchargement est déjà en cours, réessaie dans un instant."
        )
        return

    async with _download_lock:
        try:
            # 1 + 2. Download via Playwright (bloquant -> thread pour ne pas
            # geler la boucle asyncio de discord.py si besoin ; ici hymo est déjà async)
            await interaction.followup.send(
                f"🔍 Recherche et téléchargement : **{voiture}** @ **{circuit}**..."
            )
            local_path = await hymo.download_setup(voiture, circuit)

            # 3. Upload Drive (API synchrone -> exécuter dans un thread)
            file = await asyncio.to_thread(gdrive.upload_file, local_path)
            drive_link = file.get("webViewLink", "")

            # 4. Mise à jour du Sheet
            await asyncio.to_thread(
                gsheet.add_entry,
                voiture,
                circuit,
                local_path.name,
                drive_link,
                str(interaction.user),
            )

            # 5. Réponse finale
            await interaction.followup.send(
                f"✅ Setup **{voiture}** @ **{circuit}** prêt !\n"
                f"📄 `{local_path.name}`\n"
                f"🔗 {drive_link}"
            )

            # Nettoyage du fichier local (le Drive fait foi)
            try:
                local_path.unlink(missing_ok=True)
            except OSError:
                pass

        except Exception as exc:  # noqa: BLE001 - on veut remonter toute erreur à l'utilisateur
            logger.exception("Échec du workflow /setup")
            await interaction.followup.send(
                f"❌ Échec : `{exc}`\nVérifie les logs du bot pour le détail."
            )


@client.event
async def on_ready():
    logger.info("Connecté en tant que %s (id=%s)", client.user, client.user.id)


if __name__ == "__main__":
    client.run(config.DISCORD_TOKEN)
