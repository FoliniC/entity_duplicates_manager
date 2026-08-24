#!/bin/bash
# Configurazione percorso
CONFIG_DIR="/home/carlo/docker/homeassistant/config"
HOST_COMPOSE_SOURCE="/home/carlo/docker/docker-compose.yml"
HOST_BACKUP_DIR="$CONFIG_DIR/host_backup"
HOST_COMPOSE_BACKUP="$HOST_BACKUP_DIR/docker-compose.yml"

# Backup separati dei database: il backup nativo di Home Assistant non include
# MariaDB/InfluxDB quando sono volumi Docker esterni a /config.
HA_STORAGE_DIR="${HA_STORAGE_DIR:-/media/carlo/ha_storage}"
DB_BACKUP_ROOT="${DB_BACKUP_ROOT:-$HA_STORAGE_DIR/backups/databases}"
INFLUX_CONTAINER_BACKUP_ROOT="/var/lib/influxdb2/ha_backups"

cd "$CONFIG_DIR" || exit 1

export GIT_SSH_COMMAND="ssh -i /home/carlo/.ssh/id_rsa -o StrictHostKeyChecking=no -o IdentitiesOnly=yes"
git remote set-url origin git@github.com:FoliniC/ha-config.git

echo "=== BACKUP IN CORSO: $(date) ==="
echo "Repository: $(pwd)"
echo ""

# FASE -2: BACKUP CONSISTENTE DEI DATABASE ESTERNI
# I dump restano sul disco ha_storage e non vengono mai aggiunti al repository Git.
backup_databases() {
    local timestamp maria_dir maria_tmp maria_final influx_host_dir influx_container_dir
    timestamp=$(date +'%Y-%m-%d_%H-%M-%S')
    maria_dir="$DB_BACKUP_ROOT/mariadb"
    influx_host_dir="$HA_STORAGE_DIR/influxdb/data/ha_backups"
    influx_container_dir="$INFLUX_CONTAINER_BACKUP_ROOT/influxdb_$timestamp"
    maria_tmp="$maria_dir/homeassistant_$timestamp.sql.gz.partial"
    maria_final="$maria_dir/homeassistant_$timestamp.sql.gz"

    echo "🗄️  Verifica disco dati HA: $HA_STORAGE_DIR"
    if ! findmnt -T "$HA_STORAGE_DIR" >/dev/null 2>&1; then
        echo "❌ ha_storage non è montato: backup DB annullato"
        return 1
    fi
    if ! docker inspect -f '{{.State.Running}}' mariadb 2>/dev/null | grep -qx true; then
        echo "❌ Container MariaDB non in esecuzione"
        return 1
    fi
    if ! docker inspect -f '{{.State.Running}}' influxdb 2>/dev/null | grep -qx true; then
        echo "❌ Container InfluxDB non in esecuzione"
        return 1
    fi

    mkdir -p "$maria_dir" || return 1
    echo "🗄️  Dump consistente MariaDB → $maria_final"
    # La password rimane nell'environment del container, non viene scritta sul disco.
    set -o pipefail
    docker exec mariadb sh -c 'exec mariadb-dump --single-transaction --quick --routines --events --triggers --databases homeassistant -uhomeassistant -p"$MYSQL_PASSWORD"' \
        | gzip -1 > "$maria_tmp"
    local pipe_status=("${PIPESTATUS[@]}")
    local dump_status=${pipe_status[0]}
    local gzip_status=${pipe_status[1]}
    if [ "$dump_status" -ne 0 ] || [ "$gzip_status" -ne 0 ] || [ ! -s "$maria_tmp" ]; then
        rm -f "$maria_tmp"
        echo "❌ Dump MariaDB fallito (mariadb=$dump_status gzip=$gzip_status)"
        return 1
    fi
    mv "$maria_tmp" "$maria_final" || return 1

    echo "📈 Backup logico InfluxDB → $influx_host_dir"
    # Il token rimane in secrets.yaml e viene passato solo nell'environment
    # temporaneo del container; non viene scritto nell'archivio né nel Git repo.
    local influx_token
    influx_token="${INFLUX_BACKUP_TOKEN:-}"
    if [ -z "$influx_token" ]; then
        influx_token=$(python3 - "$CONFIG_DIR/secrets.yaml" <<'PY'
import sys
from pathlib import Path
for key in ("influxdb_backup_token:", "influxdb_token:"):
    for line in Path(sys.argv[1]).read_text().splitlines():
        if line.strip().startswith(key):
            print(line.split(":", 1)[1].strip().strip('"\''))
            raise SystemExit(0)
raise SystemExit(1)
PY
) || {
            echo "❌ Token InfluxDB per backup non trovato (usa INFLUX_BACKUP_TOKEN o influxdb_backup_token in secrets.yaml)"
            return 1
        }
    fi
    # /var/lib/influxdb2 è già un bind mount verso ha_storage: nessun dato passa
    # dal layer Docker o dal disco di sistema.
    if ! docker exec -e INFLUX_TOKEN="$influx_token" -e INFLUX_BACKUP_PATH="$influx_container_dir" influxdb sh -c 'rm -rf "$INFLUX_BACKUP_PATH" && mkdir -p "$INFLUX_BACKUP_PATH" && influx backup --host http://localhost:8086 --token "$INFLUX_TOKEN" --compression gzip "$INFLUX_BACKUP_PATH"'; then
        docker exec influxdb sh -c "rm -rf '$influx_container_dir'" >/dev/null 2>&1 || true
        echo "❌ Backup InfluxDB fallito"
        return 1
    fi

    printf 'created_at=%s\nmariadb_dump=%s\ninflux_backup=%s\n' \
        "$(date --iso-8601=seconds)" "$maria_final" "$influx_host_dir/influxdb_$timestamp" \
        > "$DB_BACKUP_ROOT/backup_$timestamp.manifest"
    echo "✅ Database salvati su ha_storage"
    du -sh "$maria_final" "$influx_host_dir/influxdb_$timestamp"
}

