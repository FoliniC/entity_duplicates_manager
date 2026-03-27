#!/usr/bin/env python3
"""
Verificatore Encoding Home Assistant - versione corretta
Aggiunge supporto per punteggiatura generale e simboli comuni
"""

import os
import sys
import argparse
import unicodedata
from pathlib import Path
from fnmatch import fnmatch


class HAEncodingChecker:
    def __init__(
        self,
        verbose=False,
        fix=False,
        backup=True,
        extensions=None,
        detect_invalid=True,
        context_chars=40,
        exclude_dirs=None,
        exclude_files=None,
    ):
        self.verbose = verbose
        self.fix = fix
        self.backup = backup
        self.detect_invalid = detect_invalid
        self.context_chars = context_chars
        self.files_checked = 0
        self.files_fixed = 0
        self.files_error = 0
        self.files_skipped = 0
        self.results = []

        self.default_extensions = {
            ".yaml",
            ".yml",
            ".py",
            ".json",
            ".log",
            ".md",
            ".jinja2",
        }

        if extensions:
            self.supported_extensions = self._parse_extensions(extensions)
        else:
            self.supported_extensions = self.default_extensions

        # CARTELLE DA ESCLUDERE
        self.default_exclude_dirs = [
            "__pycache__",
            ".git",
            ".venv",
            "venv",
            ".env",
            "env",
            ".pytest_cache",
            ".tox",
            ".coverage",
            "node_modules",
            "dist",
            "build",
            "*.egg-info",
            ".mypy_cache",
            ".vscode",
            ".idea",
            "__MACOSX",
        ]

        # FILE DA ESCLUDERE
        self.default_exclude_files = [
            "*.pyc",
            "*.pyo",
            "*.pyd",
            "*.so",
            "*.dll",
            "*.exe",
            "*.o",
            ".DS_Store",
            "Thumbs.db",
            ".gitignore",
            ".gitattributes",
        ]

        self.exclude_dirs = self._parse_exclude_patterns(
            exclude_dirs, self.default_exclude_dirs
        )
        self.exclude_files = self._parse_exclude_patterns(
            exclude_files, self.default_exclude_files
        )

        # Caratteri di controllo CATTIVI
        self.bad_control_chars = {
            "\x00": "[NULL]",
            "\x01": "[SOH]",
            "\x02": "[STX]",
            "\x03": "[ETX]",
            "\x04": "[EOT]",
            "\x05": "[ENQ]",
            "\x06": "[ACK]",
            "\x07": "[BEL]",
            "\x0b": "[VT]",
            "\x0c": "[FF]",
            "\x0e": "[SO]",
            "\x0f": "[SI]",
            "\x10": "[DLE]",
            "\x11": "[DC1]",
            "\x12": "[DC2]",
            "\x13": "[DC3]",
            "\x14": "[DC4]",
            "\x15": "[NAK]",
            "\x16": "[SYN]",
            "\x17": "[ETB]",
            "\x18": "[CAN]",
            "\x19": "[EM]",
            "\x1a": "[SUB]",
            "\x1b": "[ESC]",
            "\x1c": "[FS]",
            "\x1d": "[GS]",
            "\x1e": "[RS]",
            "\x1f": "[US]",
            "\x7f": "[DEL]",
        }

        self.good_control_chars = {"\x09": "[TAB]", "\x0a": "[LF]", "\x0d": "[CR]"}

        # Range Unicode VALIDI (European + Common Punctuation/Symbols)
        self.valid_ranges = [
            (0x0020, 0x007E),  # ASCII printable
            (0x0041, 0x005A),  # Latin majuscole A-Z
            (0x0061, 0x007A),  # Latin minuscole a-z
            (0x00A0, 0x017F),  # Latin Extended-A (con spazi e accenti)
            (0x0180, 0x024F),  # Latin Extended-B
            (0x0250, 0x02AF),  # IPA Extensions
            (0x1E00, 0x1EFF),  # Latin Extended Additional
            (0x0370, 0x03FF),  # Greek
            (0x0400, 0x04FF),  # Cyrillic
            (0x0500, 0x052F),  # Cyrillic Supplement
            (0x2000, 0x206F),  # General Punctuation (EN DASH, EM DASH, ecc)
            (0x2070, 0x209F),  # Superscripts and Subscripts
            (0x20A0, 0x20CF),  # Currency Symbols
            (0x2100, 0x214F),  # Letterlike Symbols
            (0x2150, 0x218F),  # Number Forms
            (0x2200, 0x22FF),  # Mathematical Operators
            (0x2300, 0x23FF),  # Miscellaneous Technical
            (0x2400, 0x243F),  # Optical Character Recognition
            (0x2440, 0x245F),  # Enclosed Alphanumerics
            (0x2500, 0x257F),  # Box Drawing
            (0x2580, 0x259F),  # Block Elements
            (0x25A0, 0x25FF),  # Geometric Shapes
            (0x2600, 0x26FF),  # Miscellaneous Symbols (emoji base)
            (0x2700, 0x27BF),  # Dingbats
        ]

        self.invalid_unicode_categories = {"Cc", "Cn", "Co", "Cs"}

    def _parse_extensions(self, extensions_str):
        parsed = set()
        patterns = extensions_str.split()
        for pattern in patterns:
            ext = pattern.lstrip("*").lstrip(".")
            if ext:
                parsed.add("." + ext.lower())
        return parsed if parsed else self.default_extensions

    def _parse_exclude_patterns(self, custom_patterns, default_patterns):
        if custom_patterns:
            if isinstance(custom_patterns, str):
                return custom_patterns.split()
            return custom_patterns
        return default_patterns

    def should_exclude_dir(self, dir_name):
        for pattern in self.exclude_dirs:
            if fnmatch(dir_name, pattern) or fnmatch(dir_name, f"*{pattern}*"):
                return True
            if dir_name.startswith("."):
                return True
        return False

    def should_exclude_file(self, file_name):
        for pattern in self.exclude_files:
            if fnmatch(file_name, pattern):
                return True
        return False

    def is_valid_text(self, char_code):
        """Controlla se il carattere è valido per testo European/common"""
        if char_code < 128:
            return True

        for start, end in self.valid_ranges:
            if start <= char_code <= end:
                return True

        return False

    def detect_encoding(self, file_path):
        try:
            with open(file_path, "rb") as f:
                raw_data = f.read()

            if raw_data.startswith(b"\xef\xbb\xbf"):
                return "utf-8-sig", "con BOM"
            elif raw_data.startswith(b"\xff\xfe"):
                return "utf-16-le", "con BOM"
            elif raw_data.startswith(b"\xfe\xff"):
                return "utf-16-be", "con BOM"

            try:
                with open(file_path, "r", encoding="utf-8", errors="strict") as f:
                    f.read()
                return "utf-8", "UTF-8 puro"
            except UnicodeDecodeError:
                for enc in ["latin-1", "cp1252", "iso-8859-1"]:
                    try:
                        with open(file_path, "r", encoding=enc, errors="strict") as f:
                            f.read()
                        return enc, f"probabile {enc}"
                    except:
                        continue

                return "unknown", "encoding sconosciuto"
        except Exception as e:
            return "error", str(e)

    def get_line_col_from_pos(self, text, pos):
        if pos > len(text):
            return 1, 1
        line = 1
        col = 1
        for i in range(pos):
            if text[i] == "\n":
                line += 1
                col = 1
            else:
                col += 1
        return line, col

    def get_context(self, text, pos, context_size=40):
        start = max(0, pos - context_size)
        end = min(len(text), pos + context_size + 1)
        context = text[start:end]
        offset_in_context = pos - start
        return context, offset_in_context

    def escape_for_display(self, text):
        display = text.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
        return display

    def check_invalid_unicode(self, text):
        invalid_chars = []

        for i, char in enumerate(text):
            char_code = ord(char)
            category = unicodedata.category(char)
            char_name = unicodedata.name(char, "UNKNOWN")
            line, col = self.get_line_col_from_pos(text, i)

            if char in self.good_control_chars:
                continue

            if char in self.bad_control_chars:
                context, offset = self.get_context(text, i, self.context_chars)
                invalid_chars.append(
                    {
                        "pos": i,
                        "line": line,
                        "col": col,
                        "char": char,
                        "desc": self.bad_control_chars[char],
                        "category": category,
                        "name": char_name,
                        "context": context,
                        "offset": offset,
                    }
                )

            elif category in self.invalid_unicode_categories:
                context, offset = self.get_context(text, i, self.context_chars)
                invalid_chars.append(
                    {
                        "pos": i,
                        "line": line,
                        "col": col,
                        "char": char,
                        "desc": f"[{category}]",
                        "category": category,
                        "name": char_name,
                        "context": context,
                        "offset": offset,
                    }
                )

            # Rileva SOLO caratteri veramente non-validi (non in range e non in categoria OK)
            elif not self.is_valid_text(char_code) and char_code > 127:
                if category not in [
                    "Po",
                    "Ps",
                    "Pe",
                    "Zs",
                    "Zl",
                    "Zp",
                    "Sc",
                    "So",
                    "Sm",
                ]:
                    context, offset = self.get_context(text, i, self.context_chars)
                    invalid_chars.append(
                        {
                            "pos": i,
                            "line": line,
                            "col": col,
                            "char": char,
                            "desc": f"[Non-standard: {char_name[:40]}]",
                            "category": category,
                            "name": char_name,
                            "context": context,
                            "offset": offset,
                        }
                    )

        return invalid_chars

    def format_error_context(self, char_info):
        context = char_info["context"]
        offset = char_info["offset"]
        display_context = self.escape_for_display(context)
        indicator = " " * offset + "^"
        output = f"    Contesto: ...{display_context}...\n"
        output += f"    Indicatore: ...{indicator}...\n"
        return output

    def check_content(self, file_path):
        issues = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="strict") as f:
                content = f.read()

            if content.startswith("\ufeff"):
                issues.append(
                    {"type": "BOM", "message": "Contiene BOM UTF-8 (da rimuovere)"}
                )

            if self.detect_invalid:
                invalid_unicode = self.check_invalid_unicode(content)
                if invalid_unicode:
                    for char_info in invalid_unicode:
                        msg = f"Linea {char_info['line']}, Colonna {char_info['col']}, Pos {char_info['pos']}: {char_info['desc']} - {char_info['name']} (U+{ord(char_info['char']):04X})\n"
                        msg += self.format_error_context(char_info)
                        issues.append(
                            {
                                "type": "INVALID_UNICODE",
                                "char_info": char_info,
                                "message": msg.rstrip(),
                            }
                        )

            return issues, None
        except UnicodeDecodeError as e:
            return [], f"Errore decodifica: {str(e)[:50]}"
        except Exception as e:
            return [], str(e)

    def fix_file(self, file_path):
        try:
            try:
                with open(file_path, "r", encoding="utf-8", errors="strict") as f:
                    content = f.read()
            except UnicodeDecodeError:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()

            if content.startswith("\ufeff"):
                content = content[1:]

            for control_char in self.bad_control_chars.keys():
                if control_char in content:
                    content = content.replace(control_char, "")

            if self.detect_invalid:
                invalid_unicode = self.check_invalid_unicode(content)
                for char_info in invalid_unicode:
                    content = content.replace(char_info["char"], "")

            if self.backup:
                backup_path = f"{file_path}.bak"
                try:
                    with open(file_path, "rb") as src:
                        with open(backup_path, "wb") as dst:
                            dst.write(src.read())
                    if self.verbose:
                        print(f"   Backup creato: {backup_path}")
                except Exception as e:
                    print(f"   Avviso: Backup fallito - {e}")

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            return True, "File corretto con successo"
        except Exception as e:
            return False, str(e)

    def process_file(self, file_path):
        self.files_checked += 1
        encoding, encoding_info = self.detect_encoding(file_path)
        issues, error = self.check_content(file_path)
        is_correct = encoding.lower() == "utf-8" and not issues and not error

        if is_correct:
            status = "OK"
        else:
            status = "WARN" if not error else "ERROR"

        if self.fix and not is_correct and status != "ERROR":
            success, msg = self.fix_file(file_path)
            if success:
                status = "FIXED"
                self.files_fixed += 1
                issues.append({"type": "FIXED", "message": f"Corretto: {msg}"})
            else:
                status = "FIX_ERROR"
                self.files_error += 1
                issues.append(
                    {"type": "FIX_ERROR", "message": f"Errore correzione: {msg}"}
                )

        self.results.append(
            {
                "file": file_path,
                "status": status,
                "encoding": encoding if status != "FIXED" else "UTF-8",
                "encoding_info": encoding_info,
                "issues": issues,
                "error": error,
            }
        )

    def process_directory(self, directory):
        print(f"Scansione directory: {directory}")
        print(f"Estensioni filtrate: {', '.join(sorted(self.supported_extensions))}")
        print(f"Cartelle escluse: {', '.join(self.exclude_dirs[:5])}...")
        print(f"File esclusi: {', '.join(self.exclude_files[:5])}...\n")

        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if not self.should_exclude_dir(d)]

            for file in files:
                file_path = os.path.join(root, file)
                file_ext = Path(file_path).suffix.lower()

                if self.should_exclude_file(file):
                    self.files_skipped += 1
                    if self.verbose:
                        print(f"Escluso: {file}")
                    continue

                if file_ext in self.supported_extensions:
                    self.process_file(file_path)

                    if self.files_checked % 10 == 0:
                        print(
                            f"Elaborati {self.files_checked} file... (Saltati: {self.files_skipped})"
                        )

    def print_report(self):
        print("\n" + "=" * 100)
        print("REPORT VERIFICA ENCODING HOME ASSISTANT")
        print("=" * 100)

        if not self.results:
            print("Nessun file trovato da verificare.")
            return

        ok_count = sum(1 for r in self.results if r["status"] == "OK")
        warn_count = sum(1 for r in self.results if r["status"] == "WARN")
        fixed_count = sum(1 for r in self.results if r["status"] == "FIXED")
        error_count = sum(
            1 for r in self.results if r["status"] in ["ERROR", "FIX_ERROR"]
        )

        print("\nRIEPILOGO:")
        print(f"  File verificati: {self.files_checked}")
        print(f"  File saltati: {self.files_skipped}")
        print(f"  OK (UTF-8 corretto): {ok_count}")
        print(f"  Warning (da correggere): {warn_count}")
        print(f"  Corretti: {fixed_count}")
        print(f"  Errori: {error_count}")

        print("\nDETAGLI:")
        print("-" * 100)

        for result in self.results:
            if result["status"] in ["WARN", "ERROR", "FIX_ERROR", "FIXED"]:
                print(f"\n[{result['status']}] {result['file']}")
                print(
                    f"  Encoding: {result['encoding']} ({result.get('encoding_info', '')})"
                )

                if result["error"]:
                    print(f"  Errore: {result['error']}")

                if result["issues"]:
                    for issue in result["issues"]:
                        print(f"\n  - {issue['message']}")

        print("\n" + "=" * 100)
        print("FINE ANALISI")
        print("=" * 100)


