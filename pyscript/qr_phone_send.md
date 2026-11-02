# Modalità riconoscimento QR + invio al telefono Xiaomi

## Procedura verificata (2026-09-28 → test con dashboard_20261101_095931)

### 1. Ricezione immagine
L'immagine contenente il QR code arriva come: `dashboard_YYYYMMDD_HHMMSS_..._image_...png`

### 2. Scelta modello riconoscimento
**Usare il modello `Inkling` dal picker** (`thinkingmachines/inkling:free` via `openrouter_free`).

Il modello nemotron-3-ultra non supporta endpoint vision (restituisce 404: `No endpoints found that support image input`).

Quindi:
```bash
# Non usare vision_analyze con nemotron → fallisce
# Usare il picker per selezionare Inkling
```

Se vision fallisce ancora (404), passare a decodifica locale con `PIL` + `pyzbar`.

### 3. Decodifica QR (fallback locale)
```python
from PIL import Image
from pyzbar.pyzbar import decode
img = Image.open("/path/to/dashboard_image_*.png")
results = decode(img)
for r in results:
    qr_content = r.data.decode('utf-8')  # es. micamera://open?foreground_input=...
```

### 4. Identificazione device Xiaomi
Controllare dispositivi collegati:
```bash
adb devices
# Es. 99c85bcc  device  → Xiaomi 14 Ultra (codename "nezha")
#     0123456789ABCDEF device → altro
```

Verifica modello se necessario:
```bash
adb -s 99c85bcc shell getprop ro.product.model  # 2512BPNDAG (Xiaomi 14 Ultra)
```

### 5. Invio link al telefono
Formattare il link nel formato richiesto (`micamera://open?foreground_input=...`) e inviare via ADB:
```bash
adb -s 99c85bcc shell am start -a android.intent.action.VIEW \
  -d "micamera://open?foreground_input=5B0-eRAARn16PGqD2A4En2Gg..."
```

Risultato atteso:
```
Starting: Intent { act=android.intent.action.VIEW dat=micamera://... }
```
Se appare anche:
```
Warning: Activity not started, its current task has been brought to the front
```
→ l'app `micamera` era già aperta; l'intent è stato comunque consegnato.

### 6. Note
- Il link può essere molto lungo (es. 503 caratteri); `am start` lo accetta senza problemi.
- Se il dispositivo è `offline` (es. `127.0.0.1:5555`), riconnetterlo con `adb connect`.
- Per decodifica locale è necessario installare `pyzbar` (`pip install pyzbar`) e `Pillow`.

---
## Seconda immagine: "拍大海" (Dashboard 20261101_100856 / image_075ad6)
- Tema: mare (拍大海)
- Profilo: LEICA CHR / Leica Classic
- Parametri: EV 0, ISO AUTO, WB AWB, F AUTO, contrast -10, temp -10, tint 0, saturation 10, sharpness 5, zoom 3.2x Tele, metering center-weighted, AF AUTO
- QR content: micamera://open?foreground_input=z8ZKILbXF57vVaLuEFmdvrHDqif_mpMgDhgAP6PHEOkIX-nw8x6FrdunmJZN2-9dldi4T6Z0s5B_rUBfZUxYFm4rlCSOMiJGojMZIsed4tKa-cuVvn8Ki9acRpK20WUYUq0o-FlGCZO8rlL-Y1cssgx3pM99VIhWAKo6jvQl5VYJcK7MX0u_YZDz0mRZu33qjLkrjhvrmp7TaP9skHNJePNPkM2uUNVW-gayUVwFdoep80Q93S8SzO8JQLSjeWPYJSyNW73vcJmYgWQ4Hmz8yiXrCGcbYYZ1WWSIt2vjI7gkYfqc88UMb-o8etLFm7ea4QL8y-SJwnX8dVu1eeSDOanRvYWe9LFW-hjSYoLmqAPlV7pvVpA5PqZayjtpcYqLZXNVBmwFyK673lieboPL8Ed5zb6oRlZgkC3_9_-G2vGEajLBlP3H5fFLfAE2bJ0Xk3efd7fGEBdFcCqxMpGVPw
- Modello da usare per riconoscimento: Inkling (thinkingmachines/inkling:free) — il picker deve selezionarlo perché vision_analyze con nemotron restituisce 404
- Fallback locale: PIL + pyzbar (installato via pip)
- Device Xiaomi per ADB: 99c85bcc (Xiaomi 14 Ultra / codename nezha)
- Comando ADB: `adb -s 99c85bcc shell am start -a android.intent.action.VIEW -d "micamera://open?foreground_input=..."`
- Risultato intent: `Starting: Intent { ... }` (consegnato con successo al device)
