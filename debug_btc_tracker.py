#!/usr/bin/env python3
"""
Debug script to analyze the BTC Investment Tracker configuration issues.
"""

import json
import os

def main():
    print("=== BTC Investment Tracker Configuration Analysis ===\n")
    
    # 1. Check packages directory structure
    print("1. Package Directory Structure:")
    packages_dir = "/home/carlo/docker/homeassistant/config/packages"
    if os.path.exists(packages_dir):
        files = os.listdir(packages_dir)
        print(f"   ✓ Packages directory exists with {len(files)} files")
        if "btc_investment_tracker.yaml" in files:
            print(f"   ✓ btc_investment_tracker.yaml present")
            
            # Check content
            with open(os.path.join(packages_dir, "btc_investment_tracker.yaml"), 'r') as f:
                content = f.read()
                if "template:" in content:
                    print(f"   ✓ Template sensors defined")
                if "btc_investment_eur" in content:
                    print(f"   ✓ btc_investment_eur template sensor found")
                if "unique_id: btc_avg_buy_price" in content:
                    print(f"   ⚠ Using unique_id: btc_avg_buy_price (may cause conflicts)")
        else:
            print(f"   ✗ btc_investment_tracker.yaml missing")
    else:
        print(f"   ✗ Packages directory missing")
    
    # 2. Check entity registry
    print("\n2. Entity Registry Analysis:")
    registry_path = "/home/carlo/docker/homeassistant/config/.storage/core.entity_registry"
    if os.path.exists(registry_path):
        with open(registry_path) as f:
            data = json.load(f)
        
        all_entities = data["data"]["entities"]
        btc_entities = [e for e in all_entities if 'btc' in e.get('entity_id', '').lower()]
        template_sensors = [e for e in btc_entities if e['entity_id'].startswith('sensor.') and e.get('platform') == 'template']
        rest_sensors = [e for e in btc_entities if e['entity_id'].startswith('sensor.') and e.get('platform') == 'rest']
        
        print(f"   Total BTC-related entities: {len(btc_entities)}")
        print(f"   Template sensors: {len(template_sensors)}")
        print(f"   REST sensors: {len(rest_sensors)}")
        
        # Check for critical sensors
        critical_sensors = {
            'sensor.btc_current_value': False,
            'sensor.btc_profit_loss': False,
            'sensor.btc_profit_loss_net': False,
            'sensor.bitcoin_price_eur': False,
            'sensor.target_phone_price': False
        }
        
        for e in btc_entities:
            for sensor in critical_sensors:
                if e['entity_id'] == sensor:
                    critical_sensors[sensor] = True
        
        print(f"\n   Critical Sensors Status:")
        for sensor, found in critical_sensors.items():
            status = "✓" if found else "✗"
            print(f"   {status} {sensor}")
        
        # Show unique_ids
        print(f"\n   Unique IDs in use:")
        unique_ids = list(set([e.get('unique_id') for e in btc_entities if e.get('unique_id')]))
        for uid in sorted(unique_ids):
            count = len([e for e in btc_entities if e.get('unique_id') == uid])
            print(f"     {uid}: {count} entities")
        
    else:
        print(f"   ✗ Entity registry not found")
    
    # 3. Configuration.yaml analysis
    print("\n3. Configuration.yaml Analysis:")
    config_path = "/home/carlo/docker/homeassistant/config/configuration.yaml"
    if os.path.exists(config_path):
        with open(config_path) as f:
            config_content = f.read()
        
        if "packages: !include_dir_named packages" in config_content:
            print("   ✓ packages: !include_dir_named packages is present")
        else:
            print("   ✗ packages: !include_dir_named packages NOT found")
            
        if "template: !include yaml_generator/fancoil_templates_master.yaml" in config_content:
            print("   ✓ Template entities properly included")
        else:
            print("   ✗ Template entities not properly configured")
            
        # Check for other sensor platform definitions
        if "sensor:" in config_content:
            print("   ✓ sensor: platform found")
            
    else:
        print(f"   ✗ configuration.yaml not found")
    
    print("\n=== Summary ===")
    print("Issues found:")
    print("1. Template sensors with state_class 'measurement' for monetary entities (warnings only)")
    print("2. Need to verify bitcoin_price_eur REST sensor is properly configured")
    print("3. Ensure template unique_ids don't conflict")
    print("\nRecommendations:")
    print("- Fix template sensor state_class for monetary sensors")
    print("- Check REST sensor configuration and ensure it's being loaded")
    print("- Verify entity registry is clean and correct")

if __name__ == "__main__":
    main()