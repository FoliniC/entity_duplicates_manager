import sys
import os
import re
import yaml
from datetime import datetime
from pathlib import Path
import shutil
import glob

# --- CONFIGURAZIONE GLOBALE ---
# Encoding di default per lettura e scrittura
TARGET_ENCODING = 'utf-8'
# Newline di default per l'output (Windows)
TARGET_NEWLINE = '\r\n'

def ask_with_default(msg, default_value):
    # Funzione standard per input con default
    user_input = input(f"{msg} [{default_value}]: ").strip()
    return user_input if user_input else default_value


def ask_filename_with_default(msg, default_value):
    # Funzione speciale per il nome del file che permette di aggiungere testo
    user_input = input(f"{msg} [{default_value}]: ").strip()
    
    if not user_input:
        return default_value
    elif user_input.startswith('-'):
        # Se inizia con dash, usa il valore inserito come nome completo
        return user_input[1:].strip()
    else:
        # Altrimenti aggiungi il testo al valore predefinito
        return f"{default_value}_{user_input}"


def remove_comments_and_empty_lines(text):
    """Rimuove commenti e righe vuote dal testo YAML"""
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        if '#' in line:
            line = line.split('#')[0]
        line = line.rstrip()
        if line.strip():
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)


def remove_yaml_sections(content, sections_to_remove):
    """Rimuove sezioni specifiche dal YAML"""
    lines = content.split('\n')
    filtered_lines = []
    skip = False
    current_indent = -1
    
    for line in lines:
        indent = len(line) - len(line.lstrip())
        
        if not line.strip() or line.strip().startswith('#'):
            if not skip:
                filtered_lines.append(line)
            continue

        if skip:
            if indent <= current_indent:
                skip = False
                current_indent = -1
            else:
                continue
        
        if not skip:
            match = re.match(r'^(\s*)(\w+):', line)
            if match:
                key = match.group(2)
                if key in sections_to_remove:
                    print(f"Rimossa sezione {key}")

                    skip = True
                    current_indent = indent
                    continue
        
        if not skip:
            filtered_lines.append(line)
    
    return '\n'.join(filtered_lines)


def normalize_newlines(text, target_newline=TARGET_NEWLINE):
    """
    Normalizza i newline del testo al formato target.
    Gestisce input misti (\n, \r\n, \r).
    """
    if not text:
        return text
    # Primo step: uniforma tutto a \n
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    # Secondo step: converte al target
    if target_newline != '\n':
        text = text.replace('\n', target_newline)
    return text


def process_file(file_path, config, base_dir):
    """
    Processa un singolo file e restituisce il contenuto e un booleano 
    che indica se il file originale terminava con newline.
    """
    content = ""
    has_final_newline = True # Default safe
    
    try:
        # Leggiamo in binario per rilevare esattamente la fine del file
        with open(file_path, 'rb') as f:
            raw_content = f.read()
            
        if not raw_content:
            return "", False

        # Verifica se l'ultimo byte è un newline
        if raw_content:
            has_final_newline = raw_content.endswith(b'\n') or raw_content.endswith(b'\r')

        # Decodifica
        try:
            content = raw_content.decode('utf-8')
        except UnicodeDecodeError:
            # Fallback se non è utf-8 (opzionale, o lancia errore)
            content = raw_content.decode('latin-1') 
        
        if config.get('process_yaml'):
            # Nota: processare il YAML potrebbe cambiare la struttura dei newline.
            # Se si processa, assumiamo standard newline alla fine.
            if config.get('sections_to_remove'):
                content = remove_yaml_sections(content, config['sections_to_remove'])
            # Dopo il processing, normalizziamo per coerenza interna
            has_final_newline = True 
        
        if config.get('tail_lines'):
            lines = content.splitlines()
            content = '\n'.join(lines[-config['tail_lines']:]).strip() # strip rimuove newline finali
            if len(lines) > config['tail_lines']:
                content = f"[...solo ultime {config['tail_lines']} righe]\n" + content
            has_final_newline = True # Tail lines mode di solito produce output pulito

    except Exception as e:
        content = f"# Errore nel processamento di {file_path}: {e}\n"
        print(f"ERRORE: Impossibile processare {file_path}: {e}")
        
    return content, has_final_newline

