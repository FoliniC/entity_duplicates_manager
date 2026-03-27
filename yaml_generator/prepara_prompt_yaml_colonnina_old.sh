#!/usr/bin/env python3
import sys
import os
from datetime import datetime
from pathlib import Path

def main():
    # Verifica argomenti
    if len(sys.argv) < 4:
        SCRIPT_NAME = os.path.basename(sys.argv[0])
        print(f"Usage: python3 {SCRIPT_NAME} <directory_base> <nome_file> <descrizione>")
        print(f"Esempio: python3 {SCRIPT_NAME} /usr/share/hassio/homeassistant/ Colonnina 'Configurazione colonnina'")
        sys.exit(1)
    
    # Parametri
    BASE_DIR = sys.argv[1]
    FILE_NAME = sys.argv[2]
    DESCRIPTION = sys.argv[3]
    
    # Estrae il nome della directory dalla base
    DIR_NAME = os.path.basename(BASE_DIR.rstrip('/'))
    if not DIR_NAME:
        DIR_NAME = "unknown"
        print("Attenzione: nome directory non trovato nel percorso, uso 'unknown'", file=sys.stderr)
    
    # Cartella di destinazione
    DEST_DIR = os.path.join(BASE_DIR, "temp/for_IA")
    
    # DEFINISCI QUI TUTTE LE VARIABILI SRC CHE VUOI UTILIZZARE
    # Aggiungi o rimuovi variabili secondo le tue necessità
    SRC_VARIABLES = {
        'SRC1': "configuration.yaml",
        'SRC2': "managed_sensors/template_sensors_static.yaml", 
        'SRC3': "yaml_generator/generated_automations/automations_not_generated_keep_it.yaml",
    }
    
    print(f"Trovate {len(SRC_VARIABLES)} variabili SRC:")
    for src_name, src_value in SRC_VARIABLES.items():
        print(f"  {src_name}: {src_value}")
    
    # Verifica esistenza sorgenti principali (SRC1 e SRC2 obbligatorie)
    for src_name in ['SRC1', 'SRC2']:
        src_path = os.path.join(BASE_DIR, SRC_VARIABLES[src_name])
        if not os.path.isfile(src_path):
            print(f"Errore: file sorgente principale non trovato: {src_path}", file=sys.stderr)
            sys.exit(1)
    
    # Crea la cartella di destinazione
    Path(DEST_DIR).mkdir(parents=True, exist_ok=True)
    
    # Timestamp
    TS = datetime.now().strftime("%Y%m%d%H%M")
    
    # Percorso del file di output
    OUT_FILE = os.path.join(DEST_DIR, f"{TS}_{DIR_NAME}_{FILE_NAME}.txt")
    
    # Scrive i contenuti
    with open(OUT_FILE, 'w', encoding='utf-8') as out_f:
        # Intestazione con descrizione
        out_f.write(f"# Descrizione: {DESCRIPTION}\n")
        out_f.write(f"# Directory: {BASE_DIR}\n")
        out_f.write(f"# Data generazione: {datetime.now()}\n")
        out_f.write(f"# File inclusi: {', '.join(SRC_VARIABLES.keys())}\n\n")
        
        # Processa tutte le variabili SRC in ordine
        for src_name, src_rel_path in SRC_VARIABLES.items():
            src_full_path = os.path.join(BASE_DIR, src_rel_path)
            
            out_f.write(f"# File: {src_name} -> {src_full_path}\n")
            
            if os.path.isfile(src_full_path):
                try:
                    with open(src_full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        out_f.write(content)
                        if not content.endswith('\n'):
                            out_f.write('\n')
                except Exception as e:
                    out_f.write(f"# Errore nella lettura del file: {e}\n")
            else:
                out_f.write(f"# File non trovato\n")
            
            out_f.write("\n")
    
    print(f"Creato: {OUT_FILE}")
    print(f"File processati: {len(SRC_VARIABLES)}")

if __name__ == "__main__":
    main()