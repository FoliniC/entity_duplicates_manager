import logging
import sys
# Mock ListHandler for local testing
class ListHandler(logging.Handler):
    def __init__(self):
        super().__init__(); self.records = []
    def emit(self, record): self.records.append(self.format(record))

# Configure logger
h = ListHandler()
log = logging.getLogger('pytuya')
log.addHandler(h)
log.setLevel(logging.DEBUG)

# Log something
log.debug("This is a test message")

print(f"Records captured: {h.records}")