def write_extracted_file(base_dest_dir, relative_file_path, content_lines, no_newline_at_eof=False):
    """
    Scrive un file estratto applicando la codifica e i newline target,
    rispettando l'indicazione di fine file originale.
    """
    full_dest_path = Path(base_dest_dir) / relative_file_path
    full_dest_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Ricostruisce il contenuto unendo le linee con \n standard per elaborazione
        # content_lines contiene le righe lette dal file TXT (che includono i newline del TXT stesso)
        # Dobbiamo pulirle per rigenerare il file con i newline target corretti.
        
        clean_lines = [line.rstrip('\r\n') for line in content_lines]
        full_text = '\n'.join(clean_lines)
        
        # Aggiunge newline finale se il file TXT wrapper lo prevedeva logicamente,
        # a meno che non sia specificato il flag NO_NEWLINE_AT_EOF
        if not no_newline_at_eof:
             full_text += '\n'

        # Normalizza ai newline desiderati (es. Windows CRLF)
        final_content = normalize_newlines(full_text, TARGET_NEWLINE)

        # Scrive il file in modalità binaria o testo con newline='' per controllo totale
        with open(full_dest_path, 'w', encoding=TARGET_ENCODING, newline='') as out_f:
            out_f.write(final_content)
        
        # Debug
        suffix_debug = " [NO EOF NL]" if no_newline_at_eof else ""
        print(f"Creato: {full_dest_path}{suffix_debug}")
            
    except Exception as e:
        print(f"ERRORE: Impossibile creare {full_dest_path}: {e}")
        
def unpack_from_txt(txt_file_path, dest_dir):
    """Estrae file da un file TXT interpretando i flag di newline"""
    print(f"Estrazione file da {txt_file_path} a {dest_dir}...")
    current_file_path = None
    current_file_content = []
    current_no_newline_eof = False
    
    dest_path_obj = Path(dest_dir)
    dest_path_obj.mkdir(parents=True, exist_ok=True)

    try:
        with open(txt_file_path, 'r', encoding=TARGET_ENCODING) as f:
            for line in f:
                # Controlla header inizio file
                file_header_match = re.match(r'^# --- File: (.*?) ---$', line.strip())
                
                # Controlla flag speciale NO NEWLINE (inserito alla fine del blocco file)
                if line.strip() == "# NO_NEWLINE_AT_EOF":
                    current_no_newline_eof = True
                    continue

                if file_header_match:
                    # Se c'era un file precedente aperto, scrivilo
                    if current_file_path is not None:
                        # Rimuovi eventuali righe vuote finali che separano i file nel TXT wrapper
                        # (la logica di packing aggiunge \n\n tra i file, dobbiamo ignorarli nel contenuto)
                        while current_file_content and not current_file_content[-1].strip():
                            current_file_content.pop()
                            
                        write_extracted_file(dest_dir, current_file_path, current_file_content, current_no_newline_eof)
                    
                    # Reset per nuovo file
                    current_file_path = file_header_match.group(1).strip()
                    current_file_content = []
                    current_no_newline_eof = False # Reset flag
                elif current_file_path is not None:
                    current_file_content.append(line)
        
        # Scrivi l'ultimo file
        if current_file_path is not None:
            # Pulizia code vuote del wrapper
            while current_file_content and not current_file_content[-1].strip():
                current_file_content.pop()
            write_extracted_file(dest_dir, current_file_path, current_file_content, current_no_newline_eof)
        
        print("Estrazione completata.")
        
    except FileNotFoundError:
        print(f"Errore: file .txt non trovato: {txt_file_path}", file=sys.stderr)
    except Exception as e:
        print(f"Errore durante l'estrazione: {e}", file=sys.stderr)

