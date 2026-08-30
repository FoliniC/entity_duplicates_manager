"""
Net Watchdog — auto-ripristino connessione Normale
====================================================
Fa polling ogni 60s su sensor.connessione_attiva_reale e sull'attributo
router_internet di sensor.router_internet_check. Se siamo in modalita'
Normale (input_select.usb_tether_mode = "Normale") ma la connessione reale
non e' WAN_NOTE11 (es. Router isolato, tethering caduto, dati mobile spenti)
per 2 cicli consecutivi, rilancia shell_command.usb_tether_restore (che via
router_wan_up riaccende dati mobile + tethering USB e rialza la WAN).

Nota: le automazioni YAML nei package vengono ignorate da HA (configuration.yaml
usa `automation: !include_dir_merge_list automations`), quindi questo pyscript e'
il sostituto funzionante dell'automazione di auto-ripristino.
"""
from datetime import timedelta

# Quante letture consecutive "non WAN" prima di ripristinare (evita falsi positivi
# sui cali transitori del bearer LTE di pochi secondi).
MAX_BAD = 2
bad_count = 0

@time_trigger("period(60s)")
def net_watchdog():
    global bad_count
    mode = state.get("input_select.usb_tether_mode")
    reality = state.get("sensor.connessione_attiva_reale")
    internet = state.getattr("sensor.router_internet_check", "router_internet") \
        if state.get("sensor.router_internet_check") else "unknown"

    # Log di debug (solo se qualcosa non va)
    if mode != "Normale":
        bad_count = 0
        return

    bad = (reality != "WAN_NOTE11") or (internet == "dead")
    if not bad:
        bad_count = 0
        return

    bad_count += 1
    log.info("NET_WATCHDOG: lettura #%s non-WAN (reality=%s, internet=%s)", bad_count, reality, internet)
    if bad_count >= MAX_BAD:
        log.warning("NET_WATCHDOG: ripristino Normale (restore) — reality=%s internet=%s", reality, internet)
        service.call("shell_command", "usb_tether_restore")
        bad_count = 0
        # Notifica all'utente
        service.call("persistent_notification", "create",
                     notification_id="usb_tether_autorestore",
                     title="🔧 Ripristino Normale automatico (watchdog)",
                     message="Connessione reale = %s / internet = %s ma modalita' Normale. "
                             "Watchdog ha rilanciato il restore (riaccende dati mobile + tethering USB)." % (reality, internet))
