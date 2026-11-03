#!/usr/bin/env python3
"""
Analizza i log fancoil_events per confrontare sensori Corridoio vs Mijia.
Estrae da tutte le righe 'State Dump' del corridoio i campi:
- Temp (fancoil), Hum (fancoil)
- Mijia_T, Mijia_RH
- Cal_T, Cal_RH (valori calibrati)
- Off_T_24h, Off_RH_24h (offset statistici 24h)
Calcola differenze, statistiche e verifica stabilità taratura.
"""

import re
import sys
import os
from datetime import datetime
from collections import defaultdict
from pathlib import Path

LOG_DIR = Path("/config/logs/fancoil_events")
LOG_PATTERN = re.compile(r"fancoil_events(?:\_\d{4}-\d{2}-\d{2}_\d{6})?\.log$")

# Regex per parsare la riga State Dump corridoio (con o senza prefisso filename)
STATE_DUMP_PATTERN = re.compile(
    r"(?:.*?\s)?(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[INFO\] \[Corridoio\] State Dump: "
    r"Trigger=[^,]+, "
    r"Temp=(?P<fancoil_temp>[\d.]+)°C, "
    r"KNX=[^,]+, "
    r"Hum=(?P<fancoil_hum>[\d.]+)% \(Var: [^,]+\), "
    r"Setpoint=[^,]+, "
    r"MasterSP=[^,]+, "
    r"Delta=(?P<delta>[\d.]+)°C \(RawDiff: (?P<rawdiff>[\d.]+)\), "
    r"Offset=[^,]+, "
    r"Target=[^,]+, "
    r"HvacMode=[^,]+, "
    r"StopCond=[^,]+, "
    r"System=[^,]+, "
    r"PDC_H2O=[^,]+, "
    r"Comm=[^,]+, "
    r"T_Circ=[^,]+, "
    r"Main=[^,]+, "
    r"Soglie=\[.*?\], "
    r"SW=\[.*?\], "
    r"Mijia_T=(?P<mijia_temp>[\d.]+|unavailable)°C, "
    r"Mijia_RH=(?P<mijia_rh>[\d.]+|unavailable)%, "
    r"Cal_T=(?P<cal_temp>[\d.]+|unavailable)°C, "
    r"Cal_RH=(?P<cal_rh>[\d.]+|unavailable)%, "
    r"Off_T_24h=(?P<off_t>[-]?[\d.]+|unavailable)°C, "
    r"Off_RH_24h=(?P<off_rh>[-]?[\d.]+|unavailable)%"
)


def parse_log_file(filepath: Path):
    """Parsa un singolo file log e restituisce lista di dict con i dati estratti."""
    records = []
    with open(filepath, "r") as f:
        for line_num, line in enumerate(f, 1):
            if "[Corridoio] State Dump:" not in line:
                continue
            m = STATE_DUMP_PATTERN.search(line)
            if not m:
                # Prova pattern più permissivo
                continue
            try:
                rec = {
                    "timestamp": datetime.strptime(m.group("ts"), "%Y-%m-%d %H:%M:%S"),
                    "fancoil_temp": float(m.group("fancoil_temp")),
                    "fancoil_hum": float(m.group("fancoil_hum")),
                    "mijia_temp": None if m.group("mijia_temp") == "unavailable" else float(m.group("mijia_temp")),
                    "mijia_rh": None if m.group("mijia_rh") == "unavailable" else float(m.group("mijia_rh")),
                    "cal_temp": None if m.group("cal_temp") == "unavailable" else float(m.group("cal_temp")),
                    "cal_rh": None if m.group("cal_rh") == "unavailable" else float(m.group("cal_rh")),
                    "off_t": None if m.group("off_t") == "unavailable" else float(m.group("off_t")),
                    "off_rh": None if m.group("off_rh") == "unavailable" else float(m.group("off_rh")),
                    "source_file": filepath.name,
                    "line_num": line_num,
                }
                records.append(rec)
            except (ValueError, AttributeError) as e:
                print(f"Parse error in {filepath.name}:{line_num}: {e}", file=sys.stderr)
    return records


