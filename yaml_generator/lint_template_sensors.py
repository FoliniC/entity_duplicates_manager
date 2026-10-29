#!/usr/bin/env python3
"""Controllo strutturale dei YAML generati (template sensor di Home Assistant).

Trova gli errori che HA non segnala in modo chiaro:
  1. 'attributes:' (o icon/availability/unique_id/device_class/unit_of_measurement/name) finito DENTRO il testo di state/variables
     per un errore di indentazione -> il sensore non ha attributi veri e lo stato diventa enorme
     ("State ... is longer than 255, falling back to unknown").
  2. YAML non valido (es. '{{ ... }}' non quotato come valore di chiave).
Uso:  python3 lint_template_sensors.py cartella_o_file.yaml [...]
"""
import sys, pathlib, re, yaml

SUSPECT = re.compile(r"^\s*(attributes|icon|availability|unique_id|device_class|unit_of_measurement|name)\s*:", re.M)

def sensors_of(doc):
    if isinstance(doc, list):
        for x in doc:
            if isinstance(x, dict) and "sensor" in x and isinstance(x["sensor"], list): yield from x["sensor"]
            elif isinstance(x, dict) and ("state" in x or "name" in x): yield x
    elif isinstance(doc, dict):
        for k in ("sensor", "binary_sensor"):
            if isinstance(doc.get(k), list): yield from doc[k]

def check(path):
    problems = []
    txt = pathlib.Path(path).read_text(encoding="utf-8")
    txt = re.sub(r"^(\s*entity_id:\s*)\{\{.*\}\}\s*$", r"\1PLACEHOLDER", txt, flags=re.M)  # solo per poter parsare
    try:
        doc = yaml.safe_load(txt)
    except Exception as e:
        return [f"YAML non valido: {str(e).splitlines()[0]}"]
    for s in sensors_of(doc):
        nm = s.get("name", "?")
        for field in ("state", "availability", "icon"):
            v = s.get(field)
            if isinstance(v, str):
                m = SUSPECT.search(v)
                if m:
                    problems.append(f"[{nm}] '{m.group(1)}:' compare DENTRO il testo di {field} (indentazione errata): "
                                    f"il sensore ha solo le chiavi {sorted(s.keys())}")
                    break
        for k, v in (s.get("variables") or {}).items():
            if isinstance(v, str) and SUSPECT.search(v) and "attributes:" in v:
                problems.append(f"[{nm}] 'attributes:' dentro la variabile '{k}'")
    return problems

if __name__ == "__main__":
    files = []
    for a in sys.argv[1:] or ["."]:
        p = pathlib.Path(a)
        files += sorted(p.rglob("*.yaml")) if p.is_dir() else [p]
    bad = 0
    for f in files:
        pr = check(f)
        if pr:
            bad += 1
            print(f"✗ {f}")
            for x in pr: print("   -", x)
    print(f"\n{len(files)} file controllati, {bad} con problemi")
    sys.exit(1 if bad else 0)