def main():
    parser = argparse.ArgumentParser(
        description="Verificatore Encoding HA - Versione definitiva"
    )
    parser.add_argument("path", help="File o directory da verificare")
    parser.add_argument("--fix", action="store_true", help="Correggi encoding")
    parser.add_argument("--no-backup", action="store_true", help="Non creare backup")
    parser.add_argument("--verbose", "-v", action="store_true", help="Output verboso")
    parser.add_argument("--extensions", "-e", type=str, default=None, help="Estensioni")
    parser.add_argument(
        "--context", "-c", type=int, default=40, help="Contesto (default: 40)"
    )
    parser.add_argument(
        "--exclude-dirs", type=str, default=None, help="Escludi cartelle"
    )
    parser.add_argument("--exclude-files", type=str, default=None, help="Escludi file")

    args = parser.parse_args()

    checker = HAEncodingChecker(
        verbose=args.verbose,
        fix=args.fix,
        backup=not args.no_backup,
        extensions=args.extensions,
        detect_invalid=True,
        context_chars=args.context,
        exclude_dirs=args.exclude_dirs,
        exclude_files=args.exclude_files,
    )

    print(f"Estensioni: {', '.join(sorted(checker.supported_extensions))}")
    print(f"Contesto: {args.context} caratteri\n")

    path = args.path

    if os.path.isfile(path):
        print(f"Verifica file: {path}\n")
        checker.process_file(path)
    elif os.path.isdir(path):
        checker.process_directory(path)
    else:
        print(f"Errore: {path} non esiste")
        sys.exit(1)

    checker.print_report()

    if any(r["status"] in ["ERROR", "FIX_ERROR"] for r in checker.results):
        sys.exit(1)
    elif any(r["status"] == "WARN" for r in checker.results) and not args.fix:
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
