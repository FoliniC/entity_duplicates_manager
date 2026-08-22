"""
Phone Price Projection App — Initializes the Phone Price Projection services.
This app is loaded by pyscript after it initializes, ensuring decorators are available.
"""
# The module registers its services when imported in pyscript context
import sys
sys.path.append("/config/pyscript/modules")
import phone_price_projection

# The module registers its services when imported in pyscript context
# This file is executed by pyscript after it initializes