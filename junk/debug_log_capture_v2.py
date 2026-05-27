import logging
import sys
# Configure root logger to include pytuya
logging.basicConfig(level=logging.DEBUG)

# Mock ListHandler
class ListHandler(logging.Handler):
    def __init__(self):
        super().__init__(); self.records = []
    def emit(self, record): self.records.append(self.format(record))

h = ListHandler()
log = logging.getLogger('pytuya')
# Important: ensure propagate is true so it reaches handlers if any,
# but we are attaching directly to the logger instance.
log.addHandler(h)

log.debug("DEBUG TEST")
print(f"Captured: {h.records}")
