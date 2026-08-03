"""
HALog2026 App — Initializes the HALog2026 logging service.
This app is loaded by pyscript after it initializes, ensuring decorators are available.
"""
# The module registers its services when imported in pyscript context
import sys
sys.path.append("/config/pyscript/modules")
import halog2026_events_write

# The module registers its services when imported in pyscript context
# This file is executed by pyscript after it initializes
