# LMU Setup Download Bot

Bot Discord qui télécharge des setups LMU depuis hymosetups.com (protégé par
Cloudflare → Playwright), les upload sur Google Drive et les répertorie dans un
Google Sheet.

> Voir `CLAUDE.md` pour le contexte complet du projet (à donner à Claude Code).

---

## Prérequis

- Python 3.14.5+
- Un compte payant hymosetups.com
- Deux applications Discord (DEV + PROD) — un token chacune
- Un projet Google Cloud avec Drive API et Sheets API activées
- Un dossier Google Drive et un Google Sheet (votre compte personnel, pas de Shared Drive requis)

---

## Structure des identifiants

```
credentials/
├── client_secret.json   # OAuth2 Desktop app (téléchargé depuis Google Cloud Console)
└── token.json           # Généré localement par python google_auth.py (NE PAS COMMITTER)

.env                     # Variables d'environnement (NE PAS COMMITTER)
```

---

## 1. Discord — Créer les bots DEV et PROD

1. Aller sur [discord.com/developers/applications](https://discord.com/developers/applications)
2. **New Application** → donner un nom (ex. `LMU Bot DEV`)
3. Onglet **Bot** → **Reset Token** → copier le token
4. Activer **Message Content Intent** si besoin
5. Onglet **OAuth2 → URL Generator** → scope `bot` + `applications.commands`
   → cocher permission **Send Messages** → copier l'URL → inviter le bot sur ton serveur de test
6. Répéter pour la version PROD avec un nom différent

Les deux tokens vont dans `.env` — utiliser le DEV en local, le PROD sur la VM.

Pour récupérer l'**ID du serveur** (DISCORD_GUILD_ID) : Discord → Paramètres →
Mode développeur activé → clic droit sur le serveur → **Copier l'ID du serveur**.

---

## 2. Google Cloud — Activer les APIs et créer les credentials OAuth2

### a. Créer un projet et activer les APIs

1. Aller sur [console.cloud.google.com](https://console.cloud.google.com)
2. **New Project** → donner un nom (ex. `lmu-bot`)
3. Menu → **APIs & Services → Library**
   - Chercher **Google Drive API** → **Enable**
   - Chercher **Google Sheets API** → **Enable**

### b. Configurer l'écran de consentement OAuth

1. Menu → **APIs & Services → OAuth consent screen**
2. User Type : **External** → **Create**
3. Remplir :
   - App name : `LMU Bot` (ou ce que tu veux)
   - User support email : ton email
   - Developer contact : ton email
4. **Save and Continue** jusqu'à la fin (scopes et test users peuvent rester vides pour l'instant)
5. Une fois créé : **Publish App** → confirmer
   > Passer en "In production" évite que le refresh token expire après 7 jours.
   > L'écran "app non vérifiée" apparaît lors de l'auth — cliquer **Avancé → Continuer**.

### c. Créer les credentials OAuth2 Desktop

1. Menu → **APIs & Services → Credentials**
2. **+ Create Credentials → OAuth client ID**
3. Application type : **Desktop app** → **Create**
4. **Download JSON** → renommer le fichier en `client_secret.json`
5. Placer le fichier dans le dossier `credentials/`

---

## 3. Google Drive — Récupérer l'ID du dossier cible

1. Ouvrir [drive.google.com](https://drive.google.com) avec ton compte personnel
2. Créer un dossier (ex. `LMU Setups`)
3. Ouvrir le dossier → l'URL contient l'ID :
   `https://drive.google.com/drive/folders/`**`<DRIVE_FOLDER_ID>`**
4. Copier cet ID → le mettre dans `.env`

---

## 4. Google Sheets — Créer le tableau de suivi

1. Ouvrir [sheets.google.com](https://sheets.google.com) → **Blank spreadsheet**
2. Donner un nom (ex. `LMU Setups Tracker`)
3. L'URL contient l'ID :
   `https://docs.google.com/spreadsheets/d/`**`<SHEET_ID>`**`/edit`
4. Copier cet ID → le mettre dans `.env`

> Les en-têtes (`Date`, `Voiture`, `Circuit`, `Version`, `Class`, `Fichier`,
> `Lien Drive`, `Demandé par`) sont créées automatiquement au premier appel.

---

## 5. Générer le token OAuth2

```bash
# Depuis ta machine locale (pas la VM — il faut un navigateur)
python google_auth.py
```

Un navigateur s'ouvre → connecte-toi avec le compte Google propriétaire du Drive
et du Sheet → cliquer **Avancé → Continuer vers LMU Bot** → **Autoriser**.

Le fichier `credentials/token.json` est créé. Il contient le refresh token qui
permet à la VM de s'authentifier sans navigateur.

---

## 6. Remplir le fichier `.env`

Créer un fichier `.env` à la racine du projet :

```env
# Discord
DISCORD_TOKEN=ton_token_bot_dev_ou_prod
DISCORD_GUILD_ID=id_du_serveur_discord   # optionnel, sync des commandes plus rapide

# hymosetups
HYMO_USER=email@exemple.com
HYMO_PASS=mot_de_passe_hymo

# Google
DRIVE_FOLDER_ID=id_du_dossier_drive
SHEET_ID=id_du_google_sheet
```

---

## Installation locale (dev)

```bash
python -m venv venv
source venv/bin/activate        # Windows : venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium

cp .env.example .env            # puis remplir les valeurs
mkdir credentials
# placer client_secret.json dans credentials/
python google_auth.py           # génère credentials/token.json
```

---

## Tester brique par brique (recommandé)

```bash
# 1. Auth Google (si pas encore fait)
python google_auth.py

# 2. Upload Drive seul
python gdrive.py downloads/un_fichier.zip LMGT3/mercedes-amg-lmgt3/lemans

# 3. Sheet seul
python gsheet.py

# 4. Download seul (headless=False dans config pour debug Cloudflare)
python hymo.py

# 5. Bot complet
python bot.py
```

---

## ⚠️ À faire avant que ça marche

Les **sélecteurs CSS** dans `hymo.py` (login, recherche, bouton download) sont
des **placeholders**. Les remplacer après inspection du site avec les DevTools (F12).
Chercher les `# TODO` dans `hymo.py`.

Commencer en `headless=False` pour voir le navigateur et vérifier que Cloudflare
passe. Si le challenge bloque en headless, regarder `playwright-stealth`.

---

## Déploiement sur la VM GCP e2-micro

### Première installation

```bash
git clone <ton-repo-privé> ~/lmu-bot
cd ~/lmu-bot
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
playwright install-deps chromium
mkdir credentials

# Copier depuis ta machine locale :
scp .env user@vm-ip:~/lmu-bot/.env
scp credentials/token.json user@vm-ip:~/lmu-bot/credentials/token.json
# client_secret.json est optionnel sur la VM (pas besoin d'auth interactive)
```

### Service systemd

```bash
sudo cp lmu-bot.service /etc/systemd/system/lmu-bot.service
# éditer User/WorkingDirectory dans le fichier si besoin
sudo systemctl daemon-reload
sudo systemctl enable --now lmu-bot
sudo journalctl -u lmu-bot -f
```

### Mises à jour

```bash
cd ~/lmu-bot && git pull && sudo systemctl restart lmu-bot
```

### Renouvellement du token (si expiré)

```bash
# En local :
python google_auth.py
scp credentials/token.json user@vm-ip:~/lmu-bot/credentials/token.json
sudo systemctl restart lmu-bot
```

---

## Rappels

- Ne jamais committer `.env`, `credentials/` (déjà dans `.gitignore`).
- Un seul bot connecté par token à la fois — utiliser le token DEV en local, PROD sur la VM.
- VM 1 Go RAM : Chromium est fermé après chaque download, swap 2 Go recommandé.