def analyze_records(records):
    """Analizza i record e stampa statistiche."""
    if not records:
        print("Nessun record trovato!")
        return

    # Filtra solo record con Mijia disponibile
    with_mijia = [r for r in records if r["mijia_temp"] is not None and r["mijia_rh"] is not None]
    without_mijia = [r for r in records if r["mijia_temp"] is None or r["mijia_rh"] is None]

    print(f"\n=== STATISTICHE GENERALI ===")
    print(f"Totale state dump corridoio: {len(records)}")
    print(f"Con Mijia disponibile: {len(with_mijia)}")
    print(f"Senza Mijia (unavailable): {len(without_mijia)}")

    if not with_mijia:
        print("\n❌ Nessun dato Mijia disponibile per confronto")
        return

    # Range temporale
    ts_min = min(r["timestamp"] for r in with_mijia)
    ts_max = max(r["timestamp"] for r in with_mijia)
    print(f"\nPeriodo coperto: {ts_min} → {ts_max} ({(ts_max - ts_min).total_seconds()/3600:.1f} ore)")

    # Diff temp: fancoil - mijia (raw offset osservato)
    temp_diffs = [r["fancoil_temp"] - r["mijia_temp"] for r in with_mijia]
    rh_diffs = [r["fancoil_hum"] - r["mijia_rh"] for r in with_mijia]

    print(f"\n=== DIFFERENZE OSSERVATE (Fancoil - Mijia) ===")
    print(f"Temperatura: media={sum(temp_diffs)/len(temp_diffs):.2f}°C, "
          f"min={min(temp_diffs):.2f}°C, max={max(temp_diffs):.2f}°C, "
          f"std={(sum((x - sum(temp_diffs)/len(temp_diffs))**2 for x in temp_diffs)/len(temp_diffs))**0.5:.2f}°C")
    print(f"Umidità:     media={sum(rh_diffs)/len(rh_diffs):.2f}%, "
          f"min={min(rh_diffs):.2f}%, max={max(rh_diffs):.2f}%, "
          f"std={(sum((x - sum(rh_diffs)/len(rh_diffs))**2 for x in rh_diffs)/len(rh_diffs))**0.5:.2f}%")

    # Offset statistici 24h (ultimo valore per ogni giorno)
    by_day = defaultdict(list)
    for r in with_mijia:
        if r["off_t"] is not None:
            by_day[r["timestamp"].date()].append(r)

    print(f"\n=== OFFSET STATISTICI 24h (ultimo per giorno) ===")
    for day in sorted(by_day.keys()):
        last = by_day[day][-1]
        print(f"  {day}: Off_T_24h={last['off_t']:.2f}°C, Off_RH_24h={last['off_rh']:.2f}% "
              f"(campioni: {len(by_day[day])})")

    # Valori calibrati vs Mijia
    cal_temp_diffs = [r["cal_temp"] - r["mijia_temp"] for r in with_mijia if r["cal_temp"] is not None]
    cal_rh_diffs = [r["cal_rh"] - r["mijia_rh"] for r in with_mijia if r["cal_rh"] is not None]

    if cal_temp_diffs:
        print(f"\n=== VALORI CALIBRATI vs MIJIA (Cal - Mijia) ===")
        print(f"Temperatura: media={sum(cal_temp_diffs)/len(cal_temp_diffs):.2f}°C")
        print(f"Umidità:     media={sum(cal_rh_diffs)/len(cal_rh_diffs):.2f}%")

    # Verifica stabilità taratura (ultime 24h)
    cutoff = ts_max - (ts_max - ts_min) if (ts_max - ts_min).total_seconds() > 86400 else ts_min
    recent = [r for r in with_mijia if r["timestamp"] >= cutoff]
    if len(recent) > 10:
        recent_temp_diffs = [r["fancoil_temp"] - r["mijia_temp"] for r in recent]
        recent_rh_diffs = [r["fancoil_hum"] - r["mijia_rh"] for r in recent]
        temp_range = max(recent_temp_diffs) - min(recent_temp_diffs)
        rh_range = max(recent_rh_diffs) - min(recent_rh_diffs)
        print(f"\n=== STABILITÀ ULTIME 24h ({len(recent)} campioni) ===")
        print(f"Range diff T: {temp_range:.2f}°C {'✅' if temp_range < 0.5 else '❌'} (soglia <0.5°C)")
        print(f"Range diff RH: {rh_range:.2f}% {'✅' if rh_range < 5 else '❌'} (soglia <5%)")

    # Campioni per ora (ultime 24h)
    if len(recent) > 0:
        hours = defaultdict(int)
        for r in recent:
            hours[r["timestamp"].hour] += 1
        avg_per_hour = sum(hours.values()) / max(len(hours), 1)
        print(f"\nCampioni/ora (ultime 24h): media={avg_per_hour:.1f}, "
              f"totale={len(recent)} {'✅' if len(recent) > 50 else '❌'} (soglia >50/24h)")

    # Ultimi 10 record per ispezione
    print(f"\n=== ULTIMI 10 RECORD ===")
    for r in sorted(with_mijia, key=lambda x: x["timestamp"])[-10:]:
        print(f"  {r['timestamp']} | Fancoil: {r['fancoil_temp']:.1f}°C/{r['fancoil_hum']:.1f}% | "
              f"Mijia: {r['mijia_temp']:.1f}°C/{r['mijia_rh']:.1f}% | "
              f"Diff: {r['fancoil_temp']-r['mijia_temp']:.2f}°C/{r['fancoil_hum']-r['mijia_rh']:.2f}% | "
              f"Off24h: {r['off_t']:.2f}°C/{r['off_rh']:.2f}%")


def main():
    # Trova tutti i file log
    log_files = sorted(LOG_DIR.glob("fancoil_events*.log"))
    if not log_files:
        print(f"Nessun file log trovato in {LOG_DIR}")
        sys.exit(1)

    print(f"Trovati {len(log_files)} file log:")
    for f in log_files:
        print(f"  {f.name} ({f.stat().st_size/1024:.0f} KB)")

    # Parsa tutti i file
    all_records = []
    for f in log_files:
        records = parse_log_file(f)
        all_records.extend(records)
        print(f"  {f.name}: {len(records)} state dump corridoio")

    # Ordina per timestamp
    all_records.sort(key=lambda x: x["timestamp"])

    # Analizza
    analyze_records(all_records)


if __name__ == "__main__":
    main()