def create_zip_archive(temp_zip_dir, zip_file_path, verbose=False):
    """Crea l'archivio ZIP e gestisce gli errori"""
    try:
        if verbose:
            print(f"\n=== VERIFICA STRUTTURA ZIP ===")
            total_files = 0
            total_size = 0
            
            for root, dirs, files in os.walk(temp_zip_dir):
                for file in files:
                    file_path = Path(root) / file
                    rel_path = file_path.relative_to(temp_zip_dir)
                    file_size = file_path.stat().st_size
                    total_size += file_size
                    total_files += 1
                    print(f"  📁 {rel_path} ({file_size} bytes)")
            
            print(f"=== RIEPILOGO: {total_files} file, {total_size} bytes totali ===")
        
        shutil.make_archive(str(zip_file_path.with_suffix('')), 'zip', str(temp_zip_dir))
        print(f"✅ Creato archivio ZIP: {zip_file_path}")
        return True
    except Exception as e:
        print(f"❌ ERRORE nella creazione dell'archivio ZIP: {e}")
        return False


def copy_file_to_zip_structure(source_file, target_file, file_cfg, base_dir, verbose=False):
    """Copia un file nella struttura ZIP con processing e normalizzazione"""
    try:
        if verbose:
            print(f"  DEBUG: Copia {source_file} -> {target_file}")
        
        # Crea la directory di destinazione
        target_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Processa il contenuto del file
        processed_content, _ = process_file(str(source_file), file_cfg, base_dir)
        
        # Normalizza newline per lo ZIP (Windows standard)
        processed_content = normalize_newlines(processed_content, TARGET_NEWLINE)

        # Scrivi il contenuto processato
        with open(target_file, 'w', encoding=TARGET_ENCODING, newline='') as f:
            f.write(processed_content)
            
        return True
        
    except Exception as e:
        print(f"❌ ERRORE nella copia di {source_file} -> {target_file}: {e}")
        return False



def clean_path_for_zip(file_path_rel):
    """Pulisce il percorso del file per lo ZIP"""
    normalized_path = file_path_rel.replace('\\', '/')
    if len(normalized_path) >= 2 and normalized_path[1] == ':' and normalized_path[0].isalpha():
        normalized_path = normalized_path[2:]
    while normalized_path.startswith('/'):
        normalized_path = normalized_path[1:]
    path = Path(normalized_path)
    parts = list(path.parts)
    while parts and parts[0] == '..':
        parts.pop(0)
    clean_path = Path(*parts) if parts else Path(normalized_path)
    return clean_path

def format_filename(task_name):
    """Formatta il nome del file in minuscolo con underscore"""
    formatted = task_name.lower().replace(' ', '_')
    formatted = re.sub(r'[^a-z0-9_]', '', formatted)
    formatted = re.sub(r'_+', '_', formatted)
    formatted = formatted.strip('_')
    return formatted


def get_base_directory(config, script_dir):
    """Determina la directory base per i file sorgente"""
    if 'base_dir' in config:
        base_dir = Path(config['base_dir'])
        if not base_dir.is_absolute():
            base_dir = script_dir / base_dir
        
        if not base_dir.exists():
            print(f"❌ Directory base non trovata: {base_dir}")
            print(f"💡 Utilizzo la directory corrente: {script_dir}")
            return script_dir
        
        print(f"📁 Directory base dalla configurazione: {base_dir}")
        return base_dir
    else:
        print(f"📁 Directory base (corrente): {script_dir}")
        return script_dir


