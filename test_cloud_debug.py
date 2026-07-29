#!/usr/bin/env python3
"""
Debug script to examine cloud devices endpoint and identify why it's returning empty results
"""
import asyncio
import json
import logging
import sys
from pathlib import Path

# Add the localtuya core path
sys.path.insert(0, str(Path(__file__).parent / "custom_components" / "localtuya" / "core"))

from cloud_api import TuyaCloudApi, DEVICES_UPDATE_INTERVAL

# Configure logging to see debug output
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

async def test_cloud_api_endpoint():
    """Test the TuyaCloudApi with the same configuration as tuya_gui.py"""
    
    # Simulate the cloud configuration that might be in HA config
    # These should come from HA config, but for debugging we'll try common values
    cloud_conf = {
        "region": "eu",  # or "cn", "ea", "in", "us", "we", "sg"
        "client_id": "YOUR_CLIENT_ID_HERE",
        "client_secret": "YOUR_CLIENT_SECRET_HERE", 
        "user_id": "YOUR_USER_ID_HERE",
    }
    
    print("=" * 80)
    print("TESTING TUYA CLOUD API ENDPOINT")
    print("=" * 80)
    print(f"Configuration:")
    print(f"  Region: {cloud_conf['region']}")
    print(f"  Client ID: {cloud_conf['client_id']}")
    print(f"  Client Secret: {cloud_conf['client_secret'][:8]}...")
    print(f"  User ID: {cloud_conf['user_id'][:8]}...")
    print(f"Timestamp: {__import__('time').strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    try:
        # Initialize the cloud API client
        api = TuyaCloudApi(
            cloud_conf["region"],
            cloud_conf["client_id"],
            cloud_conf["client_secret"],
            cloud_conf["user_id"]
        )
        
        print("1. Attempting to connect to Tuya Cloud API...")
        connect_result = await api.async_connect()
        print(f"   Connection result: {connect_result}")
        print()
        
        print("2. Getting access token...")
        token_result = await api.async_get_access_token()
        print(f"   Token result: {token_result}")
        print(f"   Access token: {api._access_token[:16]}...") if api._access_token else print("   Access token: None")
        print(f"   Token expire time: {api._token_expire_time}")
        print()
        
        print("3. Getting devices list...")
        devices_result = await api.async_get_devices_list(force_update=True)
        print(f"   Devices list result: {devices_result}")
        print()
        
        print("4. Checking device_list content...")
        if hasattr(api, 'device_list') and api.device_list:
            print(f"   Number of devices in device_list: {len(api.device_list)}")
            if len(api.device_list) > 0:
                print("   Sample device keys:", list(api.device_list.keys())[:3])
                print("   Sample device data (first device):")
                print(json.dumps(api.device_list[list(api.device_list.keys())[0]], 
                               indent=2, default=str))
            else:
                print("   Device list is empty!")
        else:
            print("   No device_list attribute or it's empty")
        print()
        
        if hasattr(api, 'cached_device_list') and api.cached_device_list:
            print(f"5. Cached device list size: {len(api.cached_device_list)}")
        print()
        
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {str(e)}")
        print()
        import traceback
        print("Full traceback:")
        traceback.print_exc()
        
        print()
        print("=" * 80)
        print("POSSIBLE CAUSES:")
        print("=" * 80)
        print("1. Invalid or expired Tuya Cloud API credentials")
        print("2. Network connectivity issues to Tuya servers")
        print("3. incorrect region code (should be 'eu' for Europe, 'cn' for China, etc.)")
        print("4. User account not registered for Tuya Cloud services")
        print("5. API rate limiting or temporary service issues")
        print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_cloud_api_endpoint())