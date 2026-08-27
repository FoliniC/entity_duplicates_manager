"""Faulthandler watchdog: dump automatico dello stack Python se l'event loop si blocca.

Programma un timer DI SISTEMA (thread separato, funziona anche con event loop
congelato) che ogni 180 secondi controlla... in realta' dump_traceback_later scrive
lo stack quando scade. Con repeat=True e cancel al reset, otteniamo: se il loop
e' vivo, il timer viene continuamente rinnovato (reset each loop iteration via
async_track_time_interval); se e' bloccato >180s, il dump viene scritto su file.
"""
from __future__ import annotations

import faulthandler
import logging
import sys

from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval
import homeassistant.loader as loader

DOMAIN = "faulthandler_watch"
DUMP_FILE = "/config/faulthandler_dump.txt"
INTERVAL = 60  # rinnovo del timer
TIMEOUT = 180  # soglia di blocco

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config) -> bool:
    # Apertura file fuori dall'event loop (evita blocking call warning)
    fh = await hass.async_add_executor_job(open, DUMP_FILE, "a", 1)

    def arm() -> None:
        # dump_traceback_later cancella il timer precedente quando repeat=False;
        # con repeat=True non serve riarmo, ma usiamo cancel+arm per misurare
        # l'assenza di rinnovi dal loop.
        faulthandler.cancel_dump_traceback_later()
        faulthandler.dump_traceback_later(TIMEOUT, file=fh, repeat=False)

    # Rinnova il timer a ogni tick DELL'EVENT LOOP: se il loop gira, il timer
    # viene sempre cancellato prima della scadenza -> nessun dump.
    async_track_time_interval(hass, lambda now: arm(), __import__("datetime").timedelta(seconds=INTERVAL))

    _LOGGER.warning("faulthandler_watch attivo: dump su %s se il loop blocca per >%ss", DUMP_FILE, TIMEOUT)
    return True
