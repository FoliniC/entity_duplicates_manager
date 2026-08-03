# PowerShell Window Monitor

Monitora una finestra PowerShell e preme automaticamente un tasto quando viene visualizzato un testo specifico.

## Due implementazioni disponibili:

### 1. Versione Python (consigliata) - `monitor_powershell.py`

Più robusta, usa `pywinauto` per automazione UI completa.

#### Installazione dipendenze:
```powershell
pip install -r requirements.txt
```

#### Utilizzo:
```powershell
# Base (cerca finestra con "PowerShell" nel titolo)
python monitor_powershell.py

# Personalizzato
python monitor_powershell.py --title "Mia Finestra" --trigger "Allow execution of \[Shell\]?" --key "2" --interval 0.5

# Elenca finestre PowerShell trovate
python monitor_powershell.py --list-windows
```

#### Parametri:
| Parametro | Default | Descrizione |
|-----------|---------|-------------|
| `--title` | "PowerShell" | Testo da cercare nel titolo finestra |
| `--trigger` | "Allow execution of [Shell]?" | Testo che attiva l'invio tasto |
| `--key` | "2" | Tasto da premere |
| `--interval` | 0.5 | Secondi tra controlli |
| `--list-windows` | - | Elenca finestre ed esce |

---

### 2. Versione PowerShell pura - `Monitor-PowerShellWindow.ps1`

Nessuna dipendenza esterna, usa API Windows native via .NET.

#### Utilizzo:
```powershell
# Base
.\Monitor-PowerShellWindow.ps1

# Personalizzato
.\Monitor-PowerShellWindow.ps1 -WindowTitlePattern "*PowerShell*" -TriggerText "Allow execution of [Shell]?" -KeyToSend "2" -CheckIntervalMs 500
```

#### Parametri:
| Parametro | Default | Descrizione |
|-----------|---------|-------------|
| `-WindowTitlePattern` | `*PowerShell*` | Pattern titolo finestra (wildcard) |
| `-TriggerText` | `Allow execution of [Shell]?` | Testo trigger |
| `-KeyToSend` | `2` | Tasto da inviare |
| `-CheckIntervalMs` | `500` | Intervallo ms tra controlli |

---

## Note importanti

1. **Permessi**: Se la finestra PowerShell target è "Run as Administrator", esegui anche lo script di monitoraggio come Amministratore.

2. **Focus finestra**: Lo script porta la finestra in foreground per inviare il tasto. Se stai lavorando su altro, l'input verrà diretto alla finestra PowerShell.

3. **Testo nelle console**: Il testo "Allow execution of [Shell]?" potrebbe non essere nel titolo della finestra ma nel buffer della console. La versione Python con `pywinauto` (backend UIA) riesce a leggere il contenuto completo della console. La versione PowerShell pura legge principalmente il titolo.

4. **Riarmo automatico**: Dopo aver inviato il tasto, lo script attende che il testo trigger scompaia prima di riarmarsi, per evitare invii multipli.

## Test rapido

Per testare senza aspettare il vero trigger:

```powershell
# In una finestra PowerShell, esegui:
Write-Host "Allow execution of [Shell]?"
Read-Host "Premi invio..."
```

Poi avvia lo script puntando a quella finestra.