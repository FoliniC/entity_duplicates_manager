#!/usr/bin/env python3
import sys
import os
import re
import yaml
from datetime import datetime
from pathlib import Path

def remove_comments_and_empty_lines(text):
    """Rimuove commenti e righe vuote dal testo YAML"""
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Rimuove commenti (ma non # dentro stringhe)
        if '#' in line:
            # Semplice rimozione: tutto da # in poi
            line = line.split('#')[0]
        
        # Rimuove spazi trailing
        line = line.rstrip()
        
        # Mantieni solo righe non vuote
        if line.strip():
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)

def remove_yaml_sections(content, sections_to_remove):
    """
    Rimuove sezioni specifiche dal YAML.
    sections_to_remove: lista di nomi di sezioni da rimuovere
    """
    lines = content.split('\n')
    filtered_lines = []
    skip = False
    current_indent = 0
    
    for line in lines:
        # Calcola l'indentazione
        indent = len(line) - len(line.lstrip())
        
        # Verifica se è una chiave di primo livello da rimuovere
        match = re.match(r'^(\w+):', line)
        
        if match:
            key = match.group(1)
            if key in sections_to_remove:
                skip = True
                current_indent = indent
                continue
            else:
                skip = False
        
        # Se siamo in una sezione da saltare
        if skip:
            # Se troviamo una riga con indentazione <= della sezione da saltare,
            # è una nuova sezione, quindi riprendiamo
            if line.strip() and indent <= current_indent:
                skip = False
                # Controlla se questa riga è una nuova chiave da rimuovere
                match = re.match(r'^(\w+):', line)
                if match and match.group(1) in sections_to_remove:
                    current_indent = indent
                    continue
                filtered_lines.append(line)
        else:
            if not skip:
                filtered_lines.append(line)
    
    return '\n'.join(filtered_lines)

def process_yaml_file(file_path, sections_to_remove):
    """Processa un file YAML: rimuove commenti e sezioni"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Rimuove commenti e righe vuote
        content = remove_comments_and_empty_lines(content)
        
        # Rimuove sezioni specifiche
        content = remove_yaml_sections(content, sections_to_remove)
        
        return content
    except Exception as e:
        return f"# Errore nel processamento: {e}\n"

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
    
    # Sezioni YAML da rimuovere (solo per configuration.yaml)
    SECTIONS_TO_REMOVE = ['conversation', 'intent_script', 'light', 'knx', 'modbus', 'scheduler']
    
    # DEFINISCI QUI TUTTE LE VARIABILI SRC CHE VUOI UTILIZZARE
    # File del progetto EV Charging Control
    SRC_VARIABLES = {
        'SRC1': "configuration.yaml",
        'SRC2': "yaml_generator/managed_sensors/template_sensors_static.yaml", 
        'SRC3': "yaml_generator/generated_automations/automations_not_generated_keep_it.yaml",
        'SRC4': "yaml_generator/input_boolean/ev_charging_control.yaml",
        'SRC5': "yaml_generator/input_datetime/ev_charging_control.yaml",
        'SRC6': "yaml_generator/input_buttons/ev_charging_control.yaml",
        'SRC7': "yaml_generator/input_number/ev_charging_control.yaml",
        'SRC8': "yaml_generator/input_select/ev_charging_control.yaml",
        'SRC9': "yaml_generator/generated_automations/ev_charging_control.yaml",
        'SRC10': "yaml_generator/managed_sensors/template_sensors_ev_charging.yaml",
        'SRC11': "ui/charge_control.yaml"
    }
    
    print(f"Trovate {len(SRC_VARIABLES)} variabili SRC:")
    for src_name, src_value in SRC_VARIABLES.items():
        print(f"  {src_name}: {src_value}")
    
    print(f"\nSezioni da rimuovere: {', '.join(SECTIONS_TO_REMOVE)}")
    
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
                    # Applica il processamento YAML solo a configuration.yaml
                    if src_name == 'SRC1':
                        content = process_yaml_file(src_full_path, SECTIONS_TO_REMOVE)
                    else:
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
    
    print(f"\nCreato: {OUT_FILE}")
    print(f"File processati: {len(SRC_VARIABLES)}")

if __name__ == "__main__":
    main()