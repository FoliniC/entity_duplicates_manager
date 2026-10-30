#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ha_clima_diagnostica.py  -  report compatto per valutare il sistema clima/finestre.

Legge SOLO (SELECT) il recorder di Home Assistant (MariaDB o SQLite, schema con
states_meta) e, opzionalmente, fa una sonda su InfluxDB. Non scrive nulla e non
stampa credenziali. Produce un unico file Markdown (di solito 15-30 KB) da incollare
in chat al posto dell'export completo.

Uso tipico (sul server dove il DB e' raggiungibile):
    pip install pandas numpy sqlalchemy pymysql            # + influxdb-client per --influx
    export HA_DB_URL='mysql+pymysql://UTENTE:PASSWORD@192.168.0.3:3306/homeassistant'
    python3 ha_clima_diagnostica.py --days 10 --out report_clima.md
    # con sonda Influx (lunghezza storico/retention e domini presenti):
    export INFLUX_URL=http://192.168.0.3:8086 INFLUX_TOKEN=... INFLUX_ORG=ViaGrande50 INFLUX_BUCKET=HAData
    python3 ha_clima_diagnostica.py --days 10 --influx --out report_clima.md

Opzioni utili:  --rooms cucina,bagno   --extra-entity binary_sensor.contact_cucina_not_used
                --pressure 980 (hPa, per ricalcolare omega)   --skip-footprint
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
from sqlalchemy import bindparam, create_engine, text

VERSION = "1.3"
UNAV = {"unavailable", "unknown", "", "none", "None"}
APRI = {"apri", "apri_se_riparata", "mantieni_aperta"}
APRI_STRICT = {"apri", "apri_se_riparata"}

ROOMS = {
    "cucina": dict(contact="binary_sensor.contact_cucina_contact_cucina", th="sensor.th1a_humidity", window=True),
    "camera_grande": dict(contact="binary_sensor.finestra_camera_grande_finestra_camera_grande", th="sensor.th2b_humidity", window=True),
    "camera": dict(contact=None, th="sensor.th3c_humidity", window=True),
    "corridoio": dict(contact=None, th=None, window=False),
    "bagno": dict(contact=None, th=None, window=True),
    "sala": dict(contact=None, th=None, window=True),
}
GLOBAL = [
    "sensor.omega_esterno", "sensor.castionetto_precipitazione",
    "sensor.meteo_castionetto_umidita", "input_boolean.verifica_mode",
]
EXT = "sensor.omega_esterno"
ATTR_KEYS = ("advice", "prev", "esito", "esito_base", "analytics", "log", "climate")


# ----------------------------------------------------------------------------
# utilita'
# ----------------------------------------------------------------------------
def log(msg):
    print(msg, file=sys.stderr, flush=True)


def ents(rid):
    r = ROOMS[rid]
    e = {
        "rh_pilota": f"sensor.umidita_{rid}_pilota",
        "rh_fancoil": f"sensor.fancoil_{rid}_humidity",
        "t_reale": f"sensor.temperatura_{rid}_reale_calcolata",
        "t_fancoil": f"sensor.fancoil_{rid}_temperature",
        "omega": f"sensor.omega_{rid}",
        "trend": f"sensor.trend_umidita_{rid}",
        "advice": f"sensor.consiglio_finestra_{rid}",
        "prev": f"sensor.previsione_finestra_{rid}",
        "esito": f"sensor.esito_ultimo_consiglio_finestra_{rid}_con_validazione",
        "esito_base": f"sensor.esito_ultimo_consiglio_finestra_{rid}",
        "analytics": f"sensor.analytics_tuning_{rid}",
        "log": f"sensor.log_attivita_manuali_{rid}",
        "climate": f"climate.controllo_temperatura_{rid}",
        "ib": f"input_boolean.finestra_{rid}_aperta",
    }
    if r["contact"]:
        e["contact"] = r["contact"]
    if r["th"]:
        e["rh_th"] = r["th"]
    for i in range(1, 5):
        e[f"fan{i}"] = f"switch.fancoil_{rid}_switch_{i}"
    return e


def parse_attrs(x):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return {}
    try:
        v = json.loads(x)
        return v if isinstance(v, dict) else {}
    except Exception:
        return {}


def fnum(v):
    try:
        return float(v)
    except Exception:
        return float("nan")


def truthy(v):
    return str(v).strip().lower() == "true"


def fmtv(v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "-"
    if isinstance(v, (float, np.floating)):
        return str(int(v)) if float(v).is_integer() and abs(v) < 1e7 else f"{v:.2f}"
    return str(v)


def md(df, max_rows=40):
    if df is None or len(df) == 0:
        return "_nessun dato_\n"
    df = df.head(max_rows)
    cols = list(df.columns)
    out = ["| " + " | ".join(map(str, cols)) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for row in df.itertuples(index=False):
        out.append("| " + " | ".join(fmtv(v) for v in row) + " |")
    return "\n".join(out) + "\n"


def pct(a):
    a = pd.Series(a).dropna()
    if a.empty:
        return dict(n=0, min=np.nan, p10=np.nan, p50=np.nan, p90=np.nan, max=np.nan)
    return dict(n=len(a), min=a.min(), p10=a.quantile(.1), p50=a.quantile(.5), p90=a.quantile(.9), max=a.max())


def wq(vals, w, q):
    """Quantile pesato (pesi = durata in secondi)."""
    v = np.asarray(vals, float)
    w = np.asarray(w, float)
    m = ~np.isnan(v) & ~np.isnan(w) & (w > 0)
    if not m.any():
        return float("nan")
    v, w = v[m], w[m]
    o = np.argsort(v)
    v, w = v[o], w[o]
    c = np.cumsum(w) / w.sum()
    return float(v[min(int(np.searchsorted(c, q)), len(v) - 1)])


LIM = {"rh_pilota": (10, 95), "rh_fancoil": (10, 95), "rh_th": (10, 95),
       "t_reale": (10, 35), "t_fancoil": (10, 35), "omega": (1, 20)}


# ----------------------------------------------------------------------------
# accesso dati
# ----------------------------------------------------------------------------
def fetch(engine, entities, since_ts, with_attrs=False):
    entities = sorted(set(entities))
    cols = "sm.entity_id AS entity_id, s.state AS state, s.last_updated_ts AS ts"
    join = ""
    if with_attrs:
        cols += ", sa.shared_attrs AS attrs"
        join = " LEFT JOIN state_attributes sa ON s.attributes_id = sa.attributes_id"
    sql = text(
        f"SELECT {cols} FROM states s JOIN states_meta sm ON s.metadata_id = sm.metadata_id{join} "
        "WHERE s.last_updated_ts >= :since AND sm.entity_id IN :ents ORDER BY s.last_updated_ts"
    ).bindparams(bindparam("ents", expanding=True))
    frames = []
    with engine.connect() as c:
        for i in range(0, len(entities), 150):
            frames.append(pd.read_sql(sql, c, params={"since": since_ts, "ents": entities[i:i + 150]}))
    frames = [f for f in frames if len(f)]
    if not frames:
        out = pd.DataFrame(columns=["entity_id", "state", "ts"] + (["a"] if with_attrs else []))
        out["ts"] = pd.to_datetime(out["ts"], utc=True)
        return out
    df = pd.concat(frames, ignore_index=True)
    df["ts"] = pd.to_datetime(df["ts"].astype(float), unit="s", utc=True)
    df["state"] = df["state"].astype(object)
    if with_attrs:
        df["a"] = df["attrs"].map(parse_attrs)
        df = df.drop(columns=["attrs"])
    return df.sort_values("ts", kind="stable").reset_index(drop=True)


def fetch_prior(engine, entities, since_ts):
    """Ultimo stato noto PRIMA dell'inizio del periodo (serve per sensori che scrivono di rado)."""
    entities = sorted(set(entities))
    sql = text(
        "SELECT sm.entity_id AS entity_id, s.state AS state, s.last_updated_ts AS ts, sa.shared_attrs AS attrs "
        "FROM states s JOIN states_meta sm ON s.metadata_id = sm.metadata_id "
        "JOIN (SELECT s2.metadata_id AS mid, MAX(s2.last_updated_ts) AS mx FROM states s2 "
        "      JOIN states_meta m2 ON s2.metadata_id = m2.metadata_id "
        "      WHERE s2.last_updated_ts < :since AND m2.entity_id IN :ents GROUP BY s2.metadata_id) m "
        "  ON s.metadata_id = m.mid AND s.last_updated_ts = m.mx "
        "LEFT JOIN state_attributes sa ON s.attributes_id = sa.attributes_id"
    ).bindparams(bindparam("ents", expanding=True))
    frames = []
    with engine.connect() as c:
        for i in range(0, len(entities), 150):
            frames.append(pd.read_sql(sql, c, params={"since": since_ts, "ents": entities[i:i + 150]}))
    frames = [f for f in frames if len(f)]
    if not frames:
        return pd.DataFrame(columns=["entity_id", "state", "ts", "a"])
    df = pd.concat(frames, ignore_index=True).drop_duplicates("entity_id", keep="last")
    df["ts"] = pd.Timestamp(since_ts, unit="s", tz="UTC")
    df["state"] = df["state"].astype(object)
    df["a"] = df["attrs"].map(parse_attrs)
    return df.drop(columns=["attrs"])


def split(df):
    return {k: v.reset_index(drop=True) for k, v in df.groupby("entity_id")} if len(df) else {}


def intervals(d, end):
    if d is None or d.empty:
        return pd.DataFrame({"ts": pd.Series(dtype="datetime64[ns, UTC]"), "state": [], "end": pd.Series(dtype="datetime64[ns, UTC]"), "sec": []})
    x = d[["ts", "state"]].copy().reset_index(drop=True)
    x["end"] = x["ts"].shift(-1).fillna(end)
    x["sec"] = (x["end"] - x["ts"]).dt.total_seconds().clip(lower=0)
    return x


def shares(iv):
    tot = iv["sec"].sum() if len(iv) else 0
    if tot <= 0:
        return pd.Series(dtype=float)
    return (iv.groupby("state")["sec"].sum() / tot).sort_values(ascending=False)


def unav_share(iv):
    tot = iv["sec"].sum() if len(iv) else 0
    if tot <= 0:
        return float("nan")
    return float(iv.loc[iv["state"].isin(UNAV), "sec"].sum() / tot)


def numeric(d):
    if d is None or d.empty:
        return pd.Series(dtype=float)
    s = pd.to_numeric(d["state"], errors="coerce")
    s.index = d["ts"]
    s = s.dropna()
    return s[~s.index.duplicated(keep="last")]


def to_grid(s, idx, limit=240):
    if s.empty:
        return pd.Series(np.nan, index=idx)
    g = s.resample("1min").last()
    g = g.reindex(g.index.union(idx)).ffill(limit=limit)
    return g.reindex(idx)


def value_at(d, t, col="state"):
    if d is None or d.empty:
        return None
    i = int(d["ts"].searchsorted(t, side="right")) - 1
    return None if i < 0 else d.iloc[i][col]


def attr_at(d, t, key):
    a = value_at(d, t, "a")
    return None if a is None else a.get(key)


def at(grid, t):
    t = t.floor("1min")
    try:
        return float(grid.loc[t])
    except Exception:
        return float("nan")


def omega_calc(t, rh, p_hpa):
    es = 6.112 * np.exp(17.62 * t / (243.12 + t))
    e = rh / 100.0 * es
    return 622.0 * e / (p_hpa - e)


def _sensore_vivo(G, ent):
    """True se l'entita' ha righe e non e' quasi sempre unavailable/unknown."""
    d = G.get(ent)
    if d is None or d.empty:
        return False
    return float(d["state"].isin(UNAV).mean()) < 0.9


# ----------------------------------------------------------------------------
# sezioni del report
# ----------------------------------------------------------------------------
def sec_discovery(engine, G, rooms, extras, since_ts, until, flags):
    expected = set(GLOBAL) | set(extras)
    for rid in rooms:
        expected |= set(ents(rid).values())
    with engine.connect() as c:
        have = {r[0] for r in c.execute(text("SELECT entity_id FROM states_meta")).fetchall()}
        cand_sql = text(
            "SELECT sm.entity_id FROM states_meta sm WHERE "
            "(sm.entity_id LIKE :b OR sm.entity_id LIKE :i) AND "
            "(sm.entity_id LIKE :c1 OR sm.entity_id LIKE :c2 OR sm.entity_id LIKE :c3 OR sm.entity_id LIKE :c4)"
        )
        cand = [r[0] for r in c.execute(cand_sql, dict(b="binary_sensor.%", i="input_boolean.%", c1="%contact%",
                                                        c2="%finestra%", c3="%window%", c4="%porta%")).fetchall()]
    with engine.connect() as c2:
        esito_found = [r[0] for r in c2.execute(text("SELECT entity_id FROM states_meta WHERE entity_id LIKE :p OR entity_id LIKE :q"),
                                                 {"p": "%esito%", "q": "%fancoil_events%"}).fetchall()]
    rows = []
    for e in sorted(expected):
        n = len(G.get(e, []))
        rows.append((e, "si" if e in have else "NO", n))
    missing = [r for r in rows if r[1] == "NO"]
    silent = [r for r in rows if r[1] == "si" and r[2] == 0]
    out = ["## 1. Entita' attese (esistenza e righe nel periodo)\n",
           f"- Attese: {len(rows)}; assenti nel recorder: {len(missing)}; presenti ma senza righe nel periodo: {len(silent)}\n"]
    if missing:
        out.append("**Assenti (mai registrate):** " + ", ".join(r[0] for r in missing) + "\n")
    if silent:
        out.append("**Presenti ma mute nel periodo:** " + ", ".join(r[0] for r in silent) + "\n")
    # candidati finestra/contatto
    cdf = fetch(engine, cand, since_ts) if cand else pd.DataFrame()
    cg = split(cdf) if len(cdf) else {}
    crow = []
    for e in sorted(cand):
        iv = intervals(cg.get(e), until)
        sh = shares(iv)
        crow.append(dict(entita=e, righe=len(cg.get(e, [])), on=sh.get("on", 0.0), off=sh.get("off", 0.0),
                         unavailable=unav_share(iv)))
    out.append("\n**Entita' 'esito' / 'fancoil_events' presenti nel recorder:** " + (", ".join(sorted(esito_found)) or "(nessuna)") + "\n")
    out.append("\n**Candidati contatto/finestra trovati nel recorder** (quota di tempo):\n")
    out.append(md(pd.DataFrame(crow), 40))
    return "\n".join(out), cg


def sec_quality(G, rooms, until, flags):
    rows = []
    for rid in rooms:
        e = ents(rid)
        for k in ["rh_pilota", "rh_fancoil", "rh_th", "t_reale", "t_fancoil", "omega"]:
            if k not in e:
                continue
            d = G.get(e[k])
            if d is None or d.empty:
                continue
            iv = intervals(d, until)
            sr = numeric(d)
            dt = d["ts"].diff().dt.total_seconds().dropna()
            diffs = sr.diff().dropna()
            nz = diffs[diffs != 0].abs()
            lo, hi = LIM[k]
            fuori = int(((sr < lo) | (sr > hi)).sum())
            costante = bool(len(sr) > 50 and sr.nunique() == 1)
            rows.append(dict(stanza=rid, sensore=k, righe=len(d), unavail_pct=100 * unav_share(iv),
                             upd_med_s=dt.median() if len(dt) else np.nan,
                             p1=sr.quantile(.01) if len(sr) else np.nan, p50=sr.median() if len(sr) else np.nan,
                             p99=sr.quantile(.99) if len(sr) else np.nan, fuori_range=fuori,
                             fuori_pct=100 * fuori / len(sr) if len(sr) else np.nan, zeri=int((sr == 0).sum()),
                             costante=costante, step_p50=nz.median() if len(nz) else np.nan))
            if costante:
                flags.append(f"{rid}: {k} e' CONGELATO a {sr.iloc[0]:g} per tutto il periodo ({len(sr)} campioni)")
            if fuori > 0 and len(sr) and fuori / len(sr) > 0.001:
                flags.append(f"{rid}: {k} ha {fuori} campioni fuori range plausibile [{lo},{hi}] ({100 * fuori / len(sr):.2f}%)")
            if (sr == 0).sum() > 0 and k in ("t_reale", "rh_pilota"):
                flags.append(f"{rid}: {k} vale 0 in {int((sr == 0).sum())} campioni")
    return "## 2. Qualita' dei sensori\n\n" + md(pd.DataFrame(rows), 80) + \
        "\n_fuori_range: T 10-35 C, RH 10-95%, omega 1-20 g/kg; costante = un solo valore per tutto il periodo; p1/p99 = percentili._\n"


def window_source(G, e):
    for key in ("contact", "ib"):
        ent = e.get(key)
        d = G.get(ent) if ent else None
        if d is not None and d["state"].isin(["on", "off"]).any():
            return ent, d
    return None, None


def build_open_events(G, rooms, until):
    ev, ivs, known, src_rows = [], {}, {}, []
    for rid in rooms:
        e = ents(rid)
        ent, d = window_source(G, e)
        ivs[rid] = []
        if not ROOMS[rid]["window"]:
            known[rid] = True
            src_rows.append(dict(stanza=rid, fonte="(nessuna finestra)", aperture=0, durata_med_min=np.nan,
                                 durata_p90_min=np.nan, tempo_aperta_pct=np.nan, unavail_pct=np.nan))
            continue
        known[rid] = ent is not None
        if ent is None:
            src_rows.append(dict(stanza=rid, fonte="NESSUN DATO", aperture=0, durata_med_min=np.nan,
                                 durata_p90_min=np.nan, tempo_aperta_pct=np.nan, unavail_pct=np.nan))
            continue
        iv = intervals(d, until)
        on = iv[iv["state"] == "on"]
        for r in on.itertuples():
            nxt = iv[iv["ts"] == r.end]
            reason = str(nxt["state"].iloc[0]) if len(nxt) else "fine_dati"
            ev.append(dict(room=rid, t0=r.ts, t1=r.end, dur=r.sec / 60.0, end_reason=reason, src=ent))
            ivs[rid].append((r.ts, r.end))
        tot = iv["sec"].sum()
        src_rows.append(dict(stanza=rid, fonte=ent, aperture=len(on), durata_med_min=on["sec"].median() / 60 if len(on) else np.nan,
                             durata_p90_min=on["sec"].quantile(.9) / 60 if len(on) else np.nan,
                             tempo_aperta_pct=100 * on["sec"].sum() / tot if tot else np.nan, unavail_pct=100 * unav_share(iv)))
    return pd.DataFrame(ev), ivs, known, pd.DataFrame(src_rows)


def compress(d, until):
    """Righe consecutive con lo stesso stato -> episodi."""
    iv = intervals(d, until)
    if iv.empty:
        return iv
    g = (iv["state"] != iv["state"].shift()).cumsum()
    return iv.groupby(g).agg(state=("state", "first"), ts=("ts", "first"), end=("end", "last"),
                             sec=("sec", "sum")).reset_index(drop=True)


def debounce_changes(ep, min_sec):
    keep = ep[ep["sec"] >= min_sec]["state"].tolist()
    n, prev = 0, None
    for st in keep:
        if prev is not None and st != prev:
            n += 1
        prev = st
    return n


def sec_advice(G, rooms, until, flags):
    out = ["## 4. Consiglio finestra (albero decisionale)\n"]
    summ, deb, eff_rows = [], [], []
    ext = G.get(EXT)
    ext_t = None
    if ext is not None and not ext.empty:
        ext_t = pd.DataFrame({"ts": ext["ts"], "t_ext": [fnum(a.get("temperatura")) for a in ext["a"]]}).dropna()
    days = max(ARGS.days, 0.1)
    for rid in rooms:
        d = G.get(ents(rid)["advice"])
        if d is None or d.empty:
            continue
        ep = compress(d, until)
        tot = ep["sec"].sum()
        sh = (ep.groupby("state")["sec"].sum() / tot).sort_values(ascending=False) if tot else pd.Series(dtype=float)
        top = ", ".join(f"{k} {100 * v:.0f}%" for k, v in sh.head(5).items())
        st, sc = ep["state"].tolist(), ep["sec"].tolist()
        rientri = sum(1 for i in range(1, len(st) - 1) if st[i - 1] == st[i + 1] and sc[i] < 60)
        summ.append(dict(stanza=rid, cambi_al_giorno=(len(ep) - 1) / days, episodi_lt60s_pct=100 * float(np.mean(ep["sec"] < 60)),
                         rientri_ABA_lt60s=rientri, dwell_med_s=ep["sec"].median(), stati_tempo=top))
        deb.append(dict(stanza=rid, grezzi=(len(ep) - 1) / days, **{f"min{x}s": debounce_changes(ep, x) / days for x in (30, 60, 120, 300)}))
        if ep["sec"].median() < 60:
            flags.append(f"{rid}: il consiglio cambia stato ogni {ep['sec'].median():.0f}s (mediana): glitch da trigger multipli, serve debounce")
        iv = intervals(d, until)
        a = pd.DataFrame(list(d["a"]))
        a["state"] = d["state"].reset_index(drop=True)
        a["ts"] = d["ts"].reset_index(drop=True)
        a["sec"] = iv["sec"].reset_index(drop=True)
        a["dw"] = pd.to_numeric(a.get("delta_omega"), errors="coerce")
        a["calo"] = pd.to_numeric(a.get("calo_umidita_previsto"), errors="coerce")
        a["imp"] = a.get("impianto_attivo", pd.Series([None] * len(a))).map(truthy)
        sub = a[a["state"].isin(APRI_STRICT)]
        for imp, g in sub.groupby("imp"):
            stab = g[g["sec"] >= 30]
            eff_rows.append(dict(stanza=rid, impianto=bool(imp), ore_apri=g["sec"].sum() / 3600,
                                 dw_min_grezzo=g["dw"].min(), dw_min_stabile30s=stab["dw"].min() if len(stab) else np.nan,
                                 dw_p10_t=wq(g["dw"], g["sec"], .1), dw_p50_t=wq(g["dw"], g["sec"], .5),
                                 calo_min_stab=stab["calo"].min() if len(stab) else np.nan, calo_p50_t=wq(g["calo"], g["sec"], .5)))
        if ext_t is not None and len(sub):
            m = pd.merge_asof(sub[["ts", "sec"]].sort_values("ts"), ext_t.sort_values("ts"), on="ts")
            hot, cold = m.loc[m["t_ext"] > 27, "sec"].sum() / 3600, m.loc[m["t_ext"] < 3, "sec"].sum() / 3600
            if hot or cold:
                flags.append(f"{rid}: consiglio 'apri' per {hot:.1f} h con T_ext >27C e {cold:.1f} h con T_ext <3C (nessun vincolo termico)")
    out.append(md(pd.DataFrame(summ)))
    out.append("\n**Cambi al giorno se si ignorano gli stati piu' brevi di N secondi** (debounce):\n")
    out.append(md(pd.DataFrame(deb)))
    out.append("\n**Soglie effettive quando consiglia 'apri/apri_se_riparata'** (pesate sul tempo; 'stabile' = righe che durano >= 30 s):\n")
    out.append(md(pd.DataFrame(eff_rows)))
    return "\n".join(out)


def sec_esito(G, rooms, until, flags, key="esito",
              title="5. Esito ultimo consiglio, sensore '_con_validazione' (Layer 2)"):
    session_keys = ["consiglio_valutato", "ora_inizio_valutazione", "umidita_inizio", "tipo_azione",
                    "esito_15m", "esito_30m", "esito_60m"]
    base_cols = ["stanza", "stato"] + session_keys + [
        "troppo_vecchi_pct", "eta_dati_med", "eta_dati_sentinella",
        "ultima_aggiornamento_na", "note_moda",
    ]
    rows, keyrows = [], []
    for rid in rooms:
        ent = ents(rid)[key]
        d = G.get(ent)
        if d is None or d.empty:
            rows.append(dict(stanza=rid, righe=0, stati="(nessuna riga)",
                             transizioni=0, efficace=0, inefficace=0,
                             in_corso=0, unavailable_pct=np.nan, restored=False))
            continue

        # --- stato di salute del sensore -----------------------------------
        n_unav = int(d["state"].isin(UNAV).sum())
        uav_pct = 100.0 * n_unav / len(d)
        is_dead = uav_pct > 90.0
        has_restored = any(truthy(a.get("restored")) for a in d["a"])

        chg = d[d["state"] != d["state"].shift()]
        vc = chg["state"].value_counts()
        sh = shares(intervals(d, until))
        rows.append(dict(
            stanza=rid, righe=len(d),
            stati=", ".join(f"{k} {100 * v:.0f}%" for k, v in sh.head(4).items()),
            transizioni=len(chg),
            efficace=int(vc.get("efficace", 0)),
            inefficace=int(vc.get("inefficace", 0)),
            in_corso=int(vc.get("in_corso", 0)),
            unavailable_pct=uav_pct, restored=has_restored,
        ))

        if is_dead:
            tag = "unavailable/restored" if has_restored else "quasi sempre unavailable"
            flags.append(
                f"{rid} [{key}]: sensore {ent} e' {tag} ({uav_pct:.0f}% del tempo)"
                + (" — entita' orfana (rimossa dalla config, stato ripristinato)" if has_restored else "")
            )
            keyrows.append(dict(
                stanza=rid, stato=tag,
                troppo_vecchi_pct=np.nan, eta_dati_med=np.nan,
                eta_dati_sentinella=False, ultima_aggiornamento_na=False,
                note_moda="-", **{k: 0 for k in session_keys},
            ))
            continue

        # --- attributi di sessione e qualita' dato -------------------------
        keys = {}
        for a in d["a"]:
            for k in a:
                keys[k] = keys.get(k, 0) + 1
        present = {k: keys.get(k, 0) for k in session_keys}

        old = [fnum(a.get("eta_dati_minuti")) for a in d["a"]]
        valid_old = [v for v in old
                     if not (isinstance(v, float) and math.isnan(v))]
        eta_sentinella = bool(valid_old and len(set(valid_old)) == 1
                              and valid_old[0] >= 999)
        eta_med = float(np.median(valid_old)) if valid_old else np.nan

        too_old_pct = 100.0 * float(np.mean(
            [truthy(a.get("dati_troppo_vecchi")) for a in d["a"]]))

        notes = pd.Series([a.get("note_validazione") for a in d["a"]]).dropna()
        note_mode = notes.mode().iloc[0] if len(notes) else "-"

        ult = [a.get("ultima_aggiornamento_dati") for a in d["a"]]
        ult_all_na = bool(ult) and all(v in (None, "N/A", "n/a", "") for v in ult)

        stuck = float(sh.get("in_attesa", 0.0) + sh.get("in_corso", 0.0)
              + sh.get("non_valutabile", 0.0))

        keyrows.append(dict(
            stanza=rid, stato="vivo",
            **present,
            troppo_vecchi_pct=too_old_pct,
            eta_dati_med=eta_med,
            eta_dati_sentinella=eta_sentinella,
            ultima_aggiornamento_na=ult_all_na,
            note_moda=note_mode,
        ))

        # --- flag diagnostici ---------------------------------------------
        if stuck > 0.95:
            stati_bloccati = ", ".join(
                f"{k} {100*sh.get(k,0):.0f}%"
                for k in ("in_attesa", "in_corso", "non_valutabile") if sh.get(k, 0) > 0
            )
            flags.append(
                f"{rid} [{key}]: sensore in stato di non-valutazione "
                f"({100*stuck:.0f}% del tempo: {stati_bloccati}) — la sessione non si completa mai"
                + (f" (note_validazione={note_mode!r})" if note_mode and note_mode != "-" else "")
            )
        if eta_sentinella:
            flags.append(
                f"{rid} [{key}]: eta_dati_minuti costante a {valid_old[0]:.0f} (sentinella) "
                f"— 'umidita_prima' mai catturata (fotografia 'prima' congelata a invalido)"
            )
        if ult_all_na and len(d) > 10:
            flags.append(
                f"{rid} [{key}]: 'ultima_aggiornamento_dati' sempre N/A "
                f"— timestamp di sessione mai scritto"
            )
        if too_old_pct >= 95 and not eta_sentinella:
            flags.append(
                f"{rid} [{key}]: dati_troppo_vecchi=true nel {too_old_pct:.0f}% delle righe"
            )
        if sum(present.values()) == 0 and key == "esito":
            flags.append(
                f"{rid} [{key}]: nessun attributo di sessione scritto "
                f"(consiglio_valutato, ora_inizio_valutazione, umidita_inizio, ...)"
            )
        if int(vc.get("efficace", 0)) + int(vc.get("inefficace", 0)) == 0 and stuck < 0.95:
            flags.append(
                f"{rid} [{key}]: nessuna transizione verso efficace/inefficace nel periodo"
            )

    tbl_rows = pd.DataFrame(rows)
    tbl_keys = pd.DataFrame(keyrows, columns=base_cols) if keyrows else pd.DataFrame(columns=base_cols)
    return (f"## {title}\n\n" + md(tbl_rows)
            + "\n**Stato sensore e attributi di sessione/qualita'** (0 = mai valorizzati):\n\n"
            + md(tbl_keys))


def sec_analytics(G, rooms, flags):
    rows = []
    for rid in rooms:
        e = ents(rid)
        da, dl, dp = G.get(e["analytics"]), G.get(e["log"]), G.get(e["prev"])
        r = dict(stanza=rid)
        if da is not None and not da.empty:
            distinct = len({json.dumps(a, sort_keys=True) for a in da["a"]})
            vs = {}
            for a in da["a"]:
                for k, v in a.items():
                    vs.setdefault(k, set()).add(json.dumps(v, sort_keys=True)[:30])
            var = "; ".join(f"{k}({len(v)}): {','.join(sorted(v)[:3])}" for k, v in vs.items() if len(v) > 1)
            last = da["a"].iloc[-1]
            r.update(analytics_righe=len(da), attr_distinti=distinct, override_rate=last.get("override_rate"),
                     accuracy=last.get("consiglio_accuracy"), pred_count=last.get("prediction_count"),
                     f_rh=last.get("prediction_factor_humidity"), attributi_variabili=var[:160] or "-")
            if distinct <= 2 and not (pd.to_numeric(pd.Series([last.get("prediction_count")]), errors="coerce").fillna(0) > 0).any():
                flags.append(f"{rid}: analytics_tuning praticamente fermo (prediction_count=0, fattori=1.0)")
        else:
            r.update(analytics_righe=0)
        if dl is not None and not dl.empty:
            vc = dl["state"].value_counts()
            r.update(log_stati=", ".join(f"{k} {v}" for k, v in vc.head(5).items()))
        if dp is not None and not dp.empty:
            h = pd.to_numeric(pd.Series([a.get("horizon_minutes") for a in dp["a"]]), errors="coerce")
            r.update(prev_h_p50=h.median(), prev_h_8min_pct=100 * (h == 8).mean())
        rows.append(r)
    return "## 6. Analytics, log manuale e previsione\n\n" + md(pd.DataFrame(rows)) + \
        "\n_attributi_variabili = attributi di analytics_tuning che assumono piu' valori nel periodo (n valori distinti: esempi)._\n"


def sec_events(G, rooms, until, p_hpa, flags, tz):
    ev, ivs, known, src = build_open_events(G, rooms, until)
    out3 = ["## 3. Finestre: fonte, aperture, tempo non disponibile\n", md(src)]
    for r_ in src.itertuples():
        if r_.fonte == "NESSUN DATO":
            flags.append(f"{r_.stanza}: nessuna fonte di stato finestra con dati (ne' contatto ne' input_boolean)")
        elif isinstance(r_.unavail_pct, float) and r_.unavail_pct > 20:
            flags.append(f"{r_.stanza}: la fonte finestra ({r_.fonte}) e' unavailable per {r_.unavail_pct:.0f}% del tempo")
    out = []
    idx = pd.date_range(until - timedelta(days=ARGS.days + 1), until, freq="1min", tz="UTC").floor("1min")
    omg = {rid: to_grid(numeric(G.get(ents(rid)["omega"])), idx) for rid in rooms}
    rhg = {rid: to_grid(numeric(G.get(ents(rid)["rh_pilota"])), idx) for rid in rooms}
    tg = {rid: to_grid(numeric(G.get(ents(rid)["t_reale"])), idx) for rid in rooms}
    ext_d = G.get(EXT)
    omext = to_grid(numeric(ext_d), idx)
    if ev.empty:
        out.append("\n## 7. Efficacia delle aperture (osservata)\n\n_Nessuna apertura finestra nel periodo: impossibile valutare efficacia._\n")
        return "\n".join(out3), "\n".join(out), ev
    rows = []
    for r in ev.itertuples():
        rid, t0 = r.room, r.t0
        e = ents(rid)
        advd = G.get(e["advice"])
        prior = set()
        if advd is not None and not advd.empty:
            w = advd[(advd["ts"] <= t0) & (advd["ts"] >= t0 - timedelta(minutes=30))]
            prior = set(w["state"])
            cur = value_at(advd, t0)
            if cur:
                prior.add(cur)
        concord = bool(prior & APRI_STRICT)
        cl = G.get(e["climate"])
        hv = attr_at(cl, t0, "hvac_action") if cl is not None else None
        fan_on = any(value_at(G.get(e.get(f"fan{i}")), t0) == "on" for i in range(1, 5))
        imp = (hv in ("cooling", "heating", "drying")) or fan_on
        text_ = attr_at(ext_d, t0, "temperatura") if ext_d is not None else None
        row = dict(stanza=rid, inizio=t0.tz_convert(tz).strftime("%m-%d %H:%M"), dur_min=r.dur, fine=r.end_reason,
                   consiglio_apri_prima=concord, impianto=bool(imp), t_ext=fnum(text_),
                   dw0=at(omg[rid], t0) - at(omext, t0))
        for k in (15, 30, 60):
            t1 = t0 + timedelta(minutes=k)
            ok = t1 <= until
            dwr = (at(omg[rid], t1) - at(omg[rid], t0)) if ok else np.nan
            drh = (at(rhg[rid], t1) - at(rhg[rid], t0)) if ok else np.nan
            dtt = (at(tg[rid], t1) - at(tg[rid], t0)) if ok else np.nan
            ctr = []
            for o in rooms:
                if o == rid or not known.get(o):
                    continue
                if any(s < t1 and f > t0 - timedelta(minutes=10) for s, f in ivs.get(o, [])):
                    continue
                if not ok:
                    continue
                v = at(omg[o], t1) - at(omg[o], t0)
                if not math.isnan(v):
                    ctr.append(v)
            row[f"dOmega{k}"] = dwr
            row[f"dRH{k}"] = drh
            row[f"dT{k}"] = dtt
            row[f"did{k}"] = (dwr - float(np.mean(ctr))) if ctr and not math.isnan(dwr) else np.nan
            row[f"n_ctrl{k}"] = len(ctr)
        # confronto con la previsione (se presente)
        dp = G.get(e["prev"])
        h = fnum(attr_at(dp, t0, "horizon_minutes")) if dp is not None else float("nan")
        pr = fnum(attr_at(dp, t0, "humidity_delta_predicted")) if dp is not None else float("nan")
        if not math.isnan(h) and t0 + timedelta(minutes=h) <= until:
            th = t0 + timedelta(minutes=h)
            row["prev_h"] = h
            row["prev_dRH"] = pr
            row["real_dRH_h"] = at(rhg[rid], th) - at(rhg[rid], t0)
        rows.append(row)
    E = pd.DataFrame(rows)
    if len(E):
        E["sys_eff"] = E["dRH60"] <= -2.0
        E["fis_eff"] = E["did60"] < -0.3
    # aggregati
    agg = []
    for name, g in [("tutte", E), ("dopo consiglio apri", E[E["consiglio_apri_prima"]]), ("senza consiglio", E[~E["consiglio_apri_prima"]]), ("durata < 1 min", E[E["dur_min"] < 1]), ("durata >= 5 min", E[E["dur_min"] >= 5]), ("durata >= 5 min e consiglio", E[(E["dur_min"] >= 5) & E["consiglio_apri_prima"]]), ("durata >= 5 min senza consiglio", E[(E["dur_min"] >= 5) & ~E["consiglio_apri_prima"]])]:
        v = g.dropna(subset=["dRH60"])
        w = g.dropna(subset=["did60"])
        agg.append(dict(gruppo=name, n=len(g), dur_med=g["dur_min"].median(), con_impianto=int(g["impianto"].sum()),
                        dRH60_med=v["dRH60"].median() if len(v) else np.nan, dOmega60_med=g["dOmega60"].median(),
                        did60_med=w["did60"].median() if len(w) else np.nan, n_did=len(w),
                        eff_regola_RH_pct=100 * v["sys_eff"].mean() if len(v) else np.nan,
                        eff_fisica_pct=100 * w["fis_eff"].mean() if len(w) else np.nan))
    out.append("## 7. Efficacia delle aperture (osservata)\n")
    out.append("did = variazione di omega della stanza meno quella delle altre stanze con finestra chiusa (stesso intervallo). "
               "`eff_regola_RH` applica la regola attuale (RH scende >= 2 punti in 60 min), `eff_fisica` richiede did60 < -0.3 g/kg.\n\n")
    out.append(md(pd.DataFrame(agg)))
    cm = E.dropna(subset=["dRH60", "did60"])
    if len(cm):
        c = pd.crosstab(cm["sys_eff"], cm["fis_eff"])
        out.append("\n**Accordo regola-RH vs fisica (righe: regola, colonne: fisica):**\n\n```\n" + c.to_string() + "\n```\n")
    pv = E.dropna(subset=["prev_dRH", "real_dRH_h"]) if "prev_dRH" in E else pd.DataFrame()
    if len(pv):
        err = (pv["real_dRH_h"] - pv["prev_dRH"])
        out.append(f"\n**Previsione umidita' vs reale all'orizzonte** (n={len(pv)}): errore mediano {err.median():.2f} punti RH, "
                   f"MAE {err.abs().mean():.2f}, correlazione {pv['prev_dRH'].corr(pv['real_dRH_h']):.2f}\n")
    cols = ["stanza", "inizio", "dur_min", "fine", "consiglio_apri_prima", "impianto", "t_ext", "dw0", "dRH30", "dRH60",
            "dOmega30", "dOmega60", "did60", "n_ctrl60"]
    out.append("\n**Ultime 30 aperture** (dRH in punti %, dOmega in g/kg):\n\n")
    out.append(md(E.sort_values("inizio", ascending=False)[cols], 30))
    return "\n".join(out3), "\n".join(out), ev


def sec_compliance(G, rooms, ev, until):
    rows = []
    for rid in rooms:
        d = G.get(ents(rid)["advice"])
        if d is None or d.empty or not ROOMS[rid]["window"]:
            continue
        ep = compress(d, until)
        tot = ep["sec"].sum()
        base = 100 * ep.loc[ep["state"].isin(APRI_STRICT), "sec"].sum() / tot if tot else np.nan
        ap = ep[ep["state"].isin(APRI_STRICT)]
        stab = ap[ap["sec"] >= 60]
        e_r = ev[ev["room"] == rid] if len(ev) else ev
        seguiti = 0
        for r in stab.itertuples():
            if len(e_r) and ((e_r["t0"] >= r.ts) & (e_r["t0"] <= r.end + timedelta(minutes=15))).any():
                seguiti += 1
        rows.append(dict(stanza=rid, episodi_apri_tot=len(ap), episodi_ge60s=len(stab), durata_med_min=stab["sec"].median() / 60 if len(stab) else np.nan,
                         seguiti=seguiti, seguiti_pct=100 * seguiti / len(stab) if len(stab) else np.nan, tempo_in_apri_pct=base))
    return "\n## 8. Consigli 'apri' (episodi >= 60 s) seguiti da un'apertura entro 15 min\n\n" + md(pd.DataFrame(rows)) + \
        "\n_Confronta seguiti_pct con tempo_in_apri_pct: se sono simili, l'apertura non e' correlata al consiglio. Nelle stanze con finestra manuale una mancata registrazione appare come consiglio ignorato._\n"


def sec_consistency(G, rooms, until, p_hpa, tz):
    idx = pd.date_range(until - timedelta(days=ARGS.days), until, freq="5min", tz="UTC").floor("5min")
    rows = []
    for rid in rooms:
        e = ents(rid)
        rh = to_grid(numeric(G.get(e["rh_pilota"])), idx)
        t = to_grid(numeric(G.get(e["t_reale"])), idx)
        om = to_grid(numeric(G.get(e["omega"])), idx)
        r = dict(stanza=rid)
        if "rh_th" in e:
            th = to_grid(numeric(G.get(e["rh_th"])), idx)
            df = (rh - th).abs().dropna()
            r.update(pilota_vs_th_n=len(df), pilota_vs_th_p50=df.median() if len(df) else np.nan,
                     pilota_vs_th_p95=df.quantile(.95) if len(df) else np.nan, oltre15_pct=100 * (df > 15).mean() if len(df) else np.nan)
        calc = omega_calc(t, rh, p_hpa)
        df = (om - calc).dropna()
        r.update(omega_n=len(df), omega_bias_med=df.median() if len(df) else np.nan,
                 omega_abs_p95=df.abs().quantile(.95) if len(df) else np.nan)
        rows.append(r)
    out = ["## 9. Coerenza tra sensori\n", md(pd.DataFrame(rows)),
           f"\n_omega_bias = omega del sensore meno omega ricalcolata (Magnus, {p_hpa:.0f} hPa) da T_reale e RH_pilota, in g/kg._\n"]
    ext = G.get(EXT)
    if ext is not None and not ext.empty:
        t_e = pd.Series([fnum(a.get("temperatura")) for a in ext["a"]])
        h_e = pd.Series([fnum(a.get("umidita")) for a in ext["a"]])
        src = pd.Series([a.get("source", "") for a in ext["a"]]).value_counts()
        om_e = numeric(ext)
        out.append("\n**Esterno (sensor.omega_esterno):** T_ext " + ", ".join(f"{k}={v:.1f}" for k, v in pct(t_e).items() if k != "n") +
                   "; RH_ext " + ", ".join(f"{k}={v:.0f}" for k, v in pct(h_e).items() if k != "n") +
                   "; omega_ext " + ", ".join(f"{k}={v:.2f}" for k, v in pct(om_e).items() if k != "n") +
                   "; fonti: " + ", ".join(f"{k or '(vuota)'} {v}" for k, v in src.head(4).items()) + "\n")
    pr = G.get("sensor.castionetto_precipitazione")
    if pr is not None and not pr.empty:
        s = numeric(pr)
        out.append(f"\n**Pioggia:** {100 * (s > 0).mean():.1f}% dei campioni > 0 (n={len(s)}).\n")
    return "\n".join(out)

def episodes_unav(d, until):
    iv = intervals(d, until)
    if iv.empty:
        return iv
    f = iv["state"].isin(UNAV)
    g = (f != f.shift()).cumsum()
    return iv[f].groupby(g[f]).agg(ts=("ts", "first"), sec=("sec", "sum")).reset_index(drop=True)


def sec_unavail(G, rooms, until, tz, flags):
    srcs = []
    for rid in rooms:
        e = ents(rid)
        srcs += [e.get("contact"), e["rh_fancoil"], e["rh_pilota"]]
    srcs += ["binary_sensor.contact_cucina_not_used", "binary_sensor.finestra_camera_grande_not_used"]
    rows = []
    for ent in dict.fromkeys([x for x in srcs if x]):
        d = G.get(ent)
        if d is None or d.empty:
            continue
        ep = episodes_unav(d, until)
        if ep.empty:
            continue
        hrs = ep["ts"].dt.tz_convert(tz).dt.hour.value_counts().head(3)
        i_max = ep["sec"].idxmax()
        lungo = ep[ep["sec"] > 600]
        rows.append(dict(entita=ent, episodi=len(ep), lt30s=int((ep["sec"] < 30).sum()), med_min=ep["sec"].median() / 60,
                         max_min=ep["sec"].max() / 60, max_inizio=ep.loc[i_max, "ts"].tz_convert(tz).strftime("%m-%d %H:%M"),
                         min_in_episodi_gt10min=lungo["sec"].sum() / 60, ore_inizio_top=", ".join(f"{h}h:{n}" for h, n in hrs.items())))
    return "\n## 9b. Episodi di indisponibilita' (unavailable/unknown)\n\n" + md(pd.DataFrame(rows), 40)


def sec_contacts(G, until):
    pairs = [("binary_sensor.contact_cucina_contact_cucina", "binary_sensor.contact_cucina_not_used"),
             ("binary_sensor.finestra_camera_grande_finestra_camera_grande", "binary_sensor.finestra_camera_grande_not_used")]
    idx = pd.date_range(until - timedelta(days=ARGS.days), until, freq="1min", tz="UTC")

    def on_grid(d):
        sr = pd.Series((d["state"] == "on").astype(float).values, index=d["ts"])
        sr = sr[~sr.index.duplicated(keep="last")].resample("1min").last()
        return sr.reindex(sr.index.union(idx)).ffill().reindex(idx).fillna(0)

    rows = []
    for a, b in pairs:
        da, db = G.get(a), G.get(b)
        if da is None or db is None or da.empty or db.empty:
            continue
        ga, gb = on_grid(da), on_grid(db)
        rows.append(dict(principale=a.split(".")[1][:32], secondaria=b.split(".")[1][:32], on_min_princ=ga.sum(), on_min_sec=gb.sum(),
                         sovrapposti_min=(ga * gb).sum(), eventi_on_princ=int((da["state"] == "on").sum()), eventi_on_sec=int((db["state"] == "on").sum())))
    return "\n## 9c. Contatto principale vs secondo ingresso ('not_used')\n\n" + md(pd.DataFrame(rows)) + \
        "\n_Se i minuti sovrapposti sono pochi e la secondaria ha eventi propri, il secondo ingresso e' cablato a un'altra apertura._\n"


def sec_ext_outliers(G, flags):
    ext = G.get(EXT)
    if ext is None or ext.empty:
        return ""
    t = pd.Series([fnum(a.get("temperatura")) for a in ext["a"]])
    h = pd.Series([fnum(a.get("umidita")) for a in ext["a"]])
    w = pd.to_numeric(ext["state"], errors="coerce").reset_index(drop=True)
    src = pd.Series([a.get("source", "") or "(vuota)" for a in ext["a"]])
    bad = (t > 45) | (t < -30) | (h > 100) | (h < 0) | (w > 30) | (w < 0)
    rows = []
    for k in src.unique():
        m = src == k
        rows.append(dict(source=k, righe=int(m.sum()), anomale=int((bad & m).sum()), t_max=t[m].max(), omega_max=w[m].max(), h_max=h[m].max()))
    if int(bad.sum()):
        flags.append(f"omega_esterno: {int(bad.sum())} righe con valori impossibili (T>45, RH>100, omega>30)")
    return "\n## 9a. Dati esterni: valori impossibili per fonte\n\n" + md(pd.DataFrame(rows)) + "\n"


def sec_footprint(engine, since_ts, rooms, flags):
    like = ["consiglio_finestra", "esito_ultimo", "previsione_finestra", "analytics_tuning", "log_attivita", "climate_advice",
            "finestra_", "omega_", "trend_umidita", "umidita_", "temperatura_"]
    with engine.connect() as c:
        top = pd.read_sql(text(
            "SELECT sm.entity_id AS entita, COUNT(*) AS righe FROM states s JOIN states_meta sm ON s.metadata_id = sm.metadata_id "
            "WHERE s.last_updated_ts >= :since GROUP BY sm.entity_id ORDER BY righe DESC LIMIT 20"), c, params={"since": since_ts})
        tot = c.execute(text("SELECT COUNT(*) FROM states WHERE last_updated_ts >= :since"), {"since": since_ts}).scalar()
        allc = pd.read_sql(text(
            "SELECT sm.entity_id AS entita, COUNT(*) AS righe FROM states s JOIN states_meta sm ON s.metadata_id = sm.metadata_id "
            "WHERE s.last_updated_ts >= :since GROUP BY sm.entity_id"), c, params={"since": since_ts})
    mine = allc[allc["entita"].map(lambda e: any(k in e for k in like) and any(r in e for r in rooms))]
    share = 100 * mine["righe"].sum() / tot if tot else float("nan")
    return ("## 10. Impronta sul recorder\n\n"
            f"- Righe totali nel periodo: {tot}; entita' del sistema clima (nome contiene stanza e sensore tipo): {mine['righe'].sum()} ({share:.1f}%)\n\n"
            + md(top, 20))


def sec_influx(rooms, flags):
    try:
        from influxdb_client import InfluxDBClient
    except Exception:
        return "## 11. Sonda InfluxDB\n\n_influxdb-client non installato (pip install influxdb-client)._\n"
    url = os.environ.get("INFLUX_URL", "http://192.168.0.3:8086")
    token = os.environ.get("INFLUX_TOKEN")
    org = os.environ.get("INFLUX_ORG", "ViaGrande50")
    bucket = os.environ.get("INFLUX_BUCKET", "HAData")
    if not token:
        return "## 11. Sonda InfluxDB\n\n_INFLUX_TOKEN non impostato._\n"
    out = ["## 11. Sonda InfluxDB\n"]
    try:
        with InfluxDBClient(url=url, token=token, org=org, timeout=60000) as cl:
            q = cl.query_api()
            b = q.query(f'buckets() |> filter(fn: (r) => r.name == "{bucket}")')
            for t in b:
                for r in t.records:
                    out.append(f"- Bucket {bucket}: retention = {r.values.get('retentionPeriod')} ns (0 = illimitata)\n")
            ids = []
            t = q.query(f'import "influxdata/influxdb/schema"\nschema.tagValues(bucket: "{bucket}", tag: "entity_id", start: -800d)')
            for tb in t:
                ids += [r.get_value() for r in tb.records]
            doms = pd.Series([i.split(".")[0] for i in ids]).value_counts()
            out.append("- Domini presenti (n. entita'): " + ", ".join(f"{k} {v}" for k, v in doms.items()) + "\n")
            keys = []
            for rid in rooms:
                e = ents(rid)
                keys += [e["rh_pilota"], e["omega"], e["advice"], e["esito"]]
                if "contact" in e:
                    keys.append(e["contact"])
                keys.append(e["ib"])
            keys = [k for k in dict.fromkeys(keys)] + [EXT]
            rows = []
            for k in keys:
                if k not in ids:
                    rows.append(dict(entita=k, presente="NO", primo="-", ultimo="-"))
                    continue
                f = f'from(bucket:"{bucket}") |> range(start:-800d) |> filter(fn:(r)=> r.entity_id == "{k}") |> keep(columns:["_time"]) |> group() '
                first = [r.get_time() for tb in q.query(f + "|> first(column:\"_time\")") for r in tb.records]
                last = [r.get_time() for tb in q.query(f + "|> last(column:\"_time\")") for r in tb.records]
                rows.append(dict(entita=k, presente="si", primo=str(first[0])[:16] if first else "-", ultimo=str(last[0])[:16] if last else "-"))
            out.append("\n" + md(pd.DataFrame(rows), 60))
    except Exception as ex:  # noqa
        out.append(f"\n_Sonda Influx fallita: {type(ex).__name__}: {str(ex)[:200]}_\n")
    return "\n".join(out)


# ----------------------------------------------------------------------------
def parse_since_spec(spec: str) -> pd.Timestamp:
    """Parse time specification: '1h', '30m', '2026-10-28 12:00:00', etc. Returns UTC Timestamp."""
    now = pd.Timestamp.now(tz="UTC").floor("1min")
    spec = spec.strip().lower()
    
    # Relative time: Nh, Nm, Ns, Nd
    m = re.match(r'^(\d+)([hmds])$', spec)
    if m:
        val = int(m.group(1))
        unit = m.group(2)
        if unit == 'h':
            return now - pd.Timedelta(hours=val)
        elif unit == 'm':
            return now - pd.Timedelta(minutes=val)
        elif unit == 's':
            return now - pd.Timedelta(seconds=val)
        elif unit == 'd':
            return now - pd.Timedelta(days=val)
    
    # Absolute time: YYYY-MM-DD HH:MM:SS or YYYY-MM-DD HH:MM or YYYY-MM-DD
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return pd.Timestamp(datetime.strptime(spec, fmt), tz="UTC")
        except ValueError:
            pass
    
    raise ValueError(f"Invalid --since spec: {spec}. Use '1h', '30m', or 'YYYY-MM-DD HH:MM:SS'")

# ----------------------------------------------------------------------------
def main():
    global ARGS
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default=os.environ.get("HA_DB_URL"), help="URL SQLAlchemy del recorder (o env HA_DB_URL)")
    ap.add_argument("--days", type=float, default=10.0, help="Giorni indietro se non si usa --since")
    ap.add_argument("--since", type=str, help="Orario inizio: '1h', '30m', '2026-10-28 12:00:00' (sovrascrive --days)")
    ap.add_argument("--rooms", default="all")
    ap.add_argument("--tz", default="Europe/Rome")
    ap.add_argument("--pressure", type=float, default=980.0)
    ap.add_argument("--extra-entity", action="append", default=[])
    ap.add_argument("--skip-footprint", action="store_true")
    ap.add_argument("--influx", action="store_true")
    ap.add_argument("--out", default="report_clima.md")
    ARGS = ap.parse_args()
    if not ARGS.db:
        sys.exit("Manca l'URL del DB: usa --db oppure la variabile HA_DB_URL")
    rooms = list(ROOMS) if ARGS.rooms == "all" else [r.strip() for r in ARGS.rooms.split(",") if r.strip() in ROOMS]
    tz = ARGS.tz
    until = pd.Timestamp(datetime.now(timezone.utc)).floor("1min")
    if ARGS.since:
        since = parse_since_spec(ARGS.since)
        log(f"Filtro --since: {since.tz_convert(tz).strftime('%Y-%m-%d %H:%M')} ({tz})")
    else:
        since = until - timedelta(days=ARGS.days)
    since_ts = since.timestamp()
    engine = create_engine(ARGS.db, pool_pre_ping=True)

    log("Lettura serie numeriche e stati...")
    want = set(GLOBAL) | set(ARGS.extra_entity)
    for rid in rooms:
        want |= set(ents(rid).values())
    df = fetch(engine, want - {EXT}, since_ts, False)
    attr_want = {ents(rid)[k] for rid in rooms for k in ATTR_KEYS} | {EXT}
    dfa = fetch(engine, attr_want, since_ts, True)
    prior = fetch_prior(engine, (want | attr_want), since_ts)
    if len(prior):
        pa = prior[prior["entity_id"].isin(attr_want)]
        pn = prior[~prior["entity_id"].isin(attr_want)].drop(columns=["a"])
        dfa = pd.concat([pa, dfa], ignore_index=True).sort_values("ts", kind="stable").reset_index(drop=True)
        df = pd.concat([pn, df], ignore_index=True).sort_values("ts", kind="stable").reset_index(drop=True)
    # le entita' con attributi sostituiscono quelle senza
    df = df[~df["entity_id"].isin(attr_want)]
    G = split(df)
    G.update(split(dfa))
    flags = []

    log("Sezioni...")
    s1, cg = sec_discovery(engine, G, rooms, ARGS.extra_entity, since_ts, until, flags)
    for k, v in cg.items():
        G.setdefault(k, v)
    s2 = sec_quality(G, rooms, until, flags)
    s3, s7, ev = sec_events(G, rooms, until, ARGS.pressure, flags, tz)
    # sezione 3 + 7 stanno nello stesso testo; separo l'ordine finale piu' sotto
    s4 = sec_advice(G, rooms, until, flags)
    s5 = sec_esito(G, rooms, until, flags)
    # esito_base: analizza solo le stanze con un sensore vivo.
    # Il Layer 1 e' stato dismesso, ma su alcuni impianti puo' essere
    # ancora attivo: analizzarlo solo dove produce dati reali evita
    # di generare warning All-NaN e falsi allarmi.
    rooms_base = [rid for rid in rooms if _sensore_vivo(G, ents(rid)["esito_base"])]
    if rooms_base:
        s5 += "\n" + sec_esito(
            G, rooms_base, until, flags, key="esito_base",
            title="5b. Esito ultimo consiglio, sensore base (Layer 1, se ancora attivo)",
        )
    else:
        s5 += ("\n## 5b. Esito sensore base (Layer 1)\n\n"
               "_Nessuna stanza ha un sensore `esito_ultimo_consiglio_finestra_<stanza>` "
               "attivo (tutti unavailable/restored): il Layer 1 risulta dismesso. "
               "Sezione saltata; le entita' orfane sono segnalate nella sezione 0._\n")
    s6 = sec_analytics(G, rooms, flags)
    s8 = sec_compliance(G, rooms, ev, until)
    s9 = sec_consistency(G, rooms, until, ARGS.pressure, tz)
    s9b = sec_ext_outliers(G, flags) + sec_unavail(G, rooms, until, tz, flags) + sec_contacts(G, until)
    s10 = "" if ARGS.skip_footprint else sec_footprint(engine, since_ts, rooms, flags)
    s11 = sec_influx(rooms, flags) if ARGS.influx else ""

    # segnali: contatto non disponibile
    if len(ev) == 0:
        flags.append("nessuna apertura finestra registrata nel periodo")
    head = [f"# Report diagnostico clima (v{VERSION})\n",
            (f"Periodo: da {since.tz_convert(tz).strftime('%Y-%m-%d %H:%M')} a {until.tz_convert(tz).strftime('%Y-%m-%d %H:%M')} ({tz}); "
             f"righe lette: {len(df) + len(dfa)}; stanze: {', '.join(rooms)}\n"),
            "## 0. Segnali automatici\n"]
    head += [f"- {f}" for f in dict.fromkeys(flags)] or ["- (nessuno)"]
    head.append("\n")
    parts = head + [s1, s2, s3, s4, s5, s6, s7, s8, s9, s9b, s10, s11]
    report = "\n".join(p for p in parts if p)
    with open(ARGS.out, "w", encoding="utf-8") as f:
        f.write(report)
    log(f"Scritto {ARGS.out} ({len(report) / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