def main():
    script_dir = Path(__file__).parent.absolute()
    verbose = "--verbose" in sys.argv or "-v" in sys.argv

    # Handle unpack mode
    if "--unpack" in sys.argv:
        unpack_index = sys.argv.index("--unpack")
        remaining_args = sys.argv[unpack_index + 1:]
        
        if len(remaining_args) == 0:
            print("Modalità interattiva di estrazione avviata.")
            txt_file_path = input("Inserisci il percorso del file .txt da estrarre: ")
            dest_dir = input("Inserisci la cartella di destinazione per i file estratti: ")
            unpack_from_txt(txt_file_path, dest_dir)
        elif len(remaining_args) == 2:
            txt_file_path = remaining_args[0]
            dest_dir = remaining_args[1]
            unpack_from_txt(txt_file_path, dest_dir)
        else:
            print("Usage (unpack): python generate_prompt_package.py --unpack [<txt_file> <dest_dir>]")
            sys.exit(1)
        return

    # Interactive mode for packing
    packing_args = [arg for arg in sys.argv[1:] if arg not in ["--verbose", "-v"]]
    
    if len(packing_args) == 0:
        print("🎯 Modalità interattiva di creazione pacchetto avviata.")
        config_files = glob.glob(os.path.join(script_dir, "config_*.yaml"))
        if not config_files:
            print("Nessun file di configurazione (config_*.yaml) trovato nella directory corrente.")
            sys.exit(1)
        
        print("File di configurazione disponibili:")
        for i, cf in enumerate(config_files):
            print(f"{i+1}. {os.path.basename(cf)}")
        
        config_choice = input("Scegli un numero per il file di configurazione: ")
        try:
            config_file_path = config_files[int(config_choice) - 1]
        except (ValueError, IndexError):
            print("Scelta non valida.")
            sys.exit(1)

        try:
            with open(config_file_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
        except Exception as e:
            print(f"Errore nel caricamento della configurazione: {e}")
            sys.exit(1)
            
        default_output_type = config.get("output_type", "txt")
        default_task_name = config.get("task_name", "output")
        default_output_filename = format_filename(default_task_name)
        default_description_comment = config.get("description", "")
        
        print(f"\n💾 NOME FILE DI OUTPUT")
        print(f"   Valore predefinito: {default_output_filename}")
        output_filename = ask_filename_with_default("Nome del file di output (senza estensione)", default_output_filename)
        
        output_type = ask_with_default("Tipo di output (txt/zip)", default_output_type)
        output_type_lower = output_type.lower()
        while output_type_lower not in ['txt', 'zip']:
            output_type = ask_with_default("Tipo di output non valido. Inserisci 'txt' o 'zip'", default_output_type)
            output_type_lower = output_type.lower()
        
        description_comment = ask_with_default("Commento/descrizione aggiuntiva (opzionale)", default_description_comment)

    elif len(packing_args) == 4:
        # Non-interactive mode
        config_file_path = packing_args[0]
        output_filename = packing_args[1]
        output_type = packing_args[2]
        description_comment = packing_args[3]
        output_type_lower = output_type.lower()
    else:
        print("Usage: python generate_prompt_package.py <config> <out_name> <type> <desc> [--verbose]")
        sys.exit(1)

    # Load configuration
    try:
        with open(config_file_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"Errore config: {e}")
        sys.exit(1)

    task_name = config.get('task_name', 'untitled_task')
    description = config.get('description', 'No description provided.')
    output_dir = config.get('output_dir', 'temp/for_IA')
    base_dir = get_base_directory(config, script_dir)

    # Setup directories
    dest_full_dir = base_dir / output_dir
    dest_full_dir.mkdir(parents=True, exist_ok=True)
    
    ts = datetime.now().strftime("%Y%m%d%H%M")
    output_base_name = f"{ts}_{output_filename}"

    processed_contents = [] # Lista di tuple: (rel_path, content, has_newline)
    temp_zip_dir = None
    files_processed = 0
    files_skipped = 0

    print(f"\n🔄 Elaborazione file in corso... (Encoding: {TARGET_ENCODING}, Newline: {repr(TARGET_NEWLINE)})")

    # --- PROCESSING FILE ---
    for i, file_cfg in enumerate(config.get('files', [])):
        file_path_rel = file_cfg['path']
        full_file_path = Path(file_path_rel) if file_path_rel.startswith('/') else base_dir / file_path_rel

        if verbose:
            print(f"\n--- File {i+1} --- {file_path_rel}")

        if not full_file_path.exists():
            print(f"❌ File non trovato: {full_file_path}")
            files_skipped += 1
            continue

        # Processa per TXT
        content, has_newline = process_file(str(full_file_path), file_cfg, base_dir)
        processed_contents.append((file_path_rel, content, has_newline))
        
        # Gestione ZIP
        if output_type_lower == 'zip':
            if temp_zip_dir is None:
                temp_zip_dir = dest_full_dir / f"temp_zip_{output_base_name}"
                if temp_zip_dir.exists(): shutil.rmtree(temp_zip_dir)
                temp_zip_dir.mkdir(parents=True, exist_ok=True)
            
            clean_rel_path = clean_path_for_zip(file_path_rel)
            zip_target_str = str(clean_rel_path).lstrip('/')
            target_file_path = temp_zip_dir / zip_target_str
            
            if copy_file_to_zip_structure(full_file_path, target_file_path, file_cfg, base_dir, verbose):
                files_processed += 1
            else:
                files_skipped += 1
        else:
            files_processed += 1

    # --- OUTPUT GENERATION ---
    print(f"\n📊 RIEPILOGO: {files_processed} file processati, {files_skipped} file saltati")

    # Generazione TXT
    if output_type_lower == 'txt':
        out_file_path = dest_full_dir / f"{output_base_name}.txt"
        try:
            # Usiamo newline='' per evitare conversioni automatiche di python
            # Scriviamo manualmente i newline corretti
            with open(out_file_path, 'w', encoding=TARGET_ENCODING, newline='') as out_f:
                # Header
                header_text = (
                    f"# Task Name: {task_name}\n"
                    f"# Description: {description}\n"
                    f"# User Comment: {description_comment}\n"
                    f"# Generated On: {datetime.now()}\n\n"
                )
                out_f.write(normalize_newlines(header_text, TARGET_NEWLINE))

                for rel_path, content, has_newline in processed_contents:
                    # File Header
                    f_head = f"# --- File: {rel_path} ---\n"
                    out_f.write(normalize_newlines(f_head, TARGET_NEWLINE))
                    
                    # Contenuto (normalizzato)
                    out_f.write(normalize_newlines(content, TARGET_NEWLINE))
                    
                    # Se il contenuto non finiva con newline, ne aggiungiamo uno per separare
                    # nel file TXT, ma aggiungiamo il flag per il restore
                    if content and not content.endswith('\n'):
                         out_f.write(normalize_newlines('\n', TARGET_NEWLINE))

                    if not has_newline:
                        marker = "# NO_NEWLINE_AT_EOF\n"
                        out_f.write(normalize_newlines(marker, TARGET_NEWLINE))
                    
                    # Spaziatura tra file
                    out_f.write(normalize_newlines("\n\n", TARGET_NEWLINE))
                    
            print(f"✅ Creato file TXT: {out_file_path}")
        except Exception as e:
            print(f"❌ ERRORE nella creazione del file TXT: {e}")

    # Generazione ZIP
    elif output_type_lower == 'zip' and temp_zip_dir:
        # Metadati
        metadata_file = temp_zip_dir / "_metadata.txt"
        with open(metadata_file, 'w', encoding=TARGET_ENCODING, newline='') as mf:
             meta_content = f"Task: {task_name}\nFiles: {files_processed}\n"
             mf.write(normalize_newlines(meta_content, TARGET_NEWLINE))
             
        zip_file_path = dest_full_dir / f"{output_base_name}.zip"
        if create_zip_archive(temp_zip_dir, zip_file_path, verbose):
            try:
                shutil.rmtree(temp_zip_dir)
            except: pass

if __name__ == "__main__":
    main()
