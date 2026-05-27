import logging
import sys
sys.path.insert(0, '/home/carlo/docker/homeassistant/config/custom_components/localtuya/core')
import pytuya
print(f"Logger name: {pytuya._LOGGER.name}")
# Try adding to the specific logger name
h = logging.Handler()
# ... (rest of the test)
