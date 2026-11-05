#!/usr/bin/env bash
set -euo pipefail

# Verifica che siano stati forniti gli argomenti
if [[ $# -lt 4 ]]; then
    echo "Usage: $0 <directory_base> <nome_file> <descrizione> <output_type>"
    echo "Esempio: $0 /home/user/fancoil_config my_fancoil_config 'Configurazione completa fancoil' zip"
    echo "output_type può essere 'txt' o 'zip'"
    echo "<directory_base> non deve avere lo slash finale"
    exit 1
fi

# Directory base dei file sorgenti (presa dall'input)
BASE_DIR="$1"

# Nome personalizzato per il file (secondo parametro)
FILE_NAME="$2"

# Descrizione (terzo parametro)
DESCRIPTION="$3"

# Tipo di output (quarto parametro: 'txt' o 'zip')
OUTPUT_TYPE="$4"

# Estrae il nome della directory dalla base
DIR_NAME=$(echo "$BASE_DIR" | awk -F'/' '{print $NF}')

# Se non trova il nome della directory, usa "unknown"
if [[ -z "$DIR_NAME" ]]; then
    DIR_NAME="unknown"
    echo "Attenzione: nome directory non trovato nel percorso, uso '$DIR_NAME'" >&2
fi

# Cartella di destinazione
DEST_DIR="${BASE_DIR}/../temp/for_IA"

# --- Definizione di tutti i file sorgenti ---
# File sorgenti principali
SRC1="${BASE_DIR}/generated_automations/cucina_automation.yaml"
SRC2="${BASE_DIR}/generated_climates/cucina.yaml"

# File aggiuntivi per il controllo completo dei fancoil
SRC3="${BASE_DIR}/input_boolean/generated_input_booleans.yaml"
SRC4="${BASE_DIR}/input_number/generated_input_numbers.yaml"
SRC5="${BASE_DIR}/generated_climates/generated_master_climate.yaml"

# File di configurazione e template
SRC6="${BASE_DIR}/fancoil_vars.yaml"
SRC7="${BASE_DIR}/templates/fancoil_climate.j2"
SRC8="${BASE_DIR}/templates/fancoil_automation.j2"
SRC9="${BASE_DIR}/templates/fancoil_room_input_booleans.j2"
SRC10="${BASE_DIR}/templates/fancoil_room_input_numbers.j2"
SRC11="${BASE_DIR}/templates/fancoil_master_input_numbers.j2"
SRC12="${BASE_DIR}/templates/fancoil_master_climate.j2"

# File di logging e script Python
SRC16="${BASE_DIR}/generator.log"
SRC17="${BASE_DIR}/generate_fancoil_climates.py"

SRC18="${BASE_DIR}/input_number/input_numbers.yaml"
SRC19="${BASE_DIR}/../configuration.yaml"
SRC20="${BASE_DIR}/generated_dashboards/generated_riscaldamento_dashboard.yaml"

# --- Raccoglie tutti i file in un array e verifica l'esistenza ---
declare -a ALL_SOURCE_FILES=(
    "$SRC1" "$SRC2" "$SRC3" "$SRC4" "$SRC5" "$SRC6" "$SRC7" "$SRC8" "$SRC9" "$SRC10"
    "$SRC11" "$SRC12" "$SRC13" "$SRC14" "$SRC15" "$SRC16" "$SRC17" "$SRC18" "$SRC19" "$SRC20"
)

declare -a EXISTING_SOURCE_FILES=()
declare -a MAIN_SOURCE_FILES=("$SRC1" "$SRC2")

for f in "${ALL_SOURCE_FILES[@]}"; do
    if [[ -f "$f" ]]; then
        EXISTING_SOURCE_FILES+=("$f")
    else
        # Verifica se è un file sorgente principale e in tal caso esci con errore
        for main_f in "${MAIN_SOURCE_FILES[@]}"; do
            if [[ "$f" == "$main_f" ]]; then
                echo "Errore: file sorgente principale non trovato: $f" >&2
                exit 1
            fi
        done
        echo "Warning: file aggiuntivo non trovato: $f" >&2
    fi
done

# Crea la cartella di destinazione
mkdir -p "$DEST_DIR"

# Timestamp nel formato YYYYMMDDHHMM
TS="$(date +"%Y%m%d%H%M")"

# --- Logica condizionale per TXT o ZIP ---
if [[ "$OUTPUT_TYPE" == "txt" ]]; then
    OUT_FILE="$DEST_DIR/${TS}_${DIR_NAME}_${FILE_NAME}.txt"

    # Scrive i contenuti con il nome del file all'inizio (come commento YAML)
    {
        # Intestazione con descrizione
        printf "# Descrizione: %s\n" "$DESCRIPTION"
        printf "# Directory: %s\n" "$BASE_DIR"
        printf "# Data generazione: %s\n\n" "$(date)"

        for f in "${EXISTING_SOURCE_FILES[@]}"; do
            printf "# File: %s\n" "$f"
            if [[ "$f" == "$SRC16" ]]; then # generator.log
                tail -50 "$f"
                printf "\n[...solo ultime 50 righe]\n"
            else
                cat "$f"
            fi
            printf "\n"
        done
    } > "$OUT_FILE"
    echo "Creato: $OUT_FILE"

elif [[ "$OUTPUT_TYPE" == "zip" ]]; then
    # Verifica se il comando 'zip' è disponibile
    if ! command -v zip &> /dev/null;
     then
        echo "Errore: il comando 'zip' non è stato trovato. Assicurati che sia installato." >&2
        exit 1
    fi

    OUT_FILE_ZIP="$DEST_DIR/${TS}_${DIR_NAME}_${FILE_NAME}.zip"

    # Crea un file temporaneo con la lista dei file da zippare
    TEMP_FILE_LIST=$(mktemp)
    for f in "${EXISTING_SOURCE_FILES[@]}"; do
        # Rimuove il prefisso BASE_DIR per avere percorsi relativi all'interno dello zip
        echo "${f#$BASE_DIR/}" >> "$TEMP_FILE_LIST"
    done

    # Comprime i file mantenendo la struttura relativa a BASE_DIR
    # cd nella BASE_DIR per zippare i file con percorsi relativi corretti
    (cd "$BASE_DIR" && zip -r "$OUT_FILE_ZIP" -@ < "$TEMP_FILE_LIST")

    # Rimuove il file temporaneo
    rm "$TEMP_FILE_LIST"

    echo "Creato: $OUT_FILE_ZIP"

else
    echo "Errore: tipo di output non valido. Usa 'txt' o 'zip'." >&2
    exit 1
fi
