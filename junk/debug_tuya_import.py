import logging
import importlib
import sys
# Set up handler early
h = logging.Handler() # Just a dummy to check if it gets called
# Actually, let's use our ListHandler
class ListHandler(logging.Handler):
    def __init__(self):
        super().__init__(); self.records = []
    def emit(self, record): self.records.append(self.format(record))
h = ListHandler()

# Ensure we are using the local pytuya
sys.path.insert(0, '/home/carlo/docker/homeassistant/config/custom_components/localtuya/core')
import pytuya
logging.getLogger('pytuya').addHandler(h)

# Trigger a log
pytuya._LOGGER.debug("TESTING")
print(f"Captured: {h.records}")
