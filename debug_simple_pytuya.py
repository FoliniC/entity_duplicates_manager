import sys
sys.path.insert(0, '/home/carlo/docker/homeassistant/config/custom_components/localtuya/core')
import pytuya
import logging

class ListHandler(logging.Handler):
    def __init__(self):
        super().__init__(); self.records = []
    def emit(self, record): self.records.append(self.format(record))

h = ListHandler()
pytuya._LOGGER.addHandler(h)
pytuya._LOGGER.setLevel(logging.DEBUG)

# Trigger something
pytuya._LOGGER.debug("HELLO WORLD")
print(f"Records: {h.records}")
