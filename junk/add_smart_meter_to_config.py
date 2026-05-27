import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

file_path = '/config/.storage/core.config_entries'

# Device Configuration
new_device_id = "bf0e2041fb7f7875c4bcss"
new_device_config = {
    "device_id": new_device_id,
    "host": "192.168.0.28",
    "local_key": "HTV}N2)7)Rl3!'v<",
    "friendly_name": "Smart Meter 2025 A=PDC",
    "protocol_version": "3.4",
    "product_key": "v5jlnn5hwyffkhp3",
    "scan_interval": 0,
    "manual_dps_strings": "1,2,101,102,103,104,105,106,109,110,111",
    "dps_strings": ["1 (value: 0)", "2 (value: 0)", "101 (value: 2300)", "102 (value: 5000)", "103 (value: 0)", "105 (value: 0)", "106 (value: 0)"],
    "enable_debug": True,
    "entities": [
        {"id": "1", "platform": "sensor", "friendly_name": "Total Consumed Energy", "device_class": "energy", "state_class": "total_increasing", "unit_of_measurement": "kWh", "scaling": 0.01},
        {"id": "2", "platform": "sensor", "friendly_name": "Total Produced Energy", "device_class": "energy", "state_class": "total_increasing", "unit_of_measurement": "kWh", "scaling": 0.01},
        {"id": "101", "platform": "sensor", "friendly_name": "Voltage", "device_class": "voltage", "state_class": "measurement", "unit_of_measurement": "V", "scaling": 0.1},
        {"id": "102", "platform": "sensor", "friendly_name": "Frequency", "device_class": "frequency", "state_class": "measurement", "unit_of_measurement": "Hz", "scaling": 0.01},
        {"id": "103", "platform": "sensor", "friendly_name": "Total Power", "device_class": "power", "state_class": "measurement", "unit_of_measurement": "W", "scaling": 0.1},
        {"id": "104", "platform": "sensor", "friendly_name": "Power Factor A", "device_class": "power_factor", "state_class": "measurement", "scaling": 0.01},
        {"id": "105", "platform": "sensor", "friendly_name": "Current Phase A", "device_class": "current", "state_class": "measurement", "unit_of_measurement": "A", "scaling": 0.001},
        {"id": "106", "platform": "sensor", "friendly_name": "Power Phase A", "device_class": "power", "state_class": "measurement", "unit_of_measurement": "W", "scaling": 0.1},
        {"id": "109", "platform": "sensor", "friendly_name": "Power Factor B", "device_class": "power_factor", "state_class": "measurement", "scaling": 0.01},
        {"id": "110", "platform": "sensor", "friendly_name": "Current Phase B", "device_class": "current", "state_class": "measurement", "unit_of_measurement": "A", "scaling": 0.001},
        {"id": "111", "platform": "sensor", "friendly_name": "Power Phase B", "device_class": "power", "state_class": "measurement", "unit_of_measurement": "W", "scaling": 0.1}
    ]
}

try:
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    found = False
    for entry in data['data']['entries']:
        if entry['domain'] == 'localtuya':
            if 'devices' not in entry['data']:
                entry['data']['devices'] = {}
            
            # Check if device already exists to update or add new
            if new_device_id in entry['data']['devices']:
                logger.info(f"Updating existing device {new_device_id}")
            else:
                logger.info(f"Adding new device {new_device_id}")
            
            entry['data']['devices'][new_device_id] = new_device_config
            found = True
            break
    
    if found:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info("Successfully updated core.config_entries")
    else:
        logger.error("Could not find localtuya entry in core.config_entries")

except Exception as e:
    logger.error(f"Failed to update config: {e}")
