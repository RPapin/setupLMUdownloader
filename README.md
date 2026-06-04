# LMU Setup Download Bot

Bot Discord qui télécharge des setups LMU depuis hymosetups.com (protégé par
Cloudflare → Playwright), les upload sur Google Drive et les répertorie dans un
Google Sheet.

> Voir `CLAUDE.md` pour le contexte complet du projet (à donner à Claude Code).

## Prérequis

- Python 3.11+
- Un compte payant hymosetups.com
- Une application Discord (token bot) — idéalement deux (DEV + PROD)
- Un service account Google avec Drive API + Sheets API activées
- Un dossier Drive et un Sheet partagés en Éditeur avec le service account

## Installation locale (dev)

```bash
python -m venv venv
source venv/bin/activate          # Windows : venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium

cp .env.example .env              # puis remplir les valeurs
# placer credentials.json (service account) à la racine
```

## Tester brique par brique (recommandé)

```bash
# 1. Download seul (mettre headless=False dans hymo.py pour debug Cloudflare)
python hymo.py "Mercedes-AMG GT3 2025" "Circuit de la Sarthe (Le Mans)"

# 2. Upload Drive seul
python gdrive.py downloads/un_fichier.zip

# 3. Sheet seul
python gsheet.py

# 4. Bot complet
python bot.py
```

## ⚠️ À faire avant que ça marche

Les **sélecteurs CSS** dans `hymo.py` (login, recherche, bouton download) sont
des **placeholders**. Il faut les remplacer après inspection du site avec les
DevTools (F12). Chercher les `# TODO` dans `hymo.py`.

Conseil : commence en `headless=False` en local pour voir le navigateur agir et
vérifier que Cloudflare passe. Si le challenge bloque en headless, regarder
`playwright-stealth`.

## Déploiement sur la VM GCP e2-micro

Première fois :
```bash
git clone <ton-repo-privé> ~/lmu-bot
cd ~/lmu-bot
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
playwright install-deps chromium
# créer .env (token PROD) et déposer credentials.json
```

Service systemd :
```bash
sudo cp lmu-bot.service /etc/systemd/system/lmu-bot.service
# éditer User/chemins (CHANGE_ME -> ton user)
sudo systemctl daemon-reload
sudo systemctl enable --now lmu-bot
sudo journalctl -u lmu-bot -f
```

Mises à jour ensuite :
```bash
cd ~/lmu-bot && git pull && sudo systemctl restart lmu-bot
```

## Rappels

- Ne jamais committer `.env`, `credentials.json`, `auth_state.json` (déjà dans `.gitignore`).
- Un seul bot connecté par token à la fois (d'où DEV/PROD séparés).
- VM 1 Go RAM : Chromium fermé après chaque download, swap 2 Go configuré.
