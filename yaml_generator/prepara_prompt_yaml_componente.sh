#!/usr/bin/env bash
set -euo pipefail

# Verifica che siano stati forniti gli argomenti
if [[ $# -lt 2 ]]; then
    echo "Usage: $0 <directory_base> <nome_file>"
    echo "Esempio: $0 /usr/share/hassio/homeassistant/custom_components/azure_openai_sdk_conversation my_custom_name"
    exit 1
fi

# Directory base dei file sorgenti (presa dall'input)
BASE_DIR="$1"

# Nome personalizzato per il file (secondo parametro)
FILE_NAME="$2"

# Estrae il nome della directory prima di "azure_openai_sdk_conversation"
DIR_NAME=$(echo "$BASE_DIR" | awk -F'/azure_openai_sdk_conversation' '{print $1}' | awk -F'/' '{print $NF}')

# Se non trova il nome della directory, usa "unknown"
if [[ -z "$DIR_NAME" ]]; then
    DIR_NAME="unknown"
    echo "Attenzione: nome directory non trovato nel percorso, uso '$DIR_NAME'" >&2
fi

# Cartella di destinazione
DEST_DIR="/usr/share/hassio/homeassistant/temp/for_IA"

# Crea la cartella di destinazione
mkdir -p "$DEST_DIR"

# Timestamp nel formato YYYYMMDDHHMM
TS="$(date +"%Y%m%d%H%M")"

# Percorso del file di output
OUT_FILE="$DEST_DIR/${TS}_${DIR_NAME}_${FILE_NAME}.txt"

# Trova tutti i file .py e .json nella cartella sorgente (ricorsivamente)
FILES=$(find "$BASE_DIR" -type f \( -name "*.py" -o -name "*.json" \) | sort)

# Se non trova file, esce
if [[ -z "$FILES" ]]; then
    echo "Nessun file .py o .json trovato in $BASE_DIR" >&2
    exit 1
fi

# Scrive i contenuti con il nome del file all'inizio
{
    for f in $FILES; do
        printf "# File: %s\n" "$f"
        cat "$f"
        printf "\n"
    done
} > "$OUT_FILE"

echo "Creato: $OUT_FILE"