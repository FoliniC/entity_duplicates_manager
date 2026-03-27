#!/usr/bin/env python3
"""
Analizzatore Log Home Assistant - Versione Completa con Timeline Eventi
Analizza log, calcola tempo di avvio, intercetta eventi start/stop/restart e identifica problemi
Con parametro --max-msg-len per controllare la lunghezza massima messaggi visualizzati
"""

import re
import sys
import os
from datetime import datetime
from collections import defaultdict, Counter
import argparse


class HALogAnalyzer:
    def __init__(self, verbose=False, max_msg_length=500):
        self.verbose = verbose
        self.max_msg_length = max_msg_length
        self.startup_events = {}
        self.startup_start_time = None
        self.startup_end_time = None
        self.event_timeline = []
        self.blocking_calls = []
        self.pyscript_issues = []
        self.errors = []
        self.warnings = []
        self.timeout_events = []
        self.initialization_line_index = None
        self.last_timestamp = None
        self.analysis_stats = Counter()
        self.events_patterns = [
            ("HA STARTED", "homeassistant_start"),
            ("HA STOPPED", "homeassistant_stop"),
            ("HA RESTARTED", "homeassistant_restart"),
        ]

    def _show_progress(self, current, total, prefix="", suffix="", bar_length=50):
        if total == 0:
            return
        percent = min(100.0, float(current) * 100 / total)
        arrow_length = int(percent / 100 * bar_length)
        arrow = (
            "=" * arrow_length + ">" if arrow_length < bar_length else "=" * bar_length
        )
        spaces = " " * (bar_length - len(arrow))
        sys.stdout.write(f"\r{prefix}[{arrow}{spaces}] {percent:.1f}% {suffix}")
        sys.stdout.flush()

    def parse_log_file(self, log_file_path):
        print(f"Analizzando il file di log: {log_file_path}")
        print(
            f"Lunghezza massima messaggi: {self.max_msg_length if self.max_msg_length != float('inf') else 'illimitata'}"
        )
        try:
            file_size = os.path.getsize(log_file_path)
            file_size_mb = file_size / (1024 * 1024)
            print(f"Dimensione file: {file_size_mb:.1f} MB")
        except OSError:
            print("Errore: Impossibile determinare la dimensione del file")
        print("-" * 100)
        try:
            with open(log_file_path, "r", encoding="utf-8", errors="ignore") as file:
                lines = file.readlines()
        except Exception as e:
            print(f"Errore nella lettura del file: {e}")
            return
        total_lines = len(lines)
        print(f"Totale righe da analizzare: {total_lines:,}")
        if total_lines == 0:
            print("Errore: File di log vuoto!")
            return
        print()
        print("Fase 1: Ricerca timeline avvio, eventi start/stop/restart...")
        self._extract_startup_timeline(lines)
        self._extract_event_timeline(lines)
        print(f"\nFase 2: Analisi di {total_lines} righe...")
        self._simple_stable_analysis(lines)
        print("\nAnalisi completata!")

    def _extract_event_timeline(self, lines):
        for line_num, line in enumerate(lines):
            for pat, event_type in self.events_patterns:
                if f"EVENTO: {pat} alle " in line:
                    ts_match = re.search(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line)
                    if ts_match:
                        self.event_timeline.append(
                            {
                                "event": event_type,
                                "timestamp": ts_match.group(1),
                                "line_number": line_num,
                                "message": line.strip(),
                            }
                        )

    def _extract_startup_timeline(self, lines):
        startup_patterns = {
            "Home Assistant starting": ("inizio_avvio", "Inizio del processo"),
            "Home Assistant initialized": (
                "inizializzazione",
                "Inizializzazione completata",
            ),
            "Home Assistant started": ("avvio_completato", "UI disponibile"),
        }
        for line_num, line in enumerate(lines):
            time_match = re.search(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}.\d{3})", line)
            if not time_match:
                continue
            timestamp = time_match.group(1)
            for pattern, (key, description) in startup_patterns.items():
                if pattern in line and key not in self.startup_events:
                    self.startup_events[key] = {
                        "timestamp": timestamp,
                        "line_number": line_num,
                        "description": description,
                        "message": line.strip(),
                    }
                    if key == "inizio_avvio":
                        self.startup_start_time = timestamp
                    elif key == "avvio_completato":
                        self.startup_end_time = timestamp
                    print(f"OK {description}: {timestamp}")
        if not self.startup_events:
            print("Attenzione: Nessun evento di avvio trovato nel log")

    def _simple_stable_analysis(self, lines):
        total_lines = len(lines)
        for i, line in enumerate(lines):
            if i % 500 == 0 or i == total_lines - 1:
                self._show_progress(
                    i + 1, total_lines, "Analisi ", f"riga {i + 1}/{total_lines}"
                )
            self._simple_analyze_line(line, i)

    def _simple_analyze_line(self, line, line_number):
        time_match = re.search(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line)
        timestamp = time_match.group(1) if time_match else None
        if "Detected blocking call" in line and "inside the event loop" in line:
            self._simple_analyze_blocking(line, timestamp, line_number)
        elif "ERROR" in line or "CRITICAL" in line:
            self._simple_analyze_error(line, timestamp, line_number)
        elif "WARNING" in line and "DEBUG" not in line:
            self._simple_analyze_warning(line, timestamp, line_number)
        elif "pyscript" in line.lower():
            self._simple_analyze_pyscript(line, timestamp, line_number)
        elif any(x in line.lower() for x in ["timeout", "timed out"]):
            self._simple_analyze_timeout(line, timestamp, line_number)

    def _simple_analyze_blocking(self, line, timestamp, line_number):
        try:
            component_match = re.search(r"by (.*?) at", line)
            component = component_match.group(1) if component_match else "unknown"
            function_match = re.search(r"call to (\w+)", line)
            function = function_match.group(1) if function_match else "unknown"
            self.blocking_calls.append(
                {
                    "component": component,
                    "function": function,
                    "line_number": line_number,
                    "timestamp": timestamp,
                    "message": line.strip(),
                }
            )
        except Exception as e:
            if self.verbose:
                print(f"\nErrore parsing blocking call: {e}")

    def _simple_analyze_error(self, line, timestamp, line_number):
        try:
            component = self._extract_component_simple(line)
            error_type = "connection" if "connection" in line.lower() else "general"
            self.errors.append(
                {
                    "component": component,
                    "type": error_type,
                    "line_number": line_number,
                    "timestamp": timestamp,
                    "message": line.strip(),
                }
            )
        except Exception as e:
            if self.verbose:
                print(f"\nErrore parsing error: {e}")

    def _format_message(self, msg):
        """Formatta il messaggio secondo max_msg_length"""
        if self.max_msg_length == float("inf") or len(msg) <= self.max_msg_length:
            return msg
        else:
            return (
                msg[: int(self.max_msg_length)]
                + f"... [TRONCATO, totale {len(msg)} caratteri]"
            )

    def _simple_analyze_warning(self, line, timestamp, line_number):
        try:
            component = self._extract_component_simple(line)
            self.warnings.append(
                {
                    "component": component,
                    "line_number": line_number,
                    "timestamp": timestamp,
                    "message": line.strip(),
                }
            )
        except Exception as e:
            if self.verbose:
                print(f"\nErrore parsing warning: {e}")

    def _simple_analyze_pyscript(self, line, timestamp, line_number):
        try:
            issue_type = "general"
            if "automation" in line.lower():
                issue_type = "automation"
            self.pyscript_issues.append(
                {
                    "type": issue_type,
                    "line_number": line_number,
                    "timestamp": timestamp,
                    "message": line.strip(),
                }
            )
        except Exception as e:
            if self.verbose:
                print(f"\nErrore parsing pyscript: {e}")

    def _simple_analyze_timeout(self, line, timestamp, line_number):
        try:
            component = self._extract_component_simple(line)
            self.timeout_events.append(
                {
                    "component": component,
                    "line_number": line_number,
                    "timestamp": timestamp,
                    "message": line.strip(),
                }
            )
        except Exception as e:
            if self.verbose:
                print(f"\nErrore parsing timeout: {e}")

    def _extract_component_simple(self, line):
        if "custom_components/pyscript" in line:
            return "pyscript"
        elif "homeassistant/components/" in line:
            match = re.search(r"homeassistant/components/([^/]+)", line)
            return match.group(1) if match else "hass_component"
        elif "pyscript" in line.lower():
            return "pyscript"
        else:
            return "unknown"

    def _calculate_startup_duration(self):
        if not self.startup_start_time or not self.startup_end_time:
            return None
        try:
            start = datetime.strptime(self.startup_start_time, "%Y-%m-%d %H:%M:%S.%f")
            end = datetime.strptime(self.startup_end_time, "%Y-%m-%d %H:%M:%S.%f")
            return end - start
        except:
            return None

    def generate_report(self):
        print("\n" + "=" * 100)
        print("RAPPORTO ANALISI - VERSIONE COMPLETA CON TIMELINE EVENTI")
        print("=" * 100)
        print("\nTIMELINE EVENTI HOME ASSISTANT:")
        print("-" * 100)
        if self.event_timeline:
            for idx, e in enumerate(self.event_timeline, 1):
                print(f"[{idx}] Evento: {e['event']}")
                print(f"    Timestamp: {e['timestamp']}")
                print(f"    Riga: {e['line_number']}")
                print(f"    Messaggio: {self._format_message(e['message'])}")
                print()
        else:
            print("Nessun evento start/stop/restart trovato nel log\n")

        print("TIMELINE AVVIO HOME ASSISTANT:")
        print("-" * 100)
        if self.startup_events:
            events_ordered = [
                ("inizio_avvio", "Inizio Avvio"),
                ("inizializzazione", "Inizializzazione"),
                ("avvio_completato", "Avvio Completato"),
            ]
            for key, label in events_ordered:
                if key in self.startup_events:
                    event = self.startup_events[key]
                    print(f"\nOK {label}")
                    print(f"   Timestamp: {event['timestamp']}")
                    print(f"   Riga: {event['line_number']}")
                    print(f"   Messaggio: {self._format_message(event['message'])}")
            duration = self._calculate_startup_duration()
            if duration:
                print(
                    f"\nTempo totale di avvio: {duration.total_seconds():.2f} secondi"
                )
                if duration.total_seconds() > 300:
                    print("AVVIO MOLTO LENTO (>5 min) - Probabile blocco!")
                elif duration.total_seconds() > 120:
                    print("AVVIO LENTO (>2 min) - Verifica integrazioni bloccanti")
                else:
                    print("Tempo di avvio normale")
        else:
            print("Home Assistant non ha completato l'avvio o il log e incompleto\n")

        if self.blocking_calls:
            print(f"\nBLOCKING CALLS TROVATE ({len(self.blocking_calls)}):")
            print("-" * 100)
            by_component = defaultdict(list)
            for call in self.blocking_calls:
                by_component[call["component"]].append(call)
            for component, calls in by_component.items():
                print(f"\n{component.upper()}: {len(calls)} chiamate bloccanti")
                for idx, call in enumerate(calls, 1):
                    print(
                        f"   [{idx}] Riga {call['line_number']}, Funzione: {call.get('function', '?')}"
                    )
                    print(f"       Messaggio: {self._format_message(call['message'])}")
                    print()

        if self.errors:
            print(f"\nERRORI TROVATI ({len(self.errors)}):")
            print("-" * 100)
            by_component = defaultdict(list)
            for error in self.errors:
                by_component[error["component"]].append(error)
            for component, errors in by_component.items():
                print(f"\n{component.upper()}: {len(errors)} errori")
                for idx, error in enumerate(errors, 1):
                    print(f"   [{idx}] Riga {error['line_number']} ({error['type']})")
                    print(f"       Messaggio: {self._format_message(error['message'])}")
                    print()

        if self.warnings:
            print(f"\nWARNING TROVATI ({len(self.warnings)}):")
            print("-" * 100)
            by_component = defaultdict(list)
            for warning in self.warnings:
                by_component[warning["component"]].append(warning)
            for component, warnings_list in by_component.items():
                print(f"\n{component.upper()}: {len(warnings_list)} warning")
                for idx, warning in enumerate(warnings_list, 1):
                    print(f"   [{idx}] Riga {warning['line_number']}")
                    print(
                        f"       Messaggio: {self._format_message(warning['message'])}"
                    )
                    print()

        if self.pyscript_issues:
            print(f"\nPROBLEMI PYSCRIPT ({len(self.pyscript_issues)}):")
            print("-" * 100)
            by_type = defaultdict(list)
            for issue in self.pyscript_issues:
                by_type[issue["type"]].append(issue)
            for issue_type, issues in by_type.items():
                print(f"\n   Tipo: {issue_type.upper()} - {len(issues)} occorrenze")
                for idx, issue in enumerate(issues, 1):
                    print(f"      [{idx}] Riga {issue['line_number']}")
                    print(
                        f"          Messaggio: {self._format_message(issue['message'])}"
                    )
                    print()

        if self.timeout_events:
            print(f"\nTIMEOUT TROVATI ({len(self.timeout_events)}):")
            print("-" * 100)
            for idx, timeout in enumerate(self.timeout_events, 1):
                print(
                    f"   [{idx}] Riga {timeout['line_number']} ({timeout['component']})"
                )
                print(f"       Messaggio: {self._format_message(timeout['message'])}")
                print()

        print("\nRIEPILOGO:")
        print("-" * 100)
        print(f"Blocking calls: {len(self.blocking_calls)}")
        print(f"Errori: {len(self.errors)}")
        print(f"Warning: {len(self.warnings)}")
        print(f"Problemi PyScript: {len(self.pyscript_issues)}")
        print(f"Timeout: {len(self.timeout_events)}")


def main():
    parser = argparse.ArgumentParser(
        description="Analizzatore Log HA - Versione Completa + Timeline Eventi"
    )
    parser.add_argument("logfile", help="Percorso al file di log")
    parser.add_argument("--verbose", "-v", action="store_true", help="Output verboso")
    parser.add_argument(
        "--max-msg-len",
        "-m",
        type=int,
        default=500,
        help="Lunghezza massima messaggi (0 = illimitato, default: 500)",
    )

    args = parser.parse_args()

    max_len = args.max_msg_len if args.max_msg_len > 0 else float("inf")

    print("Avvio analizzatore in modalita COMPLETA con TIMELINE EVENTI...\n")
    analyzer = HALogAnalyzer(verbose=args.verbose, max_msg_length=max_len)

    try:
        analyzer.parse_log_file(args.logfile)
        analyzer.generate_report()
    except FileNotFoundError:
        print(f"Errore: File non trovato: {args.logfile}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nAnalisi interrotta dall'utente")
        sys.exit(1)
    except Exception as e:
        print(f"Errore imprevisto: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
