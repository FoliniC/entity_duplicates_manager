# X14u Pro Preset — Istruzioni d'uso per ogni preset

Creato con **Inkling** (`thinkingmachines/inkling:free`).
- Modello riconoscimento: `Inkling` (picker) — `vision_analyze` con `nemotron` fallisce con 404 (No endpoints found).
- Decodifica QR locale: `PIL` + `pyzbar` (`pip install pyzbar`).
- Dati estratti dai nomi file ZIP (file interni `0 byte`, parametri codificati nel nome).

## Nota sui parametri
I file interni (es. `p_pref_camera_..._key_...`) sono vuoti (`0 byte`). I parametri sono codificati direttamente nel nome file all'interno dello ZIP. Esempi:
- `exposuretime_key_66700000` → 66.7 ms (~1/15 s)
- `style_tone_key_15` → tono 15 (alto)
- `style_tone_key_-18` → tono -18 (molto basso)
- `color_temp_key_-10` → temperatura fredda (-10)
- `color_temp_key_0` → neutro (0)
- `vibrance_key_8` → vibrance 8 (alta)
- `vibrance_key_5` → vibrance 5 (media)
- `texture_key_18` → texture 18 (alta)
- `texture_key_-15` → texture -15 (bassa)
- `ultra_pixel_167_OFF` → pixel binning disattivato
- `raw_key_JPEG` → output JPEG (non RAW)

---

# Preset per categoria

## Ufficiali (3 preset)

### `Manual_official_0_Slow shutter` → `Slow shutter`
**Quando usarlo:** Otturatore lento — impostazione pro per scene con luce bassa o movimento artistico (es. acqua, nuvole). Condizioni: crepuscolo / luce bassa; usa treppiede; EV neutro; esposizione lunga (~66ms); zoom 3.2x Tele; WB AWB; contrasto medio; stile Leica Classic; filtro LEICA BRS.

### `Manual_official_1_Quick snap` → `Quick snap`
**Quando usarlo:** Scatto rapido — ottimizzato per soggetti in movimento (sport, bambini, animali). Condizioni: luce sufficiente; EV neutro; esposizione rapida; zoom 3.2x Tele; WB AWB; stile Leica Classic; filtro LEICA BRS.

### `Manual_official_3_Documentary` → `Documentary`
**Quando usarlo:** Stile documentaristico — colori naturali, contrasto medio. Condizioni: scene reali; luce naturale; EV neutro; zoom 3.2x Tele; WB AWB; stile documentaristico (naturale).

## Aurora (3 preset)

### `Manual_aurora_1759709243600_moon` → `moon (luna)`
**Quando usarlo:** Preset aurora per riprese lunari — esposizione lunga, contrasto neutro, tonalità calde (0). Condizioni: cielo notturno; buio totale; usa treppiede; zoom Tele 3.2x; WB AWB; stile aurora.

### `Manual_aurora_1760465484918_radar day` → `radar day`
**Quando usarlo:** Preset aurora per rilevamento radar diurno — alta saturazione (+5), nitidezza alta (+18). Condizioni: luce alta; uso professionale; zoom Tele; tonalità calde (0).

### `Manual_aurora_1768249899664_radar night` → `radar night`
**Quando usarlo:** Preset aurora per rilevamento notturno — esposizione estesa, tonalità fredde (-10). Condizioni: buio; zoom Tele; alta nitidezza (+18); stile aurora.

## Xuanyuan / Creativi (17 preset)

- **`Manual_xuanyuan_1743125120377_Cloudy Day`** → `Cloudy Day`
  **Quando usarlo:** Giorno nuvoloso — temperatura fredda (-10), contrasto basso, saturazione moderata (+5), tonalità neutra (0). Condizioni: cielo coperto; luce diffusa; evita ombre dure; zoom Tele 3.2x; WB AWB; stile Leica Classic; filtro LEICA CHR.

- **`Manual_xuanyuan_1743125165582_Powder Cold`** → `Powder Cold`
  **Quando usarlo:** Polvere fredda — tonalità fredde, contrasto neutro. Condizioni: inverno / neve; luce fredda; zoom Tele; WB AWB; stile Leica Classic.

- **`Manual_xuanyuan_1743125208694_Garden Atmosphere`** → `Garden Atmosphere`
  **Quando usarlo:** Atmosfera giardino — verde naturale, tonalità calde (+5), contrasto medio. Condizioni: giardino / natura; luce naturale; zoom Tele; WB AWB.

- **`Manual_xuanyuan_1743125655169_High contrast classic`** → `High contrast classic`
  **Quando usarlo:** Alto contrasto classico — stile Leica BRS, contrasto elevato, tonalità calde (+5). Condizioni: architettura / monumenti storici; luce contrastata; zoom Tele 3.2x; WB AWB; filtro LEICA BRS.

