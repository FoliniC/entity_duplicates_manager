#!/bin/bash
# Configurazione percorso
CONFIG_DIR="/home/carlo/docker/homeassistant/config"

cd "$CONFIG_DIR" || exit 1

export GIT_SSH_COMMAND="ssh -i /root/.ssh/id_rsa -o StrictHostKeyChecking=no"
git remote set-url origin git@github.com:FoliniC/ha-config.git

echo "=== BACKUP IN CORSO: $(date) ==="
echo "Repository: $(pwd)"
echo ""

# FASE 0: VERIFICA STATO PRE-ESISTENTE
echo "🔍 Verifica stato repository..."
# Fetch per assicurarsi che lo stato remoto sia aggiornato
git fetch origin main >/dev/null 2>&1

HAS_UNPUSHED_COMMITS=$(git log --oneline origin/main..main 2>/dev/null | wc -l)
HAS_STAGED_CHANGES=$(git diff --cached --name-only | wc -l)
HAS_UNSTAGED_CHANGES=$(git diff --name-only | wc -l)

if [ $HAS_UNPUSHED_COMMITS -gt 0 ]; then
    echo "ℹ️  Trovati $HAS_UNPUSHED_COMMITS commit locali non pushati"
    git --no-pager log --oneline origin/main..main
    echo ""
fi

if [ $HAS_STAGED_CHANGES -gt 0 ]; then
    echo "ℹ️  Trovati $HAS_STAGED_CHANGES file nello staging area"
    git diff --cached --name-only | while read file; do
        if [ -f "$file" ]; then
            size=$(du -h "$file" 2>/dev/null | cut -f1 || echo "?")
            echo "  📁 $size - $file"
        fi
    done
    echo ""
fi

# FASE 1: AGGIUNTA SOLO SE CI SONO MODIFICHE NON STAGED
if [ $HAS_UNSTAGED_CHANGES -gt 0 ]; then
    echo "📁 File da aggiungere:"
    git status --porcelain | grep -v "^D" | while read status file; do
        if [ -f "$file" ]; then
            size=$(du -h "$file" 2>/dev/null | cut -f1 || echo "?")
            echo "  $status $size $file"
        else
            echo "  $status $file"
        fi
    done

    echo ""
    echo "🗂️  Aggiunta file..."
    git add .
else
    echo "ℹ️  Nessun file nuovo da aggiungere"
fi

# FASE 2: COMMIT (solo se necessario)
if [ $HAS_UNSTAGED_CHANGES -gt 0 ] || [ $HAS_STAGED_CHANGES -gt 0 ]; then
    echo ""
    echo "💾 Creazione commit..."
    git -c "user.name=HA Backup" -c "user.email=ha@$(hostname)" commit -m "Backup $(date +'%Y-%m-%d %H:%M')"
    COMMIT_RESULT=$?

    if [ $COMMIT_RESULT -ne 0 ]; then
        echo "ℹ️  Nessun cambiamento da committare"
    fi
else
    echo "ℹ️  Nessun cambiamento da committare"
fi

# FASE 3: PUSH (sempre, se ci sono commit locali)
HAS_UNPUSHED_COMMITS_AFTER=$(git log --oneline origin/main..main 2>/dev/null | wc -l)

if [ $HAS_UNPUSHED_COMMITS_AFTER -gt 0 ]; then
    echo ""
    echo "🚀 Upload su GitHub ($HAS_UNPUSHED_COMMITS_AFTER commit da pushare)..."

    # Push
    git push --progress origin main 2>&1 | while read line; do
        case "$line" in
            *Compressing*|*Compressione*) echo "  🗜️  $line" ;;
            *Writing*|*Writing*|*Ricezione*|*Invio*) echo "  📤 $line" ;;
            *objects*|*oggetti*) echo "  📊 $line" ;;
            *done*|*fatto*) echo "  ✅ $line" ;;
            *error*|*fatal*) echo "  ❗ $line" ;;
            *%) echo "  📈 $line" ;;
            *To*) echo "  🌐 $line" ;;
            *) echo "  🔄 $line" ;;
        esac
    done

    PUSH_EXIT_CODE=${PIPESTATUS[0]}

    if [ $PUSH_EXIT_CODE -eq 0 ]; then
        echo "✅ Backup completato: $(date +'%H:%M:%S')"
    else
        echo "❌ Errore durante il push (exit code: $PUSH_EXIT_CODE)"
        echo "💡 Prova con: git push --force-with-lease origin main"
    fi
else
    echo "✅ Nessun commit da pushare - repository sincronizzato"
fi
