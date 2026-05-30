import logging
logger = logging.getLogger("debug_sensor")
entity_id = "sensor.th3c_temperature_humidity_temperature"
state = hass.states.get(entity_id)

if state:
    unit = state.attributes.get("unit_of_measurement")
    logger.error(f"[DEBUG_SENSOR] Entity: {entity_id}")
    logger.error(f"[DEBUG_SENSOR] Raw Unit of Measurement: '{unit}'")
    logger.error(f"[DEBUG_SENSOR] Hex representation: {[hex(ord(c)) for c in unit] if unit else 'None'}")
else:
    logger.error(f"[DEBUG_SENSOR] Entity {entity_id} not found.")
