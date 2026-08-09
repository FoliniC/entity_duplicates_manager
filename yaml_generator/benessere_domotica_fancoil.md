# Benessere Indoor e Controllo Domotico Fancoil
> Guida completa per la gestione ottimale di temperatura, umidità e qualità dell'aria in appartamento

---

## Indice

1. [Parametri di Comfort e Salubrità](#1-parametri-di-comfort-e-salubrità)
2. [Soglie di Rischio](#2-soglie-di-rischio)
3. [Principi di Deumidificazione con Fancoil](#3-principi-di-deumidificazione-con-fancoil)
4. [Impostazioni Ottimali Fancoil](#4-impostazioni-ottimali-fancoil)
5. [Strategia Dinamica di Controllo](#5-strategia-dinamica-di-controllo)
6. [Sensori: Posizionamento e Utilizzo](#6-sensori-posizionamento-e-utilizzo)
7. [Gestione Finestre e Porte](#7-gestione-finestre-e-porte)
8. [Algoritmo Domotico Integrato](#8-algoritmo-domotico-integrato)
9. [Tabelle di Riferimento Rapido](#9-tabelle-di-riferimento-rapido)

---

## 1. Parametri di Comfort e Salubrità

### 1.1 Zona di Comfort (ISO 7730 / ASHRAE 55)

Il comfort termoigrometrico non è un punto fisso ma un'**area** nel diagramma psicrometrico. I valori variano per stagione e attività.

| Parametro | Inverno | Estate | Notte |
|---|---|---|---|
| **Temperatura aria** | 20–22°C | 24–26°C | 18–20°C |
| **Umidità relativa (UR)** | 40–60% | 50–60% | 45–55% |
| **Punto di rugiada target** | 8–11°C | 11–14°C | 8–11°C |
| **Velocità aria massima** | 0.15 m/s | 0.25 m/s | 0.10 m/s |

### 1.2 Perché NON mantenere 22°C tutto l'anno

**In estate** i 22°C sono controindicati:

- **Shock termico**: un delta > 7°C tra interno ed esterno (es. 35°C fuori, 22°C dentro) sollecita fortemente il sistema cardiovascolare
- **Secchezza mucose**: a temperature basse con aria deumidificata le vie aeree si disidratano
- **Blocco acclimatazione**: il corpo non sviluppa i meccanismi di adattamento al caldo (espansione del volume plasmatico, riduzione della soglia di sudorazione)
- **Spreco energetico**: ogni grado in meno in estate = +6–8% di consumo del gruppo refrigeratore

> **Regola pratica**: in estate puntare a **24–26°C** e gestire il comfort abbassando l'**umidità** piuttosto che la temperatura.

**In inverno** i 22°C sono al limite alto:

- La temperatura ottimale invernale (EN 15251) è **20°C**
- Ogni grado sopra i 20°C in riscaldamento = +7–10% di consumo energetico
- Temperature notturne più basse (18–19°C) migliorano la qualità del sonno

### 1.3 Temperatura Operativa vs Temperatura Aria

La temperatura **percepita** dipende anche dalle superfici:

```
T_operativa = (T_aria + T_superfici_medie) / 2
```

- In inverno con pareti fredde: T_operativa è 1–2°C sotto la T_aria → si percepisce più freddo
- In estate con pareti calde: T_operativa è sopra la T_aria → si percepisce più caldo

---

## 2. Soglie di Rischio

### 2.1 Rischi da Umidità Relativa

| Intervallo UR | Condizione | Rischio principale | Soglia critica |
|---|---|---|---|
| **< 25%** | Molto secco | Irritazione mucose, sopravvivenza virale aumentata, elettricità statica | ⛔ Critico |
| **25–40%** | Secco | Lieve disagio mucose, pelle secca | ⚠️ Attenzione |
| **40–60%** | **IDEALE** | Minimo rischio microbiologico, comfort ottimale | ✅ Ottimale |
| **60–65%** | Umido | Acari iniziano a proliferare (soglia riproduttiva ~65%) | ⚠️ Attenzione |
| **65–70%** | Molto umido | Proliferazione acari attiva, rischio muffa su superfici fredde | ⚠️ Intervenire |
| **70–80%** | Pericoloso | Muffe (*Aspergillus*, *Cladosporium*), condensa superfici | ⛔ Pericoloso |
| **> 80%** | Critico | Muffe visibili, micotossine, *Legionella* in impianti, condensa | ⛔ Critico |

> **Nota importante**: la muffa non si forma dove si misura l'umidità, ma dove l'aria è più fredda (angoli, pareti nord, dietro i mobili). In quelle zone l'UR locale può essere **15–20 punti superiore** a quella ambiente.

### 2.2 I Tre Patogeni Principali

**Acari della polvere** (*Dermatophagoides pteronyssinus*)
- Proliferano con T 23–27°C e UR > 65%
- Muoiono con UR < 45% mantenuta per alcune settimane, oppure T > 55°C
- Gli allergeni persistono anche dopo la morte degli acari

**Muffe**
- Germinazione spore: superficie sotto il punto di rugiada locale, UR > 80%
- *Stachybotrys chartarum* (muffa nera): richiede umidità molto elevata e prolungata, produce micotossine gravi

**Virus respiratori**
- Sopravvivono meglio con UR < 40% **oppure** UR > 70% (curva a U)
- Finestra di minor sopravvivenza virale: **UR 50–60%** — coincide con la zona di comfort ideale

### 2.3 Tabella Soglie Operative per il Sistema Domotico

| Parametro | Allarme basso | Zona ideale | Allarme alto |
|---|---|---|---|
| Temperatura (estate) | < 23°C | **24–26°C** | > 28°C |
| Temperatura (inverno) | < 18°C | **20–22°C** | > 23°C |
| Temperatura notturna | < 16°C | **18–20°C** | > 22°C |
| Umidità relativa | < 35% | **45–55%** | > 65% |
| Punto di rugiada | < 6°C | **9–12°C** | > 15°C |
| Delta T interno-esterno | — | < 6°C | > 7°C (shock termico) |

---

## 3. Principi di Deumidificazione con Fancoil

### 3.1 Come Deumidifica un Fancoil

Il fancoil deumidifica perché la superficie della batteria fredda scende al di sotto del **punto di rugiada** dell'aria ambiente. L'umidità condensa sulla batteria e cola nel piatto di raccolta.

La quantità d'acqua estratta per ora dipende da:
```
Acqua estratta = Portata_aria × (ω_entrata − ω_uscita)
```
dove ω è l'umidità specifica in g/kg.

### 3.2 Il Punto di Apparato (ADP — Apparatus Dew Point)

L'**ADP** è la temperatura teorica a cui l'aria uscirebbe completamente satura dalla batteria se il contatto fosse perfetto. L'aria reale esce su una retta tra le condizioni d'ingresso e l'ADP.

- **Contact factor** (1 - bypass factor): quanto l'aria si avvicina all'ADP
- Obiettivo: massimizzare il contact factor = avvicinare l'uscita all'ADP

### 3.3 Effetto della Velocità della Ventola

| Velocità | Portata aria | Tempo contatto batteria | Umidità rimossa per kg | Totale rimosso |
|---|---|---|---|---|
| Alta | Alta | Breve | Bassa | Medio-bassa |
| Media | Media | Medio | Media | Media |
| **Bassa** | Bassa | **Lungo** | **Alta** | **Massima** |

A bassa velocità il bypass factor è minimo: l'aria satura il contatto con la batteria.

### 3.4 Differenza con Deumidificatori Commerciali

| Aspetto | Deumidificatore commerciale | Fancoil |
|---|---|---|
| Autonomia | Ciclo chiuso autonomo | Dipende da gruppo refrigeratore esterno |
| Effetto termico | Riscalda leggermente (+1–3°C) | Raffredda significativamente |
| SHR | > 1 (aggiunge calore sensibile) | < 1 (rimuove calore sensibile e latente) |
| Scopo | Deumidificazione come funzione primaria | Raffreddamento + deumidificazione collaterale |
| Controllo UR | Igrometro integrato con set-point | Nessun controllo diretto dell'umidità |
| Sbrinamento | Ciclo automatico integrato | Non sempre presente |
| Efficienza deumidifica | Alta (ottimizzata) | Media (compromesso) |

---

## 4. Impostazioni Ottimali Fancoil

### 4.1 Configurazione di Base per Massima Deumidificazione

| Switch/Parametro | Impostazione | Motivazione |
|---|---|---|
| Valvola liquido (switch 1) | **Aperta** | Necessario per il raffreddamento |
| Temperatura liquido | **7°C** | Massima forza motrice per condensazione |
| Velocità ventola | **Bassa** | Massimo tempo di contatto aria-batteria |

> ⚠️ **Rischio ghiaccio**: con 7°C di liquido e ventola al minimo, la superficie della batteria può scendere sotto 0°C e ghiacciare. Il ghiaccio funge da isolante termico e riduce la deumidificazione. Usare la strategia dinamica descritta nella sezione 5.

### 4.2 Accortezze Fisiche che Aumentano l'Efficienza

- **Pulizia della batteria**: sporco e biofilm possono dimezzare il coefficiente di scambio termico. Pulire periodicamente.
- **Orientamento del flusso**: verificare che i deflettori indirizzino il flusso ortogonalmente alla batteria
- **Sigillare le infiltrazioni**: ogni fuga d'aria esterna umida ricarica immediatamente l'umidità estratta
- **Raccolta condensa**: verificare che il piatto si svuoti. Un piatto pieno riduce il gradiente di pressione parziale del vapore
- **Orario di utilizzo**: avviare la deumidificazione intensa nelle ore più fresche (notte/mattina) quando il punto di rugiada esterno è più basso

---

## 5. Strategia Dinamica di Controllo

### 5.1 Il Problema delle Impostazioni Statiche

La strategia statica (7°C + ventola bassa sempre) genera un conflitto:

```
Bassa velocità → massima deumidificazione → rischio ghiaccio
Ghiaccio → isola la batteria → deumidificazione crolla → situazione peggiore
```

La strategia dinamica rompe questo conflitto.

### 5.2 Ciclo di Deumidificazione Ottimale

```
CICLO OTTIMALE (~ 20 minuti)
──────────────────────────────────────────────────────────────
│  FASE A (15 min)         │  FASE B (5 min)                 │
│  Liquido: 7°C            │  Liquido: 7°C                   │
│  Ventola: BASSA          │  Ventola: ALTA                  │
│                           │                                  │
│  → Massima condensazione  │  → Sbrinamento preventivo       │
│                           │  → Rimozione film acqua batteria│
│                           │  → Rimescolamento aria locale   │
──────────────────────────────────────────────────────────────
```

La **Fase B** ad alta velocità:
1. Scioglie eventuale ghiaccio prima che si consolidi
2. Rimuove lo strato d'acqua dalla superficie (resistenza termica)
3. Movimenta l'aria del locale, portando aria più umida verso la batteria
4. Consente alla batteria di recuperare temperatura

### 5.3 Modulazione della Temperatura del Liquido

| Strategia | Vantaggio | Svantaggio |
|---|---|---|
| Fisso a 7°C | Massima forza motrice | Rischio ghiaccio a bassa velocità |
| Alzare a 10–11°C | Nessun ghiaccio | Meno condensazione per kg d'aria |
| **Ciclo 7°C → 10°C** | Ottimizza e sbrina termicamente | Richiede controllo attivo |

**Raccomandazione pratica**: con switch discreti, tenere **7°C fisso** e modulare solo la ventola. Alzare la temperatura del liquido solo se si forma ghiaccio persistente.

### 5.4 Termostato di Minima (Protezione Overcooling)

Il fancoil raffredda sempre mentre deumidifica. Rischio reale specialmente in primavera/autunno.

```
SE T_indoor < T_minima_comfort (21°C)
   → PAUSA fancoil (chiudi valvola acqua)
   → Mantieni ventola bassa per circolazione aria
   → Riprendi quando T_indoor > T_ripresa (22°C)
```

---

## 6. Sensori: Posizionamento e Utilizzo

### 6.1 Sensori Necessari

| Posizione | Tipo | Parametri | Utilizzo |
|---|---|---|---|
| Ambiente interno | T + UR (es. SHT31, BME280) | T_int, RH_int | Comfort, controllo fancoil |
| Esterno (o loggia) | T + UR | T_ext, RH_ext | Decisione apertura finestre |
| A valle batteria (5–10 cm) | T + UR | T_out, RH_out | Ottimizzazione fancoil |
| Superficie batteria (opzionale) | Termistore/termocoppia | T_superficie | Rilevazione ghiaccio diretta |

> Costo stimato componenti: **< 20€** per ESP32 + 2× SHT31 + termistore

### 6.2 Calcoli con i Sensori

**Umidità specifica** (g di vapore per kg di aria secca):
```
ω = 0.622 × [P_sat(T) × RH] / [101325 − P_sat(T) × RH]
```

**Punto di rugiada** (approssimazione di Magnus, errore < 1°C):
```
T_dew ≈ T − (100 − RH) / 5
```

**Potenza di deumidificazione effettiva**:
```
Acqua estratta = Portata_aria × (ω_int − ω_out_batteria)
```

### 6.3 Interpretazione delle Misure a Valle della Batteria

| T_out | RH_out | Interpretazione | Azione |
|---|---|---|---|
| < 3°C | qualsiasi | Superficie batteria sotto 0°C | ⚠️ Sbrinamento immediato: ventola ALTA |
| 3–7°C | > 90% | Zona ottimale, vicino all'ADP | ✅ Mantieni |
| 3–7°C | < 80% | Basso contatto aria-batteria | Riduci velocità ventola |
| > 8°C | qualsiasi | Batteria troppo calda | Abbassa temperatura liquido |

### 6.4 Algoritmo di Controllo con Sensori (ogni 2–3 minuti)

```
OGNI 2-3 MINUTI:
├── Misura T_out, RH_out dalla sonda a valle batteria
│
├── SE T_out < 3°C
│     → GHIACCIO IMMINENTE: ventola su ALTA per 5 min → torna BASSA
│
├── SE RH_out < 85% E T_out > 5°C
│     → BASSO CONTATTO: riduci velocità ventola di un livello
│
├── SE RH_out > 95% E T_out > 8°C
│     → BATTERIA TROPPO CALDA: abbassa T liquido
│
└── ALTRIMENTI: mantieni impostazione attuale
```

---

## 7. Gestione Finestre e Porte

### 7.1 L'Errore Comune: Usare l'UR per Decidere

> ⚠️ **L'umidità relativa esterna NON dice se conviene aprire la finestra.**

Una giornata con 80% UR a 16°C ha **molta meno** acqua nell'aria di una con 55% UR a 28°C.

### 7.2 La Variabile Corretta: Umidità Assoluta (o Punto di Rugiada)

La sola grandezza rilevante è l'**umidità specifica ω** (g/kg) o equivalentemente il **punto di rugiada T_dew**.

```
Δω = ω_indoor − ω_outdoor

Δω > 0  →  aria esterna PIÙ SECCA  →  aprire aiuta
Δω < 0  →  aria esterna PIÙ UMIDA  →  finestra CHIUSA obbligatorio
Δω ≈ 0  →  indifferente sull'umidità
```

### 7.3 Esempi Pratici (Brescia, valori tipici)

| Scenario | Esterno | Interno | Δω (g/kg) | Decisione |
|---|---|---|---|---|
| Mattina primaverile | 14°C, 65% UR → ω ≈ 6.4 | 22°C, 68% UR → ω ≈ 11.2 | **+4.8** | ✅ Apri |
| Pomeriggio estivo caldo | 32°C, 60% UR → ω ≈ 18.0 | 26°C, 65% UR → ω ≈ 13.7 | **−4.3** | ❌ Chiudi |
| Sera estiva (caso controintuitivo) | 24°C, 75% UR → ω ≈ 14.2 | 26°C, 60% UR → ω ≈ 12.6 | **−1.6** | ❌ Chiudi |
| Notte autunnale | 16°C, 80% UR → ω ≈ 9.1 | 21°C, 72% UR → ω ≈ 11.1 | **+2.0** | ✅ Apri |

> Il caso "sera estiva" è il più controintuitivo: 75% UR fuori sembra umido, ma l'aria è più secca di quella interna al 60%. Chi chiude per istinto sbaglia.

### 7.4 Matrice Decisionale Finestra (Umidità + Temperatura)

```
                    ω_est < ω_int              ω_est > ω_int
                  (esterno più secco)        (esterno più umido)
                ┌────────────────────────┬────────────────────────┐
T_est > T_int   │  ✅ APRI               │  ❌ CHIUDI             │
(est. più caldo)│  Deumidifichi gratis   │  Porta umidità E calore│
                │  e mantieni T.         │  doppio danno          │
                │  Fancoil in pausa      │                        │
                ├────────────────────────┼────────────────────────┤
T_est < T_int   │  ✅ APRI (parziale)    │  ❌ CHIUDI             │
(est. più freddo│  Deumidifichi ma       │  Fancoil a piena       │
 dell'interno)  │  raffreddi: monitora   │  potenza con cicli     │
                │  T_indoor              │  sbrinamento           │
                └────────────────────────┴────────────────────────┘
```

**Quadrante ideale** (in alto a sinistra): aria esterna più secca e più calda. In primavera/autunno capita frequentemente nel pomeriggio.

### 7.5 Risparmio Energetico dalla Ventilazione Naturale

Ogni ora in cui la finestra aperta sostituisce il fancoil vale circa **200–400 Wh** di energia non consumata dal gruppo refrigeratore, con deumidificazione identica o superiore (nessun bypass, nessun raffreddamento indesiderato).

---

## 8. Algoritmo Domotico Integrato

### 8.1 Input Necessari

```
SENSORI RICHIESTI:
  ├── T_int, RH_int      → sonda ambiente interno
  ├── T_ext, RH_ext      → sonda esterna (o loggia)
  ├── T_out_batt         → sonda a valle batteria fancoil
  └── T_sup_batt         → termistore su superficie batteria (opzionale)

ATTUATORI:
  ├── Switch_1           → valvola liquido refrigerante
  ├── Switch_ventola     → velocità ventola (Bassa / Media / Alta)
  ├── T_liquido          → set-point temperatura liquido (min 7°C)
  └── Notifica_finestra  → alert su display/app per apertura/chiusura finestra
```

### 8.2 Algoritmo Principale (eseguito ogni 5 minuti)

```python
# ============================================================
# STEP 1: CALCOLA GRANDEZZE DERIVATE
# ============================================================
omega_int  = calcola_umidita_specifica(T_int, RH_int)
omega_ext  = calcola_umidita_specifica(T_ext, RH_ext)
delta_omega = omega_int - omega_ext
T_dew_int  = T_int - (100 - RH_int) / 5   # punto di rugiada interno
stagione   = determina_stagione()           # "estate" / "inverno"

# Set-point per stagione
T_target   = 25 if stagione == "estate" else 21
T_minima   = 23 if stagione == "estate" else 19
UR_target  = 52   # centro zona ideale
UR_max     = 65   # soglia intervento deumidificazione
UR_min     = 38   # soglia stop deumidificazione

# ============================================================
# STEP 2: PROTEZIONI ASSOLUTE (priorità massima)
# ============================================================
if T_int < 16:
    # Troppo freddo: ferma tutto
    valvola_chiudi()
    ventola_off()
    notifica("⚠️ Temperatura critica, sistema fermo")
    STOP

if T_sup_batt < 0:
    # Ghiaccio sulla batteria
    ventola_alta()
    notifica("❄️ Sbrinamento batteria in corso")
    attendi(5_minuti)
    # riprendi il ciclo

# ============================================================
# STEP 3: SUGGERIMENTO FINESTRA (isteresi ±1.5 g/kg)
# ============================================================
if delta_omega > 1.5 and T_int > T_minima:
    notifica("✅ Apri finestra: aria esterna più secca di " 
             + str(round(delta_omega,1)) + " g/kg")
    valvola_chiudi()   # finestra sostituisce il fancoil
    STOP

if delta_omega < 0.5:
    notifica("❌ Tieni finestra chiusa: aria esterna più umida")

# ============================================================
# STEP 4: CONTROLLO TEMPERATURA (priorità alta)
# ============================================================
if T_int < T_minima:
    # Overcooling: pausa fancoil
    valvola_chiudi()
    ventola_bassa()    # solo circolazione
    STOP

# ============================================================
# STEP 5: CONTROLLO DEUMIDIFICAZIONE
# ============================================================
if RH_int > UR_max:
    # Deumidificazione attiva
    valvola_apri()
    T_liquido_set(7)   # massima potenza
    # Ciclo dinamico (gestito dal loop sub-ciclo ogni 20 min)
    avvia_ciclo_deumidificazione()

elif RH_int < UR_min:
    # Umidità troppo bassa: ferma deumidificazione
    valvola_chiudi()
    notifica("💧 UR bassa (" + str(RH_int) + "%), valutare umidificazione")

else:
    # Zona di comfort: mantenimento
    if T_int > T_target:
        valvola_apri()
        ventola_bassa()
    else:
        valvola_chiudi()
        ventola_bassa()   # solo circolazione

# ============================================================
# SUB-CICLO DEUMIDIFICAZIONE (ogni 20 minuti)
# ============================================================
# FASE A (15 min): T_liquido 7°C, ventola BASSA
# FASE B (5 min):  T_liquido 7°C, ventola ALTA (sbrinamento)
# poi ripeti
```

### 8.3 Funzione Calcolo Umidità Specifica

```python
import math

def calcola_umidita_specifica(T, RH):
    """
    T: temperatura in °C
    RH: umidità relativa in % (0-100)
    Ritorna: ω in g/kg di aria secca
    """
    # Pressione di vapore saturo (formula di Magnus)
    P_sat = 610.78 * math.exp(17.27 * T / (T + 237.3))  # Pa
    P_vapore = (RH / 100) * P_sat
    P_atm = 101325  # Pa
    omega = 622 * P_vapore / (P_atm - P_vapore)  # g/kg
    return omega

def calcola_punto_rugiada(T, RH):
    """Approssimazione Magnus, errore < 1°C"""
    return T - (100 - RH) / 5
```

### 8.4 Logica di Allerta e Notifiche

| Condizione | Allerta | Azione automatica |
|---|---|---|
| UR > 65% | 🟡 Deumidificazione attiva | Avvia fancoil ciclo deumidifica |
| UR > 75% | 🔴 Rischio muffa | Deumidificazione massima + notifica urgente |
| UR < 35% | 🟡 Aria troppo secca | Ferma deumidificazione |
| T_int < 19°C | 🔴 Overcooling | Ferma valvola, solo ventilazione |
| T_sup_batt < 0°C | 🔴 Ghiaccio batteria | Ventola alta 5 min immediati |
| Delta T int-est > 7°C | 🟡 Shock termico | Alza set-point +2°C |
| Δω > 1.5 g/kg | 🟢 Finestra conveniente | Notifica apertura finestra |

---

## 9. Tabelle di Riferimento Rapido

### 9.1 Valori Target per Stagione

| Parametro | Primavera | Estate | Autunno | Inverno |
|---|---|---|---|---|
| T diurna | 21–23°C | 24–26°C | 20–22°C | 20–21°C |
| T notturna | 18–19°C | 22–23°C | 18–19°C | 17–18°C |
| UR target | 45–55% | 50–55% | 45–55% | 40–50% |
| Punto rugiada | 9–11°C | 12–14°C | 9–11°C | 7–10°C |

### 9.2 Impostazioni Fancoil per Modalità

| Modalità | Valvola | T liquido | Ventola | Quando usare |
|---|---|---|---|---|
| **Deumidifica max** | Aperta | 7°C | Bassa (ciclica) | UR > 65%, T_int OK |
| **Raffredda + deumidifica** | Aperta | 7–9°C | Media | T_int > 26°C, estate |
| **Solo circolazione** | Chiusa | — | Bassa | T_int OK, UR OK |
| **Overcooling protection** | Chiusa | — | Bassa | T_int < T_minima |
| **Sbrinamento** | Aperta | 7°C | Alta (5 min) | T_sup < 3°C |

### 9.3 Guida Rapida Finestre

| Situazione | Δ Punto di rugiada | Azione |
|---|---|---|
| TD_int >> TD_ext (> 3°C) | Interno molto più umido | ✅ Apri finestra |
| TD_int > TD_ext (1–3°C) | Interno leggermente più umido | ✅ Apri se T_int OK |
| TD_int ≈ TD_ext (±1°C) | Simile | Indifferente |
| TD_int < TD_ext | Esterno più umido | ❌ Tieni chiusa |

---

## Note Implementative

### Hardware consigliato (entry level)
- **Microcontrollore**: ESP32 (WiFi integrato, > 10 GPIO)
- **Sensori T+UR**: SHT31 (precisione ±0.2°C, ±2% UR) — 1 interno, 1 esterno, 1 a valle batteria
- **Sensore superficie batteria**: NTC 10kΩ incollato sulle alette
- **Attuatori switch**: relè 5V per i 4 switch esistenti del fancoil
- **Interfaccia**: Home Assistant / ESPHome per logica e dashboard

### Priorità di implementazione suggerita
1. Sonda interna T+UR → termostato di minima + allarme UR
2. Sonda esterna T+UR → suggerimento finestre
3. Ciclo dinamico ventola (timer 15+5 min) → +20–30% efficienza deumidificazione
4. Sonda a valle batteria → ottimizzazione fine e rilevazione ghiaccio
5. Termistore superficie batteria → protezione ghiaccio diretta

---

## 10. Gestione degli Scenari Specifici

### 10.1 Picchi di Umidità Interni

Alcune attività generano picchi rapidi di umidità che richiedono una risposta diversa dalla deumidificazione lenta.

| Evento | Produzione vapore stimata | Durata | Strategia |
|---|---|---|---|
| Doccia (box chiuso) | 200–400 g | 10–15 min | Ventilazione bagno + finestra se Δω > 0 |
| Doccia (porta aperta) | 400–700 g diffusi | 20–30 min | Attivazione immediata fancoil |
| Cottura pasta/lesso | 300–600 g | 20–40 min | Cappa aspirante + finestra cucina |
| Cottura al forno | 100–200 g | 30–60 min | Cappa + monitoraggio UR |
| 2 persone presenti | ~100 g/h cadauno | Continuo | Incluso nel set-point base |
| Piante in numero elevato | 50–200 g/h | Continuo | Considerare nel bilancio umidità |
| Bucato steso in casa | 1.5–3 kg totali | 4–8 h | Deumidificazione attiva, finestra se possibile |

#### Strategia per picco rapido (es. dopo doccia)

```
RILEVATO: UR_int sale > 3% in meno di 10 minuti

→ Priorità 1: ventilazione localizzata (aspiratore bagno)
→ Priorità 2: SE Δω > 0 → apri finestra camera adiacente
→ Priorità 3: SE Δω < 0 → attiva fancoil a ventola MEDIA
              (non bassa: il picco è rapido, serve portata)
→ Torna a logica standard quando UR < UR_target + 5%
```

### 10.2 Appartamento Vuoto vs Occupato

Il comportamento ottimale cambia significativamente in base all'occupazione.

**Modalità Assenza** (nessuno in casa per > 2 ore):

| Parametro | Limite minimo | Limite massimo | Logica |
|---|---|---|---|
| Temperatura estate | 28°C | — | Risparmio energetico |
| Temperatura inverno | — | 16°C | Anticongelamento |
| Umidità relativa | 40% | 70% | Solo protezione struttura |

```
MODALITÀ ASSENZA:
  → Fancoil attivo SOLO se UR > 70% (protezione muffe)
  → Set-point T allargato (risparmio energetico)
  → Finestre: logica Δω normale (automatizzabile con attuatori)
  → 30 min prima del rientro: pre-condizionamento a valori comfort
```

**Modalità Notte** (ore 23:00–07:00):

```
MODALITÀ NOTTE:
  → T_target = 18–19°C (sonno ottimale)
  → UR_target = 50–55% (mucose protette, sonno profondo)
  → Ventola MINIMA o OFF (rumore)
  → Valvola aperta solo se UR > 65%
  → NO notifiche finestra (non si alzano di notte)
```

### 10.3 Giorni Critici: Alta Umidità Persistente

Tipici in Pianura Padana: nebbia estesa, pioggia prolungata, umidità esterna > 85% per > 24 ore.

```
SCENARIO: T_ext = 18°C, RH_ext = 90%, ω_ext = 11.7 g/kg
          T_int = 22°C, RH_int = 75%, ω_int = 13.1 g/kg

→ Δω = +1.4 g/kg: finestra marginalmente utile ma:
  - T_ext < T_int → raffredda l'appartamento (problema in inverno)
  - Il guadagno di deumidificazione è piccolo
  - DECISIONE: fancoil attivo, finestre chiuse
  
STRATEGIA GIORNATA UMIDA:
  1. Fancoil in ciclo continuo (15+5 min) tutto il giorno
  2. UR_max abbassata a 60% (margine extra contro muffa)
  3. Attenzione speciale agli angoli freddi (ispezione visiva)
  4. Circolazione d'aria interna con ventola anche a fancoil spento
```

### 10.4 Ondate di Calore Estive

Quando T_ext > 35°C per più giorni consecutivi:

```
PROBLEMA: Delta T necessario per comfort (24°C int vs 37°C est)
          è > 13°C → shock termico all'uscita

STRATEGIA:
  → Alzare progressivamente T_target a 26–27°C
  → Aumentare UR_target a 55% (si percepisce più fresco con
    aria leggermente più umida ma non calore umido)
  → Pre-raffrescamento notturno (quando T_ext scende a 25–28°C)
  → Oscurare finestre esposte a sud/ovest (riduce carico termico
    radiante del 30–40%, alleggerisce il fancoil)
  → Ventilazione notturna massiva SE T_ext < T_int E Δω > 0
```

---

## 11. Calendario Stagionale — Pianura Padana

### 11.1 Strategia Mensile

#### Gennaio – Febbraio
- **Problema dominante**: aria secca per riscaldamento (UR interna crolla a 25–35%)
- **Fancoil**: in modalità riscaldamento (se previsto), deumidificazione non necessaria
- **Finestre**: aprire brevemente (10–15 min) nelle ore centrali per ricambio d'aria
- **Attenzione**: UR < 30% → valutare umidificatore autonomo
- **Set-point**: T = 20–21°C, UR target = 45–50%

#### Marzo – Aprile
- **Problema dominante**: escursioni termiche ampie, umidità variabile
- **Fancoil**: deumidificazione intermittente, soprattutto di sera
- **Finestre**: opportunità frequenti di ventilazione naturale (mattina fresca e secca)
- **Momento ideale**: mattine con T_ext 12–16°C e UR < 65% → apri tutto
- **Set-point**: T = 21–22°C, UR target = 50%

#### Maggio – Giugno
- **Problema dominante**: umidità in rapido aumento, caldo che inizia
- **Fancoil**: deumidificazione attiva pomeriggio/sera, ciclo dinamico
- **Finestre**: attenzione al pomeriggio (T e ω esterne salgono)
- **Regola pratica**: finestre aperte 06:00–09:00, chiuse 10:00–20:00, rivalutare sera
- **Set-point**: T = 23–24°C, UR target = 52%

#### Luglio – Agosto
- **Problema dominante**: caldo e umidità elevati, notti tropicali
- **Fancoil**: attivo gran parte del giorno, ciclo deumidifica + raffredda
- **Finestre**: quasi sempre chiuse di giorno; aperte solo se T_ext < 24°C e Δω > 1
- **Notte**: SE T_ext scende sotto 24°C e Δω > 0 → finestre aperte, fancoil spento
- **Set-point**: T = 25–26°C, UR target = 52–55%

#### Settembre – Ottobre
- **Problema dominante**: umidità ancora elevata, temperature più miti
- **Fancoil**: deumidificazione attiva, rischio overcooling in aumento
- **Finestre**: opportunità crescenti, soprattutto pomeriggio soleggiato
- **Attenzione**: settembre nebbia mattutina → ω_ext alta la mattina, scende nel pomeriggio
- **Set-point**: T = 22–23°C, UR target = 50%

#### Novembre – Dicembre
- **Problema dominante**: ritorno a aria secca per riscaldamento
- **Fancoil**: deumidificazione non necessaria (UR interna già bassa)
- **Finestre**: ricambio d'aria breve nelle ore centrali
- **Attenzione**: muffe negli angoli freddi (pareti nord e ponti termici)
- **Set-point**: T = 20–21°C, UR target = 45–50%

### 11.2 Ore del Giorno Ottimali per Ventilazione Naturale

In Pianura Padana, il profilo tipico di umidità esterna segue questo schema:

```
ω_ext (g/kg)
  18 │                        ████
  16 │                     ███    ███
  14 │                  ███          ██
  12 │     ████      ███               ██
  10 │  ███    ██████                    ████
   8 │██
     └─────────────────────────────────────── ora
       0    4    8   10   12   14   18   22   24

     ↑ notte umida    ↑ min mattina   ↑ max pomeriggio
     
FINESTRA IDEALE: 07:00–10:00 (ω in discesa, T ancora fresca)
SECONDA FINESTRA: 20:00–22:00 (ω cala dopo tramonto)
EVITARE: 12:00–17:00 luglio/agosto (ω e T massime)
```

---

## 12. Implementazione Home Assistant / ESPHome

### 12.1 Configurazione ESPHome (sensori + relè)

```yaml
# esphome/fancoil_controller.yaml
esphome:
  name: fancoil_controller
  platform: ESP32
  board: esp32dev

wifi:
  ssid: !secret wifi_ssid
  password: !secret wifi_password

api:
  encryption:
    key: !secret api_key

ota:
  password: !secret ota_password

# ── SENSORI ────────────────────────────────────────────
i2c:
  sda: GPIO21
  scl: GPIO22

sensor:
  # Sensore interno
  - platform: sht3xd
    address: 0x44
    temperature:
      name: "Temperatura Interna"
      id: t_int
    humidity:
      name: "Umidità Relativa Interna"
      id: rh_int
    update_interval: 60s

  # Sensore a valle batteria
  - platform: sht3xd
    address: 0x45
    temperature:
      name: "Temperatura Valle Batteria"
      id: t_batt_out
    humidity:
      name: "UR Valle Batteria"
      id: rh_batt_out
    update_interval: 30s

  # Termistore NTC superficie batteria
  - platform: ntc
    sensor: resistance_sensor
    calibration:
      b_constant: 3950
      reference_temperature: 25°C
      reference_resistance: 10kΩ
    name: "Temperatura Superficie Batteria"
    id: t_sup_batt

  - platform: resistance
    id: resistance_sensor
    sensor: ntc_source
    configuration: DOWNSTREAM
    resistor: 10kΩ

  - platform: adc
    id: ntc_source
    pin: GPIO34
    attenuation: 11db

  # Umidità specifica calcolata (interna)
  - platform: template
    name: "Umidità Specifica Interna (g/kg)"
    id: omega_int
    unit_of_measurement: "g/kg"
    lambda: |-
      float T = id(t_int).state;
      float RH = id(rh_int).state / 100.0;
      float psat = 610.78 * exp(17.27 * T / (T + 237.3));
      float pvap = RH * psat;
      return 622.0 * pvap / (101325.0 - pvap);
    update_interval: 60s

  # Punto di rugiada interno
  - platform: template
    name: "Punto di Rugiada Interno (°C)"
    id: t_dew_int
    unit_of_measurement: "°C"
    lambda: |-
      return id(t_int).state - (100.0 - id(rh_int).state) / 5.0;
    update_interval: 60s

# ── RELÈ FANCOIL ───────────────────────────────────────
switch:
  - platform: gpio
    name: "Fancoil - Valvola Acqua"
    id: sw_valvola
    pin: GPIO25
    restore_mode: RESTORE_DEFAULT_OFF

  - platform: gpio
    name: "Fancoil - Ventola Bassa"
    id: sw_vent_bassa
    pin: GPIO26
    restore_mode: RESTORE_DEFAULT_OFF

  - platform: gpio
    name: "Fancoil - Ventola Media"
    id: sw_vent_media
    pin: GPIO27
    restore_mode: RESTORE_DEFAULT_OFF

  - platform: gpio
    name: "Fancoil - Ventola Alta"
    id: sw_vent_alta
    pin: GPIO14
    restore_mode: RESTORE_DEFAULT_OFF

# ── STATO SISTEMA ──────────────────────────────────────
text_sensor:
  - platform: template
    name: "Modalità Sistema"
    id: modalita_sistema
    update_interval: 60s

binary_sensor:
  - platform: template
    name: "Allarme Ghiaccio Batteria"
    lambda: |-
      return id(t_sup_batt).state < 1.0;
```

### 12.2 Automazioni Home Assistant

```yaml
# configuration.yaml — automazioni fancoil

automation:
  # ── PROTEZIONE GHIACCIO (priorità assoluta) ──────────
  - alias: "Fancoil - Sbrinamento emergenza"
    trigger:
      - platform: numeric_state
        entity_id: sensor.temperatura_superficie_batteria
        below: 1.5
    action:
      - service: switch.turn_on
        entity_id: switch.fancoil_ventola_alta
      - service: switch.turn_off
        entity_id:
          - switch.fancoil_ventola_bassa
          - switch.fancoil_ventola_media
      - delay: "00:05:00"
      - service: switch.turn_off
        entity_id: switch.fancoil_ventola_alta
      - service: switch.turn_on
        entity_id: switch.fancoil_ventola_bassa

  # ── CICLO DEUMIDIFICAZIONE (15 min bassa + 5 alta) ───
  - alias: "Fancoil - Fase A (ventola bassa)"
    trigger:
      - platform: time_pattern
        minutes: "/20"   # ogni 20 minuti a :00
    condition:
      - condition: state
        entity_id: switch.fancoil_valvola_acqua
        state: "on"
    action:
      - service: switch.turn_on
        entity_id: switch.fancoil_ventola_bassa
      - service: switch.turn_off
        entity_id:
          - switch.fancoil_ventola_media
          - switch.fancoil_ventola_alta

  - alias: "Fancoil - Fase B (sbrinamento preventivo)"
    trigger:
      - platform: time_pattern
        minutes: "/20"
        seconds: "900"   # 15 minuti dopo l'inizio
    condition:
      - condition: state
        entity_id: switch.fancoil_valvola_acqua
        state: "on"
    action:
      - service: switch.turn_on
        entity_id: switch.fancoil_ventola_alta
      - service: switch.turn_off
        entity_id:
          - switch.fancoil_ventola_bassa
          - switch.fancoil_ventola_media

  # ── DEUMIDIFICAZIONE ATTIVA (UR > 65%) ────────────────
  - alias: "Fancoil - Avvia deumidificazione"
    trigger:
      - platform: numeric_state
        entity_id: sensor.umidita_relativa_interna
        above: 65
        for: "00:05:00"
    condition:
      - condition: numeric_state
        entity_id: sensor.temperatura_interna
        above: 21
    action:
      - service: switch.turn_on
        entity_id: switch.fancoil_valvola_acqua
      - service: notify.mobile_app
        data:
          message: "💧 Deumidificazione attiva — UR {{ states('sensor.umidita_relativa_interna') }}%"

  # ── STOP DEUMIDIFICAZIONE (UR < 50%) ─────────────────
  - alias: "Fancoil - Ferma deumidificazione"
    trigger:
      - platform: numeric_state
        entity_id: sensor.umidita_relativa_interna
        below: 50
        for: "00:10:00"
    action:
      - service: switch.turn_off
        entity_id: switch.fancoil_valvola_acqua

  # ── OVERCOOLING (T < 21°C) ────────────────────────────
  - alias: "Fancoil - Protezione overcooling"
    trigger:
      - platform: numeric_state
        entity_id: sensor.temperatura_interna
        below: 21
    action:
      - service: switch.turn_off
        entity_id: switch.fancoil_valvola_acqua
      - service: notify.mobile_app
        data:
          message: "🌡️ Fancoil in pausa — T interna {{ states('sensor.temperatura_interna') }}°C"

  # ── SUGGERIMENTO FINESTRA ─────────────────────────────
  - alias: "Finestra - Suggerisci apertura"
    trigger:
      - platform: numeric_state
        entity_id: sensor.delta_omega   # valore calcolato (vedi template)
        above: 1.5
        for: "00:10:00"
    condition:
      - condition: numeric_state
        entity_id: sensor.temperatura_interna
        above: 21
      - condition: time
        after: "07:00:00"
        before: "23:00:00"
    action:
      - service: notify.mobile_app
        data:
          message: >
            ✅ Apri la finestra! Aria esterna più secca di
            {{ states('sensor.delta_omega') | round(1) }} g/kg.
            T esterna: {{ states('sensor.temperatura_esterna') }}°C

  - alias: "Finestra - Suggerisci chiusura"
    trigger:
      - platform: numeric_state
        entity_id: sensor.delta_omega
        below: -0.5
        for: "00:05:00"
    condition:
      - condition: time
        after: "07:00:00"
        before: "23:00:00"
    action:
      - service: notify.mobile_app
        data:
          message: >
            ❌ Chiudi la finestra — aria esterna più umida di
            {{ (states('sensor.delta_omega') | float * -1) | round(1) }} g/kg
```

### 12.3 Template Sensori Derivati (configuration.yaml)

```yaml
template:
  - sensor:
    # Delta omega (int - ext)
    - name: "Delta Omega (int-ext)"
      unique_id: delta_omega
      unit_of_measurement: "g/kg"
      state: >
        {% set T_ext = states('sensor.temperatura_esterna') | float %}
        {% set RH_ext = states('sensor.umidita_relativa_esterna') | float / 100 %}
        {% set T_int = states('sensor.temperatura_interna') | float %}
        {% set RH_int = states('sensor.umidita_relativa_interna') | float / 100 %}
        {% set psat_ext = 610.78 * e ** (17.27 * T_ext / (T_ext + 237.3)) %}
        {% set psat_int = 610.78 * e ** (17.27 * T_int / (T_int + 237.3)) %}
        {% set omega_ext = 622 * (RH_ext * psat_ext) / (101325 - RH_ext * psat_ext) %}
        {% set omega_int = 622 * (RH_int * psat_int) / (101325 - RH_int * psat_int) %}
        {{ (omega_int - omega_ext) | round(2) }}

    # Stato comfort complessivo
    - name: "Stato Comfort"
      unique_id: stato_comfort
      state: >
        {% set T = states('sensor.temperatura_interna') | float %}
        {% set RH = states('sensor.umidita_relativa_interna') | float %}
        {% if T >= 23 and T <= 26 and RH >= 45 and RH <= 60 %}
          Ottimale
        {% elif T >= 21 and T <= 27 and RH >= 40 and RH <= 65 %}
          Accettabile
        {% elif RH > 70 %}
          ⚠️ Umidità eccessiva
        {% elif RH < 35 %}
          ⚠️ Aria troppo secca
        {% elif T > 28 %}
          ⚠️ Troppo caldo
        {% elif T < 19 %}
          ⚠️ Troppo freddo
        {% else %}
          Fuori range
        {% endif %}
```

### 12.4 Dashboard Lovelace (esempio card)

```yaml
# Aggiungere alla dashboard Lovelace
type: vertical-stack
cards:
  - type: entities
    title: "🌡️ Comfort Indoor"
    entities:
      - entity: sensor.temperatura_interna
        name: Temperatura
      - entity: sensor.umidita_relativa_interna
        name: Umidità Relativa
      - entity: sensor.punto_di_rugiada_interno
        name: Punto di Rugiada
      - entity: sensor.stato_comfort
        name: Stato Comfort

  - type: entities
    title: "🌬️ Fancoil"
    entities:
      - entity: switch.fancoil_valvola_acqua
        name: Valvola Acqua
      - entity: sensor.temperatura_superficie_batteria
        name: T Superficie Batteria
      - entity: sensor.temperatura_valle_batteria
        name: T Valle Batteria

  - type: entities
    title: "🪟 Finestre"
    entities:
      - entity: sensor.delta_omega
        name: Δω Int-Ext (g/kg)
      - entity: sensor.temperatura_esterna
        name: T Esterna
      - entity: sensor.umidita_relativa_esterna
        name: UR Esterna
```

---

## 13. Manutenzione e Calibrazione

### 13.1 Programma di Manutenzione

| Intervallo | Attività | Motivazione |
|---|---|---|
| **Mensile** | Controllare il piatto di raccolta condensa | Prevenire ristagni e proliferazione batterica |
| **Mensile** | Verificare assenza di ghiaccio residuo sulla batteria | Può indicare problemi con il ciclo di sbrinamento |
| **Stagionale** (inizio estate) | Pulizia filtri fancoil | Filtri sporchi riducono portata d'aria del 30–50% |
| **Stagionale** (inizio estate) | Pulizia alette batteria (soffio aria compressa) | Sporco riduce scambio termico |
| **Annuale** | Controllo tenuta valvola acqua (switch 1) | Perdite riducono la temperatura del liquido |
| **Annuale** | Controllo scarico condensa | Ostruzione causa allagamento piatto |
| **Biennale** | Calibrazione sensori T+UR | Drift tipico SHT31: ±0.5°C, ±3% UR dopo 2 anni |

### 13.2 Calibrazione Sensori

I sensori capacitivi di umidità (SHT31, BME280, DHT22) tendono a derivare nel tempo. Procedura di verifica:

**Metodo sale saturo (calibrazione UR)**

Con sale da cucina (NaCl) saturo in acqua in contenitore chiuso si ottiene UR = 75.3% a 20°C. Confrontare la lettura del sensore dopo 2 ore di stabilizzazione:

```
Offset_UR = 75.3 - lettura_sensore

SE |Offset_UR| < 3%  → sensore OK
SE |Offset_UR| > 5%  → sostituire il sensore
SE 3% < |Offset_UR| < 5% → applicare offset nel firmware
```

**Correzione in ESPHome**:
```yaml
sensor:
  - platform: sht3xd
    humidity:
      name: "Umidità Relativa Interna"
      filters:
        - offset: -2.5   # correzione derivata dalla calibrazione
```

**Calibrazione temperatura**: confrontare con termometro di riferimento a bagno d'acqua a 20°C per 10 minuti. Offset tipico < 0.5°C per SHT31.

### 13.3 Verifica Prestazioni Fancoil

Per verificare che il fancoil stia deumidificando effettivamente, misurare con il solo fancoil acceso (finestre chiuse, nessuna fonte di vapore):

```
TEST PRESTAZIONI:
  1. Registra UR_start e tempo T_start
  2. Avvia fancoil (7°C, ventola bassa)
  3. Dopo 30 minuti: registra UR_end

  ΔUR/h = (UR_start - UR_end) × 2

  Risultato atteso per appartamento 80m², soffitto 2.7m:
    Volume aria = 216 m³
    Densità aria ~ 1.2 kg/m³ → 259 kg aria
    ΔUR atteso: 3–5%/30min in condizioni normali

  SE ΔUR/30min < 1% → sospettare:
    → Filtro otturato
    → Temperatura liquido non a 7°C
    → Perdite d'aria (finestre, porte)
    → Batteria sporca o ghiacciata
```

---

## 12.4 Verifiche di Funzionalità – Schema di Riferimento

### 12.4.1 State Dump Fancoil (cucina)

I log di stato periodici contengono i dati di calibrazione completi:

```
[Cucina] State Dump: Trigger=periodic/time (?->?), Temp=24.8°C, KNX=N/A°C, Hum=57.0% (Var: 8.0), Setpoint=23.5°C (Raw: 23.5), MasterSP=23.5°C, Delta=1.3°C (RawDiff: 1.3), Offset=0.0°C, Target=off, HvacMode=cool, StopCond=False, System=False, PDC_H2O=off, Comm=unavailable, T_Circ=18.0°C, Main=on, Soglie=[S:-0.8, I:-0.6, L:-0.2, M:0.1, H:0.5], SW=[0,0,0,0], Mijia_T=24.7°C, Mijia_RH=61%, Cal_T=24.8°C, Cal_RH=58%, Off_T_24h=0.0°C, Off_RH_24h=5.27%
```

**Indicazioni chiave nel log (cucina)**:
- `Mijia_T`, `Mijia_RH` – misurazioni del sensore di riferimento Xiaomi Mijia
- `Cal_T`, `Cal_RH` – valori corretti del fancoil (temperatura e umidità calibrate)
- `Off_T_24h`, `Off_RH_24h` – offset medi calibrati (24 ore)

**A partire da oggi (2026-08-08) — Le letture della calibrazione sono funzionanti**

**Data e ora di riferimento per i test futuri**: `2026-08-08 22:14:06`

**Come usare i log per i test**:

1. **Verifica integrità dei dati** – Assicurarsi che ogni log contenga:
   - `Mijia_T`, `Mijia_RH` ≠ unavailables
   - `Cal_T`, `Cal_RH` ≠ unknown
   - `Off_T_24h`, `Off_RH_24h` ≠ unknown

2. **Annulla continuità degli offset** – Utilizzare il delta 24 ore in `Off_T_24h` / `Off_RH_24h` per:
   - Calcolare i correttivi applicabili agli istanti del fancoil: `T_corretto = T_raw + Off_T_24h`
   - Mappare i valori della temperatura e umidità calibrate per il tuning manuale

3. **Validazione sensori di calibrazione** – Verificare periodicamente il ciclo di deumidificazione:
   - `sensor.cucina_calibrazione_temp_offset_instantaneo`
   - `sensor.cucina_calibrazione_umidita_offset_instantaneo`
   - `sensor.cucina_temperatura_calibrata` / `sensor.cucina_umidita_calibrata`
   - `sensor.statistiche_cucina_calibrazione_temp_offset_24h`
   - `sensor.statistiche_cucina_calibrazione_umidita_offset_24h`

### 12.4.2 Attivazione sistema di calibrazione

Per avviare un nuovo test di calibrazione:

1. Assicurarsi che il file **`packages/fancoil_cucina_mijia_calibration.yaml`** sia presente in **/config/packages/**
2. Regenerate i files fancoil: `python3 yaml_generator/generate_fancoil_climates.py`
3. Riavviare Home Assistant: `docker restart homeassistant`
4. Verificare la scrittura dei log di stato: `/config/logs/fancoil_events/fancoil_events.log`

**I log mostreranno Mijia_T, Mijia_RH, Cal_T, Cal_RH solo per la cucina**

---

---

## 15. Troubleshooting

### 15.1 Problemi Comuni e Soluzioni

| Sintomo | Causa probabile | Soluzione |
|---|---|---|
| UR non scende nonostante fancoil attivo | Filtro sporco / batteria ghiacciata / perdite aria | Pulire filtro, verificare ghiaccio, sigillare finestre |
| T scende troppo rapidamente | Liquido troppo freddo + ventola troppo alta | Ridurre velocità ventola, attivare termostato di minima |
| Ghiaccio persistente sulla batteria | Ventola troppo lenta o T liquido troppo bassa | Aumentare velocità minima ciclo, alzare T a 9°C |
| Condensa sulle pareti (non sulla batteria) | Ponte termico + UR > 65% | Deumidificazione più aggressiva + ispezione pareti |
| Odore musty dall'apparecchio | Biofilm nel piatto raccolta o batteria | Pulizia con soluzione diluita candeggina, poi risciacquo |
| Sensore UR sempre > 10% rispetto ad altri | Deriva del sensore | Calibrazione con sale saturo, applicare offset |
| Fancoil fa rumore a ventola bassa | Pulsazioni d'aria a bassa portata | Alzare leggermente la velocità minima |
| UR sale rapidamente dopo spegnimento fancoil | Alta permeabilità all'umidità dell'involucro | Verificare guarnizioni finestre, aumentare cicli di deumidificazione |

### 15.2 Diagnosi con i Dati dei Sensori

```
SCENARIO: UR interna rimane alta (> 65%) dopo 2 ore di fancoil attivo

CHECK 1: T_sup_batteria?
  → < 5°C: batteria fredda ✓ (problema altrove)
  → > 10°C: batteria non si raffredda → liquido non arriva o filtro otturato

CHECK 2: T_out_batteria vs T_int?
  → T_out quasi uguale a T_int (< 2°C di differenza): aria bypassa la batteria
    → verificare posizione deflettori
  → T_out molto bassa (< 10°C) con RH_out < 80%: l'aria non porta umidità
    → le infiltrazioni esterne sono la fonte principale

CHECK 3: Δω_int_ext?
  → Δω < 0: l'aria esterna è più umida → cercare infiltrazioni
  → Δω > 3: molta umidità interna → fonte interna (persone, piante, bucato)
```

---

## 16. Riepilogo Decisionale Visivo

### 16.1 Albero delle Decisioni Principale

```
START (ogni 5 min)
│
├─ T_sup_batteria < 0°C? ──YES──► SBRINAMENTO EMERGENZA
│                                  (ventola ALTA 5 min)
│ NO
├─ T_int < 16°C? ──────────YES──► TUTTO SPENTO, notifica
│
│ NO
├─ Calcola Δω = ω_int - ω_ext
│
├─ Δω > 1.5 g/kg E T_ext > 18°C?
│   YES ──► APRI FINESTRA + SPEGNI FANCOIL (ventilazione gratuita)
│   NO  ──► continua
│
├─ T_int > T_minima_stagione?
│   NO  ──► FANCOIL PAUSA (overcooling)
│   YES ──► continua
│
├─ UR_int > 65%?
│   YES ──► FANCOIL DEUMIDIFICAZIONE (ciclo 15+5 min)
│   NO  ──► continua
│
├─ T_int > T_target_stagione?
│   YES ──► FANCOIL RAFFREDDAMENTO (ventola media)
│   NO  ──► SOLO CIRCOLAZIONE (valvola chiusa, ventola bassa)
│
└─ FINE (ripeti tra 5 min)
```

### 16.2 Semaforo di Comfort — Valori Soglia Estate

| Indicatore | 🟢 Ottimale | 🟡 Attenzione | 🔴 Intervenire |
|---|---|---|---|
| Temperatura | 24–26°C | 22–23°C / 27–28°C | < 21°C / > 29°C |
| Umidità relativa | 48–58% | 40–48% / 58–65% | < 38% / > 65% |
| Punto di rugiada | 11–14°C | 9–11°C / 14–16°C | < 7°C / > 17°C |
| T superficie batteria | 2–6°C | 0–2°C / 6–10°C | < 0°C / > 12°C |
| Δω (int-ext) | > 1.5 | 0–1.5 | < 0 (chiudi!) |

### 16.3 Semaforo di Comfort — Valori Soglia Inverno

| Indicatore | 🟢 Ottimale | 🟡 Attenzione | 🔴 Intervenire |
|---|---|---|---|
| Temperatura | 20–22°C | 19–20°C / 22–23°C | < 18°C / > 24°C |
| Umidità relativa | 45–55% | 38–45% / 55–62% | < 30% / > 65% |
| Punto di rugiada | 8–11°C | 6–8°C / 11–13°C | < 4°C / > 15°C |

---

## Appendice — Formule di Riferimento

### A.1 Umidità Specifica ω (g/kg)

```
P_sat(T) = 610.78 × exp(17.27 × T / (T + 237.3))    [Pa]
P_vap    = (RH/100) × P_sat                           [Pa]
ω        = 622 × P_vap / (101325 - P_vap)             [g/kg]
```

### A.2 Punto di Rugiada T_dew (°C)

```
T_dew ≈ T - (100 - RH) / 5      [approssimazione Magnus, errore < 1°C]

Formula più precisa (Magnus completa):
  α = ln(RH/100) + 17.27 × T / (237.3 + T)
  T_dew = 237.3 × α / (17.27 - α)
```

### A.3 Temperatura Operativa T_op (°C)

```
T_op = (T_aria + T_media_radiante_superfici) / 2
```

### A.4 Acqua Estratta dal Fancoil (stima)

```
m_acqua [g/h] = Portata_aria [kg/h] × (ω_in - ω_out) [g/kg]

Portata tipica fancoil residenziale:
  Ventola bassa:  150–250 m³/h → 180–300 kg/h
  Ventola media:  300–450 m³/h → 360–540 kg/h
  Ventola alta:   450–600 m³/h → 540–720 kg/h
```

### A.5 Tempo Stimato per Abbassare l'UR

```
ΔUR_necessaria [%] = UR_attuale - UR_target
Volume_aria [m³] = Superficie [m²] × Altezza [m]
Massa_aria [kg]  = Volume × 1.2

Acqua_da_estrarre [g] = Massa_aria × Δω [g/kg]
Tempo_stimato [min]   = Acqua_da_estrarre / (m_acqua [g/h] / 60)

Esempio: appartamento 80m², h 2.7m, UR 72% → 55%, T 25°C
  Massa_aria = 216 × 1.2 = 259 kg
  ω(72%) = 14.8 g/kg,  ω(55%) = 11.0 g/kg
  Acqua_da_estrarre = 259 × 3.8 = 984 g
  m_acqua fancoil bassa velocità ≈ 200 g/h
  Tempo = 984 / (200/60) ≈ 295 min ≈ 5 ore
  (con ciclo ottimizzato e finestre chiuse)
```

---

*Documento generato da sessione di analisi — Giugno 2026*
*Valori di riferimento: ISO 7730, ASHRAE 55, ASHRAE Handbook of Fundamentals, EN 15251, EPA Indoor Air Quality Guidelines*
*Implementazione: Home Assistant 2024+, ESPHome 2024+*