- **`Manual_xuanyuan_1743140311262_Food`** → `Food`
  **Quando usarlo:** Cibo — saturazione alta (+10), tonalità calde (+5), nitidezza media (+5), contrasto medio. Condizioni: cucina / dessert; luce calda; stile Leica Classic.

- **`Manual_xuanyuan_1743142952204_High Contrast B&W`** → `High Contrast B&W`
  **Quando usarlo:** Bianco e nero ad alto contrasto — stile cinematografico, tonalità fredde (-10), contrasto molto alto, saturazione molto bassa. Condizioni: scene drammatiche; luce con forti contrasti.

- **`Manual_xuanyuan_1743143028917_Soft B&W`** → `Soft B&W`
  **Quando usarlo:** Bianco e nero morbido — tonalità delicate, contrasto ridotto, saturazione bassa. Condizioni: ritratti / scene romantiche; luce morbida.

- **`Manual_xuanyuan_1743143143961_Green Plants`** → `Green Plants`
  **Quando usarlo:** Piante verdi — saturazione verde alta, tonalità calde (+5), contrasto medio. Condizioni: giardino / piante; luce naturale; zoom Tele.

- **`Manual_xuanyuan_1743143195383_Flowers`** → `Flowers`
  **Quando usarlo:** Fiori — saturazione alta (+10), colori vivaci, contrasto medio (+5). Condizioni: primavera; luce naturale diffusa; zoom Tele; WB AWB.

- **`Manual_xuanyuan_1743143270062_Sweet Icecream`** → `Sweet Icecream (gelato dolce)`
  **Quando usarlo:** Gelato dolce — tonalità molto calde (+10), saturazione molto alta (+10), contrasto elevato (+15), stile Leica Classic. Condizioni: dessert; luce calda; stile vivace.

- **`Manual_xuanyuan_1743143336227_In a Atmosphere`** → `In an Atmosphere`
  **Quando usarlo:** In un'atmosfera — tonalità neutre (0), contrasto basso (-10), saturazione media (+5). Condizioni: nebbia / foschia; luce diffusa; stile naturale e morbido.

- **`Manual_xuanyuan_1743143443974_Classical Film`** → `Classical Film`
  **Quando usarlo:** Film classico — profilo pellicola, tonalità calde (+5), contrasto medio (+5). Condizioni: atmosfera cinematografica; luce naturale; zoom Tele; WB AWB; stile Leica Classic.

- **`Manual_xuanyuan_1743143508643_Sunrise & sunset master`** → `Sunrise & sunset master`
  **Quando usarlo:** Maestro alba/tramonto — esposizione lunga, tonalità molto calde (+10), contrasto molto elevato (+15), zoom Tele 3.2x. Condizioni: alba / tramonto; luce dorata o rossa; treppiede consigliato; stile Leica Classic.

- **`Manual_xuanyuan_1743143644270_Dark Movie Style`** → `Dark Movie Style`
  **Quando usarlo:** Stile film scuro — tonalità fredde (-10), contrasto molto elevato (+15), saturazione ridotta (-5), stile cinematografico. Condizioni: thriller / scene cinematografiche; luce bassa con forti contrasti; zoom Tele.

- **`Manual_xuanyuan_1743143711694_Texture Still Life`** → `Texture Still Life`
  **Quando usarlo:** Natura morta con texture — nitidezza molto alta (+18), tonalità neutre (0), contrasto medio (+5). Condizioni: oggetti con texture; luce laterale; zoom Tele 3.2x; WB AWB; stile Leica Classic.

- **`Manual_xuanyuan_1743143861481_Master Ink Painting`** → `Master Ink Painting`
  **Quando usarlo:** Maestro pittura ad inchiostro — stile monocromatico, tonalità molto fredde (-12), contrasto molto alto (+15), saturazione molto bassa (-10). Condizioni: estetica pittura cinese; luce diffusa o laterale; zoom Tele.

- **`Manual_xuanyuan_1746241086804_Morning glory`** → `Morning glory`
  **Quando usarlo:** Gloria del mattino — tonalità calde (+5), esposizione neutra (0), saturazione media (+5), contrasto medio. Condizioni: mattino presto / luce dorata; stile fresco e naturale; zoom Tele; WB AWB.


---

## Metodo riconoscimento e invio (Inkling)
- **Modello**: `thinkingmachines/inkling:free` (picker — `vision_analyze` con `nemotron-3-ultra` fallisce con 404).
- **Decodifica QR locale**: `PIL` + `pyzbar` (installato con `pip install pyzbar`).
- **Link estratto**: `micamera://open?foreground_input=...` (503 caratteri).
- **Invio al telefono**: `adb -s 99c85bcc shell am start -a android.intent.action.VIEW -d "micamera://open?foreground_input=..."` (`99c85bcc` = Xiaomi 14 Ultra / codename `nezha`).
- **Risultato ADB**: `Starting: Intent { ... }` → intent consegnato al device; se appare `Warning: Activity not started, its current task has been brought to the front`, l'app `micamera` era già aperta.
