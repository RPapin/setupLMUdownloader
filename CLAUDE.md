# CLAUDE.md — LMU Setup Download Bot

## Objectif du projet

Bot Discord qui automatise le téléchargement de setups payants pour le jeu
**Le Mans Ultimate (LMU)** depuis **hymosetups.com** ou **app.tracktitan.io**,
puis les archive et les répertorie.

Workflow déclenché par une commande slash Discord `/setup` :

1. **Sélection** du site source (Hymo Setups / Track Titan), d'une voiture et d'un circuit.
2. **Téléchargement** du setup correspondant via le site choisi
   (comptes payants — les sites sont protégés par **Cloudflare**).
3. **Upload** du fichier sur un dossier Google Drive privé.
4. **Mise à jour** d'un Google Sheet servant de tableau de suivi des setups
   téléchargés (une matrice par site : "Matrix Hymo" et "Matrix Titan").

## Contrainte technique majeure : Cloudflare

hymosetups.com est derrière **Cloudflare** → `requests` se fait bloquer par le
challenge JS. On utilise donc **Playwright (Chromium headless)** pour :
- se connecter avec les identifiants payants,
- naviguer jusqu'au setup,
- déclencher le téléchargement réel via le navigateur.

NE PAS tenter de reproduire le download avec `requests`/`httpx` seuls : ça ne
passera pas Cloudflare. Tout passe par le contexte navigateur Playwright (qui
porte les cookies `cf_clearance` / session).

### Détails Cloudflare à garder en tête
- Lancer Chromium en mode le moins détectable possible (pas de flags
  d'automatisation criards). Envisager `playwright-stealth` si le challenge
  bloque le headless. Tester d'abord en `headless=False` en local.
- Login systématique à chaque session avec les identifiants `.env` — pas de storage_state persisté.
- Sur la VM (headless, IP datacenter), Cloudflare peut être plus agressif qu'en
  local. Prévoir un fallback / retry et logguer les pages de challenge.

## Stack technique

- **Python 3.11+**
- **discord.py** — bot Discord, commandes slash (app commands)
- **Playwright (Chromium)** — automatisation navigateur pour passer Cloudflare
- **google-api-python-client + google-auth** — upload Google Drive
- **gspread** — mise à jour du Google Sheet
- Auth Google via **compte de service** (service account JSON), pas d'OAuth
  interactif. Le dossier Drive et le Sheet sont partagés en Éditeur avec
  l'email du service account.

## Déploiement cible

- **Dev/test** : en local (idéalement WSL2 Ubuntu pour coller à la prod).
- **Prod** : VM **Google Cloud e2-micro** (Always Free, région us-west1),
  Ubuntu 22.04, 1 Go RAM + 2 Go swap. Bot lancé via **systemd**
  (service `lmu-bot`, `Restart=always`).
- Déploiement par `git pull` + `sudo systemctl restart lmu-bot`.

### Contrainte RAM
La VM n'a qu'1 Go de RAM. Chromium est gourmand :
- toujours **fermer le navigateur** (`browser.close()`) après chaque download,
- ne **lancer Chromium qu'à la demande** (à réception d'une commande), pas au
  démarrage du bot,
- une seule session de download à la fois (lock / file d'attente si besoin).

## Conventions de code

- Secrets via **variables d'environnement** (fichier `.env` en local, chargé
  avec `python-dotenv`). Sur la VM, `.env` ou variables systemd.
- Ne **JAMAIS committer** : `.env`, `credentials.json`, `venv/`, fichiers téléchargés. (Voir `.gitignore`.)
- Utiliser `pathlib`/`os.path` pour les chemins (compat Windows/Linux).
- Logguer proprement (module `logging`), pas de `print` en prod.
- Code asynchrone (discord.py et Playwright async API).

## Deux bots Discord (DEV / PROD)

Pour pouvoir tester en local pendant que la prod tourne, prévoir **deux
applications Discord** (deux tokens). Discord refuse deux connexions du même
token simultanément. Le token utilisé est lu depuis `DISCORD_TOKEN` dans `.env`.

## Variables d'environnement attendues (.env)

```
DISCORD_TOKEN=          # token du bot (DEV ou PROD selon l'environnement)
DISCORD_GUILD_ID=       # (optionnel) ID du serveur pour sync rapide des slash commands
HYMO_USER=              # email du compte hymosetups payant
HYMO_PASS=              # mot de passe hymosetups
TITAN_USER=             # email du compte tracktitan payant
TITAN_PASS=             # mot de passe tracktitan
GOOGLE_CREDENTIALS_PATH=credentials.json   # chemin du JSON service account
DRIVE_FOLDER_ID=        # ID du dossier Drive privé cible
SHEET_ID=               # ID du Google Sheet de suivi
```

## Structure des fichiers

```
lmu-bot/
├─ CLAUDE.md                  # ce fichier (contexte projet)
├─ bot.py                     # point d'entrée : bot Discord + commandes slash
├─ hymo.py                    # scraping/download hymosetups via Playwright
├─ titan.py                   # scraping/download tracktitan via Playwright
├─ gdrive.py                  # upload Google Drive
├─ gsheet.py                  # mise à jour du Google Sheet (2 onglets Matrix)
├─ combos.py                  # mapping combos voiture/circuit -> infos de recherche
├─ config.py                  # chargement des variables d'env
├─ requirements.txt
├─ .gitignore
├─ .env                       # NON commité — à créer manuellement
├─ credentials.json           # NON commité — service account Google
└─ downloads/                 # NON commité — setups téléchargés temporairement
```

## État d'avancement / TODO

- [ ] **CRITIQUE** : finaliser `hymo.py` — les sélecteurs CSS (login, champ
      recherche, bouton download) sont des **placeholders** à remplacer après
      inspection réelle du site avec les DevTools. Voir les `TODO` dans le code.
- [ ] Valider le passage de Cloudflare en headless sur la VM (tester stealth).
- [ ] Définir la vraie structure des combos voiture/circuit dans `combos.py`
      (liste réelle ou recherche dynamique sur le site).
- [ ] Tester chaque brique isolément (`test_*.py`) avant d'assembler.
- [ ] Gérer la file d'attente si plusieurs `/setup` arrivent en même temps.

## Tests manuels recommandés (ordre)

1. `hymo.py` seul en `headless=False` : login + download d'UN setup connu.
2. `gdrive.py` seul : upload d'un fichier test dans le dossier Drive.
3. `gsheet.py` seul : append d'une ligne test.
4. Assemblage dans `bot.py`, test via commande Discord sur le serveur de test.

## Notes légales / éthiques

- L'automatisation **réutilise** un abonnement payant légitime, elle ne le
  contourne pas. Respecter les ToS de hymosetups (pas de redistribution
  publique des setups ; le Drive est **privé**).
- Ne pas marteler le site (un download à la demande, pas de scraping massif).
