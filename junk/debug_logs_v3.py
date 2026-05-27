import logging
import sys
sys.path.insert(0, '/home/carlo/docker/homeassistant/config/custom_components/localtuya/core')
import pytuya
from tuya_gui import ListHandler

h = ListHandler()
pytuya._LOGGER.addHandler(h)
pytuya._LOGGER.setLevel(logging.DEBUG)

# Trigger a log
pytuya._LOGGER.debug("TESTING")
print(f"Captured: {h.records}")
