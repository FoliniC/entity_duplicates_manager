"""One-shot: ricarica tutte le automazioni e poi si autoelimina."""
import os

@time_trigger("startup")
def reload_on_startup():
    hass.services.call("automation", "reload")
    log.info("reload_ev_automation: automation reload eseguito")
    # Autoeliminazione: rimuovi questo file dopo l'esecuzione
    try:
        os.remove("/config/pyscript/reload_ev_automation.py")
        log.info("reload_ev_automation: file rimosso")
    except Exception as e:
        log.warning(f"reload_ev_automation: impossibile rimuovere file: {e}")
