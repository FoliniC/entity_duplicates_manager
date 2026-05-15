#!/bin/bash
CONFIG_DIR="/home/carlo/docker/homeassistant/config"
REPO_URL="https://github.com/FoliniC/ha-config.git"
TOKEN="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"

cd "$CONFIG_DIR" || exit 1

echo "=== BACKUP HA CONFIG: $(date) ==="

# Assicurati che il remote sia corretto con il token
git remote set-url origin "https://$TOKEN@github.com/FoliniC/ha-config.git"

# Verifica se ci sono cambiamenti
if [[ -z $(git status --porcelain) ]]; then
    echo "ℹ️ Nessun cambiamento da salvare."
    # Comunque proviamo un push per sicurezza nel caso ci siano commit locali non pushati
    git push --force origin main 2>&1 | sed "s/$TOKEN/**********/g"
    exit 0
fi

echo "📁 Aggiunta file (filtrati da .gitignore)..."
git add .

echo "💾 Creazione commit..."
git commit -m "Backup $(date +%Y-%m-%d)"

echo "🚀 Push su GitHub..."
git push --force origin main 2>&1 | sed "s/$TOKEN/**********/g"
