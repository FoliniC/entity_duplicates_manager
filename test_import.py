import sys
import os
from pathlib import Path
sys.path.append("/home/carlo/docker/homeassistant/config/custom_components/localtuya/core")
try:
    from pytuya import connect
    print("pytuya connect imported successfully")
except ImportError as e:
    print(f"pytuya connect failed: {e}")
try:
    from cloud_api import TuyaCloudApi
    print("TuyaCloudApi imported successfully")
except ImportError as e:
    print(f"TuyaCloudApi failed: {e}")
