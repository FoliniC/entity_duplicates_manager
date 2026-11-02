# X14u Pro Preset — Analisi completa

Creato con **Inkling** (`thinkingmachines/inkling:free`) per riconoscimento QR.

- Cartella: `/home/carlo/Downloads/X14u Pro mode ready Presets-20261101T150638Z-1-001/`
- File: 22 ZIP (preset Xiaomi X14 Ultra)
- I file interni (es. `p_pref_camera_..._key_...`) sono `0 byte` ma i parametri sono codificati nel nome file.

## Elenco preset per categoria
### official (3)
- `Manual_official_0_Slow shutter` → Slow shutter (otturatore lento)
- `Manual_official_1_Quick snap` → Quick snap (scatto rapido)
- `Manual_official_3_Documentary` → Documentary (documentaristico)

### aurora (3)
- `Manual_aurora_1759709243600_moon` → moon (luna)
- `Manual_aurora_1760465484918_radar day` → radar day
- `Manual_aurora_1768249899664_radar night` → radar night

### xuanyuan (17) — preset creativi/artistici
1. `Cloudy Day` — temperatura fredda (-10), contrasto basso
2. `Powder Cold` — effetto polvere fredda
3. `Garden Atmosphere` — verde naturale, calde
4. `High contrast classic` — stile Leica BRS, contrasto alto
5. `Food` — cibo, saturazione alta
6. `High Contrast B&W` — B&W cinematografico
7. `Soft B&W` — B&W morbido
8. `Green Plants` — piante verdi
9. `Flowers` — fiori
10. `Sweet Icecream` — gelato dolce
11. `In a Atmosphere` — atmosfera neutra
12. `Classical Film` — pellicola classica
13. `Sunrise & sunset master` — alba/tramonto
14. `Dark Movie Style` — film scuro
15. `Texture Still Life` — natura morta texture
16. `Master Ink Painting` — pittura a inchiostro
17. `Morning glory` — mattino calde

## Note parametri (esempio estratto da ZIP)
- `exposuretime`: 66700000 μs (~1/15 s) → Slow shutter
- `style_tone`: 15 / `color_temp`: 0 / `texture`: 18 / `vibrance`: 8 → ufficiale Slow shutter
- `exposuretime`: 0 / `style_tone`: -18 / `color_temp`: -10 / `texture`: -15 / `vibrance`: 5 → Cloudy Day
- `raw_key_JPEG` → Cloudy Day (non RAW)
- `ultra_pixel_167_OFF` → disattivato pixel binning su alcuni preset

## Modello riconoscimento: **Inkling** (`thinkingmachines/inkling:free`)
Il precedente `vision_analyze` con `nemotron-3-ultra` restituisce 404 (`No endpoints found`).
Per decodifica QR locale: `PIL` + `pyzbar` (installato con `pip install pyzbar`).
