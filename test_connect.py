import sys
sys.path.insert(0, '/home/carlo/docker/homeassistant/config/custom_components/localtuya/core')
try:
    from pytuya import connect
    print("pytuya.connect imported successfully")
except ImportError as e:
    # Let's inspect the traceback
    import traceback
    traceback.print_exc()
