"""
BTC Tracker App — Initializes the BTC Investment Tracker services.
This app is loaded by pyscript after it initializes, ensuring decorators are available.
"""
# The module registers its services when imported in pyscript context
import sys
sys.path.append("/config/pyscript/modules")
import btc_tracker

# The module registers its services when imported in pyscript context
# This file is executed by pyscript after it initializes