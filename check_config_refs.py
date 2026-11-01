#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_config_refs.py - coerenza della configurazione generata (sola lettura).

1) INCLUDE: confronta le righe '!include ...' del master dei template con i file presenti su disco.
   Segnala i file generati ma NON inclusi (non vengono mai caricati, senza alcun errore nel log) e gli
   include che puntano a file mancanti.
2) RIFERIMENTI: raccoglie gli entity_id citati nei YAML/J2 e li confronta col recorder:
   mai registrata / muta da ore / ultimo stato unavailable. Evidenzia riferimenti a entita' orfane
   (es. rinominate) e quali file le usano.

Uso:  export HA_DB_URL='mysql+pymysql://UTENTE:PASSWORD@192.168.0.3:3306/homeassistant'
      python3 check_config_refs.py --config /home/carlo/docker/homeassistant/config [--hours 24] [--out riferimenti.md]
Senza DB (solo controllo include):  python3 check_config_refs.py --config ... --no-db
"""
import argparse, os, re, sys, time
from collections import defaultdict
from pathlib import Path

DOMAINS = ("sensor|binary_sensor|input_boolean|input_number|input_select|input_text|input_button|input_datetime|"
           "switch|climate|automation|cover|number|select|button|light|script|scene|person|weather|sun|fan")
ENT = re.compile(r"(?<![\w.%])((?:" + DOMAINS + r")\.[a-z0-9_]+)(?![\w.]*\()")
INC = re.compile(r"!include(?:_dir_(?:merge_list|merge_named|named|list))?\s+([^\s#]+)")


def strip_comments(txt):
    txt = re.sub(r"\{#.*?#\}", "", txt, flags=re.S)
    return "\n".join(l for l in txt.splitlines() if not l.lstrip().startswith("#"))


def check_includes(cfg):
    out = ["## 1. Include del master dei template\n"]
    master = cfg / "yaml_generator" / "fancoil_templates_master.yaml"
    if not master.exists():
        trovati = sorted(cfg.rglob("fancoil_templates_master.yaml"))
        if trovati:
            master = trovati[0]
            out.append(f"_master trovato in un'altra posizione: {master}_\n")
        else:
            elenco = ", ".join(sorted(p.name for p in cfg.iterdir())[:25])
            return out + [f"_master non trovato sotto {cfg}. Contenuto della cartella: {elenco}_\n"], []
    base = master.parent
    included_files, included_dirs, missing = set(), set(), []
    for line in master.read_text(encoding="utf-8").splitlines():
        m = INC.search(line)
        if not m or line.lstrip().startswith("#"):
            continue
        p = (base / m.group(1)).resolve()
        if "_dir_" in line:
            included_dirs.add(p)
            if not p.is_dir():
                missing.append(str(p.relative_to(cfg.resolve())))
        else:
            included_files.add(p)
            if not p.exists():
                missing.append(str(p.relative_to(cfg.resolve())))
    out.append(f"- Include a file singolo: {len(included_files)}; a directory: {len(included_dirs)}\n")
    not_inc = []
    for d in sorted(base.glob("managed_*")):
        if not d.is_dir():
            continue
        if d.resolve() in included_dirs:
            continue                       # directory caricata per intero
        for f in sorted(d.glob("*.yaml")):
            if f.resolve() not in included_files:
                not_inc.append(str(f.relative_to(base)))
    out.append(f"- Include verso file/directory MANCANTI: {len(missing)}\n")
    for m_ in missing:
        out.append(f"  - {m_}\n")
    out.append(f"- File generati in managed_* ma NON inclusi nel master: {len(not_inc)}\n")
    for n in not_inc:
        out.append(f"  - {n}\n")
    return out, not_inc


def collect_refs(cfg):
    refs = defaultdict(set)
    roots = [cfg / "yaml_generator", cfg / "automations", cfg / "packages", cfg / "sql_sensors", cfg / "configuration.yaml"]
    files = []
    for r in roots:
        if r.is_file():
            files.append(r)
        elif r.is_dir():
            files += [p for p in r.rglob("*") if p.suffix in (".yaml", ".j2") and "__pycache__" not in str(p)]
    for f in files:
        try:
            txt = strip_comments(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        for m in ENT.finditer(txt):
            e = m.group(1)
            if "%%" in e or e.endswith("_"):
                continue
            refs[e].add(str(f.relative_to(cfg)))
    return refs


def check_refs(cfg, refs, db_url, hours):
    from sqlalchemy import bindparam, create_engine, text
    eng = create_engine(db_url, pool_pre_ping=True)
    since = time.time() - hours * 3600
    ents = sorted(refs)
    res = {}
    with eng.connect() as c:
        have = {r[0] for r in c.execute(text("SELECT entity_id FROM states_meta")).fetchall()}
        sql = text("SELECT sm.entity_id, MAX(s.last_updated_ts) FROM states s JOIN states_meta sm ON s.metadata_id = sm.metadata_id "
                   "WHERE sm.entity_id IN :e GROUP BY sm.entity_id").bindparams(bindparam("e", expanding=True))
        last_ts = {}
        present = [e for e in ents if e in have]
        for i in range(0, len(present), 200):
            for e, ts in c.execute(sql, {"e": present[i:i + 200]}).fetchall():
                last_ts[e] = ts
        sql2 = text("SELECT s.state FROM states s JOIN states_meta sm ON s.metadata_id = sm.metadata_id WHERE sm.entity_id = :e "
                    "ORDER BY s.last_updated_ts DESC LIMIT 1")
        for e in ents:
            if e not in have:
                res[e] = ("MAI_REGISTRATA", None)
            elif last_ts.get(e) is None or last_ts[e] < since:
                st = c.execute(sql2, {"e": e}).scalar()
                res[e] = ("MUTA", st)
            else:
                st = c.execute(sql2, {"e": e}).scalar()
                res[e] = ("UNAVAILABLE", st) if st in ("unavailable", "unknown") else ("OK", st)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--hours", type=float, default=24)
    ap.add_argument("--db", default=os.environ.get("HA_DB_URL"))
    ap.add_argument("--no-db", action="store_true")
    ap.add_argument("--out", default="riferimenti.md")
    a = ap.parse_args()
    cfg = Path(a.config)
    if not cfg.is_dir():
        sys.exit(f"ERRORE: la cartella --config non esiste: {cfg}\n"
                 "Se esegui lo script in Docker, la cartella dell'host non e' visibile: monta il volume, ad esempio\n"
                 "  docker run --rm -it --network host -v /home/carlo/docker/homeassistant/config:/config:ro -v \"$PWD\":/w -w /w "
                 "-e HA_DB_URL=... python:3.12-slim bash -c 'pip install -q pandas sqlalchemy pymysql && python check_config_refs.py --config /config'")
    parts = ["# Controllo configurazione\n"]
    inc_out, _ = check_includes(cfg)
    parts += inc_out
    refs = collect_refs(cfg)
    if not refs:
        parts.append("\n## 2. Riferimenti a entita'\n\n**Nessun file letto o nessun entity_id trovato**: controlla il percorso --config "
                     "(cartella che contiene configuration.yaml, yaml_generator/, automations/).\n")
        Path(a.out).write_text("".join(parts), encoding="utf-8")
        print(f"ATTENZIONE: 0 riferimenti trovati sotto {cfg}; scritto {a.out}")
        sys.exit(2)
    parts.append(f"\n## 2. Riferimenti a entita' ({len(refs)} entity_id citati nei file)\n")
    if a.no_db or not a.db:
        parts.append("_DB non indicato: controllo dei riferimenti saltato._\n")
    else:
        res = check_refs(cfg, refs, a.db, a.hours)
        cnt = defaultdict(int)
        for st, _ in res.values():
            cnt[st] += 1
        parts.append("- " + ", ".join(f"{k}: {v}" for k, v in sorted(cnt.items())) + f" (finestra: ultime {a.hours:g} h)\n")
        for label, title in (("MAI_REGISTRATA", "Mai registrate nel recorder (nome sbagliato o entita' mai creata)"),
                             ("UNAVAILABLE", "Ultimo stato unavailable/unknown"),
                             ("MUTA", "Registrate ma senza aggiornamenti nel periodo")):
            rows = [(e, st, sorted(refs[e])) for e, (s, st) in res.items() if s == label]
            if not rows:
                continue
            parts.append(f"\n**{title}** ({len(rows)}):\n\n| entita' | ultimo stato | citata in |\n|---|---|---|\n")
            for e, st, fl in rows[:60]:
                parts.append(f"| {e} | {st if st is not None else '-'} | {', '.join(fl[:3])}{' ...' if len(fl) > 3 else ''} |\n")
    Path(a.out).write_text("".join(parts), encoding="utf-8")
    print(f"scritto {a.out}")


if __name__ == "__main__":
    main()
