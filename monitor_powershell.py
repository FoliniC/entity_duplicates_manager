#!/usr/bin/env python3
"""
Monitora una finestra PowerShell e preme '2' quando appare il testo
"Allow execution of [Shell]?"
"""

import time
import sys
from pywinauto import Application, Desktop
from pywinauto.findwindows import ElementNotFoundError
import argparse


def find_powershell_window(title_contains="PowerShell"):
    """Trova la finestra PowerShell target."""
    try:
        # Cerca finestre che contengono "PowerShell" nel titolo
        windows = Desktop(backend="uia").windows(title_re=f".*{title_contains}.*")
        if windows:
            return windows[0]
    except ElementNotFoundError:
        pass
    return None


def get_window_text(window):
    """Estrae tutto il testo visibile dalla finestra."""
    try:
        # Per console PowerShell, il testo è nel controllo "ConsoleWindowClass"
        # Proviamo diversi approcci
        texts = []

        # Metodo 1: Legacy text (funziona per console standard)
        try:
            legacy_text = window.legacy_properties()["text"]
            if legacy_text:
                texts.append(legacy_text)
        except Exception:
            pass

        # Metodo 2: UIA TextPattern - scansiona tutti gli elementi figli
        try:
            for child in window.descendants(control_type="Text"):
                try:
                    txt = child.window_text()
                    if txt and txt.strip():
                        texts.append(txt)
                except Exception:
                    continue
        except Exception:
            pass

        # Metodo 3: window_text() diretto
        try:
            direct_text = window.window_text()
            if direct_text:
                texts.append(direct_text)
        except Exception:
            pass

        return "\n".join(texts)
    except Exception as e:
        print(f"Errore lettura testo: {e}")
        return ""


def send_key(window, key):
    """Invia un tasto alla finestra."""
    try:
        window.set_focus()
        time.sleep(0.1)
        window.type_keys(key)
        print(f"Inviato tasto: '{key}'")
        return True
    except Exception as e:
        print(f"Errore invio tasto: {e}")
        return False


def monitor_window(window, trigger_text="Allow execution of [Shell]?", key_to_send="2", check_interval=0.5):
    """
    Monitora la finestra per il testo trigger.
    """
    print(f"Monitoraggio avviato...")
    print(f"Testo trigger: '{trigger_text}'")
    print(f"Tasto da inviare: '{key_to_send}'")
    print(f"Intervallo controllo: {check_interval}s")
    print("-" * 50)

    already_triggered = False

    try:
        while True:
            try:
                # Riporta la finestra in primo piano se non lo è
                if not window.has_focus():
                    window.set_focus()

                current_text = get_window_text(window)

                if trigger_text in current_text:
                    if not already_triggered:
                        print(f"\n[TRIGGER TROVATO] Testo rilevato: '{trigger_text}'")
                        if send_key(window, key_to_send):
                            already_triggered = True
                            print("Attendo che il testo scompaia prima di riarmare...")
                    else:
                        # Verifica se il testo è scomparso per riarmare
                        if trigger_text not in current_text:
                            already_triggered = False
                            print("Testo trigger scomparso - monitoraggio riarmato")
                else:
                    if already_triggered:
                        already_triggered = False
                        print("Testo trigger scomparso - monitoraggio riarmato")

            except Exception as e:
                print(f"Errore durante monitoraggio: {e}")

            time.sleep(check_interval)

    except KeyboardInterrupt:
        print("\n\nMonitoraggio interrotto dall'utente.")


def main():
    parser = argparse.ArgumentParser(
        description="Monitora una finestra PowerShell e preme un tasto quando appare un testo specifico"
    )
    parser.add_argument(
        "--title",
        default="PowerShell",
        help="Testo da cercare nel titolo della finestra (default: 'PowerShell')"
    )
    parser.add_argument(
        "--trigger",
        default="Allow execution of [Shell]?",
        help="Testo che attiva l'invio del tasto (default: 'Allow execution of [Shell]?')"
    )
    parser.add_argument(
        "--key",
        default="2",
        help="Tasto da premere quando il trigger viene trovato (default: '2')"
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.5,
        help="Intervallo di controllo in secondi (default: 0.5)"
    )
    parser.add_argument(
        "--list-windows",
        action="store_true",
        help="Elenca tutte le finestre PowerShell trovate ed esce"
    )

    args = parser.parse_args()

    print("=== PowerShell Window Monitor ===")
    print(f"Cerca finestre con titolo contenente: '{args.title}'")

    # Trova la finestra
    window = find_powershell_window(args.title)

    if not window:
        print("Nessuna finestra PowerShell trovata!")
        print("\nFinestre disponibili con 'PowerShell' nel titolo:")
        for w in Desktop(backend="uia").windows():
            if "powershell" in w.window_text().lower() or "powershell" in w.class_name().lower():
                print(f"  - Titolo: '{w.window_text()}' | Classe: '{w.class_name()}' | Handle: {w.handle}")
        sys.exit(1)

    print(f"Finestra trovata:")
    print(f"  Titolo: '{window.window_text()}'")
    print(f"  Classe: '{window.class_name()}'")
    print(f"  Handle: {window.handle}")

    if args.list_windows:
        sys.exit(0)

    # Avvia monitoraggio
    monitor_window(window, args.trigger, args.key, args.interval)


if __name__ == "__main__":
    main()