DB_BACKUP_FAILED=0
backup_databases || DB_BACKUP_FAILED=1

# Modalità di verifica: esegue solo i backup DB e non modifica il repository Git.
if [ "${DB_BACKUP_ONLY:-0}" = "1" ]; then
    exit "$DB_BACKUP_FAILED"
fi

echo ""

# FASE -1: SNAPSHOT CONFIG HOST
# Il docker-compose principale vive fuori dal repository HA. Ne salviamo una
# copia sanitizzata dentro il repo prima del git add, evitando token/password.
if [ -f "$HOST_COMPOSE_SOURCE" ]; then
    mkdir -p "$HOST_BACKUP_DIR"
    sed -E \
        -e 's/(TOKEN=).*/\1<redacted>/' \
        -e 's/(AUTHTOKEN=).*/\1<redacted>/' \
        -e 's/(PASSWORD=).*/\1<redacted>/' \
        -e 's/(MYSQL_ROOT_PASSWORD=).*/\1<redacted>/' \
        -e 's/(POSTGRES_PASSWORD=).*/\1<redacted>/' \
        -e 's/(POSTGRESQL_PASSWORD=).*/\1<redacted>/' \
        -e 's/(--token )[A-Za-z0-9._=-]+/\1<redacted>/' \
        -e 's/(command: -u "[^;"]+;)[^;"]+/\1<redacted>/' \
        "$HOST_COMPOSE_SOURCE" > "$HOST_COMPOSE_BACKUP"
    echo "📦 Snapshot compose host aggiornato: $HOST_COMPOSE_BACKUP"
else
    echo "⚠️  Compose host non trovato: $HOST_COMPOSE_SOURCE"
fi
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

if [ "$DB_BACKUP_FAILED" -ne 0 ]; then
    echo "❌ Backup Git completato, ma il backup dei database è fallito"
    exit 1
fi
