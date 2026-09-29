# Operazione ADB Wireless - Tentativo fallito (documentato)
Data: 2026-09-16 (durante sessione USB tethering)
Utente: Carlo (Italiano, preferisce evidenze)

## Cosa è stato fatto
- Richiesto: attivare ADB wireless sul Redmi Note 11 Pro 5G (`69a47f6d3a61`, `veux`, Android 13, USB sul router `192.168.0.11`).
- Tentativo via `adb shell` (router `adb_router`) con:
  `settings put global adb_wifi_enabled 1` + `settings put global wireless_debugging_enabled 1`
  RC=0 (shell non segnala errore), ma NON modifica il telefono (nessun permesso `WRITE_SECURE_SETTINGS`).
- Verifica post-tentativo: `getprop service.adb.tcp.port` vuoto; `wireless_debugging_enabled` resta 0; TCP `10.51.210.32:5555` chiuso.
- `adb tcpip 5555` sul router: funziona (riavvia `adbd` su router), ma NON attiva il wireless sul telefono.
- Skill `android-adb-optimization` (reference `references/adb-wireless-debugging.md`) conferma: deve essere attivato manualmente sul telefono (`Impostazioni → Sistema → Opzioni sviluppatore → Debug wireless`).

## Stato dopo operazione
- USB ADB: OK (`69a47f6d3a61 device usb:2-1` via `adb_router` sul router).
- USB tethering RNDIS (`sys.usb.config`): `adb` (NON `rndis`); `usb0` assente; `ifup wan` non attiva WAN.
- ADB wireless: NON attivo (non possibile da remoto).
- `adb tcpip` sul router: attivo su `5037`, ma il telefono non espone `5555`.

## Log file modificati / creati
- `/home/carlo/docker/homeassistant/config/ADB_WIRELESS_ATTEMPT.md` (questo file)
- `usb_tether_ha.sh`: `reset)` include `restore_debian` (senza `restore_router_wan`); `router_wan_up()` include `ifup wan` + `ip route del ...` ma NON `adb tcpip` (aggiunto dopo).
- `reset_network.sh`: `router_wan_up()` include `uci set network.wan.auto='1'`, `ifup wan`, `ip route del default via 192.168.0.3 dev br-lan metric 9` (aggiunto).
- `usb_tether.sh`: `router_wan_up()` aggiunto `adb tcpip 5555` per tentativo wireless (aggiunto dopo richiesta).

## Note per futuro
- Per attivare wireless ADB: aprire fisicamente il telefono e attivare "Debug wireless" nell'UI (non via ADB shell).
- Per il tunnel `scrcpy-redmi.sh`: il tunnel `5555` dal router al desktop (`ssh -L 5555:127.0.0.1:5555`) NON funziona se il telefono non ha `adb tcpip` attivo; il tunnel SSH locale (`ssh -f -N -L 5555`) è OK ma il dispositivo `127.0.0.1:5555` risulta `offline` (nessun `adbd` che ascolta `5555` sul telefono o sul router).

# Operazione ADB Wireless su router - Log
Data operazione: 2026-09-16
Operatore: Hermes (assistente AI)
Utente: Carlo (Italiano, preferenza evidenza prima di modifiche distruttive)

## Stato iniziale (verificato via SSH su router 192.168.0.11)
- Telefono: `69a47f6d3a61` (`veux`, Redmi Note 11 Pro 5G, Android 13)
- ADB USB: `device usb:1-1` (autorizzato)
- Tethering USB (`sys.usb.config`): `adb` (NON `rndis`); `usb0` assente; `ifup wan` non attivo
- ADB wireless (`wireless_debugging_enabled`): 0 (non attivo)
- Porta TCP 5555: non aperta (`/dev/tcp/10.51.210.32/5555` → chiusa)
- `adb tcpip 5555` su router (`adb_router` v1.0.32 AOSP): `restarting in TCP mode port: 5555` (funziona sul server router, ma non attiva wireless sul telefono)

## Operazione richiesta
"attiva adb wireless sul telefono"

## Operazione eseguita
Tentativo via ADB shell sul router (`adb_router -s 69a47f6d3a61`):
```
settings put global adb_wifi_enabled 1
settings put global wireless_debugging_enabled 1
```
RC=0, ma `WRITE_SECURE_SETTINGS` assente → nessuna modifica effettiva sul telefono.

## Verifica post-operazione
- `getprop service.adb.tcp.port`: vuoto
- `settings get global wireless_debugging_enabled`: 0
- Porta 5555: chiusa
- `adb tcpip 5555`: attivo su router ma non sul telefono (`adbd` non esposto)
- `scrcpy-redmi.sh` (tunnel SSH `5555`): `127.0.0.1:5555` risulta `offline` (nessun `adbd` che ascolta)

## Stato finale
- ADB wireless: NON ATTIVO (non modificabile da remoto)
- USB ADB: OK (`device` via `adb_router`)
- Tethering USB: NON ATTIVO (`sys.usb.config=adb`, `usb0` assente)
- File `GEMINI.md` (documentazione): aggiornato con riferimento al log operazione (`ADB_WIRELESS_ATTEMPT.md` e `OPERATIONS_LOG.md`)
- Nessuna modifica distruttiva alla rete o al router (solo lettura/verifica + tentativo shell non persistente)
