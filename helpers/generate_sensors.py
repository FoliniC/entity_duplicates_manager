# gen_ha_sensors.py

devices = [
    {"id": "th1a", "area": "cucina"},
    {"id": "th2b", "area": "camera_grande"},
    {"id": "th3c", "area": "bagno"},
    {"id": "th4d", "area": "strenscia"},
    # aggiungi altri dispositivi qui
]

measurement_types = [
    {"type": "temperature", "device_class": "temperature", "unit": "°C"},
    {"type": "humidity", "device_class": "humidity", "unit": "%"},
]

template_file = "/usr/share/hassio/homeassistant/managed_sensors/template_sensors.yaml"
sql_file = "/usr/share/hassio/homeassistant/sql_sensors/sql_sensors.yaml"

# Genera template sensors
with open(template_file, "w") as f:
    for dev in devices:
        for m in measurement_types:
            sensor_name = f"{dev['id']} {m['type'].capitalize()}"
            unique_id = f"{dev['id']}_{m['type']}"
            device_class = m["device_class"]
            state_class = "measurement"
            unit = m["unit"]

            base_entity = f"{dev['id']}_{m['type']}"
            sensor_th = f"sensor.{dev['id']}_temperature_humidity_{m['type']}"
            sensor_short = f"sensor.{dev['id']}_{m['type']}"
            sensor_last = f"sensor.{dev['id']}_temperature_humidity_{m['type']}_last"

            f.write(f'- name: "{sensor_name}"\n')
            f.write(f'  unique_id: "{unique_id}"\n')
            f.write(f'  state_class: "{state_class}"\n')
            f.write(f'  device_class: "{device_class}"\n')
            f.write(f'  unit_of_measurement: "{unit}"\n')
            f.write("  attributes:\n")
            f.write(f"    area: \"{{{{ area_name('sensor.{base_entity}') }}}}\"\n")
            f.write("  state: >\n")
            f.write("    {% set initial_value = 0 %}\n")
            f.write(f"    {{% if not states('{sensor_th}') | is_number %}}\n")
            f.write(
                f"      {{% if states('{sensor_short}') in [None, 'unknown', 'unavailable'] or states('sensor.1a_temperature') == -100 %}}\n"
            )
            f.write(f"        {{{{ states('{sensor_last}') | float(0) }}}}\n")
            f.write("      {% else %}\n")
            f.write(f"        {{{{ states('{sensor_short}') | float(0) }}}}\n")
            f.write("      {% endif %}\n")
            f.write("    {% else %}\n")
            f.write(f"      {{{{ states('{sensor_th}') | float(0) }}}}\n")
            f.write("    {% endif %}\n")

# Genera sql sensors
with open(sql_file, "w") as f:
    for dev in devices:
        for m in measurement_types:
            sql_sensor_name = f"{dev['id']}_temperature_humidity_{m['type']}_last"
            unique_id = sql_sensor_name
            entity_id = f"sensor.{dev['id']}_temperature_humidity_{m['type']}"
            f.write(f'- name: "{sql_sensor_name}"\n')
            f.write(f"  unique_id: {unique_id}\n")
            f.write("  query: >\n")
            f.write("    SELECT COALESCE ((\n")
            f.write("      SELECT CAST(states.state AS REAL) as state\n")
            f.write("      FROM\n")
            f.write("        states\n")
            f.write("      LEFT JOIN state_attributes ON (\n")
            f.write("        states.attributes_id = state_attributes.attributes_id\n")
            f.write("      )\n")
            f.write("      WHERE\n")
            f.write("         metadata_id = (\n")
            f.write(
                f"          SELECT metadata_id FROM states_meta WHERE entity_id = '{entity_id}'\n"
            )
            f.write("        )\n")
            f.write("       AND states.state IS NOT NULL\n")
            f.write("       AND NOT states.state in ( 'unavailable', 'unknown')\n")
            f.write("       AND CAST(states.state AS REAL) > -100\n")
            f.write("      ORDER BY states.state_id DESC\n")
            f.write("      LIMIT 1), -100.0 ) AS state;\n")
            f.write('  column: "state"\n')

print(f"File '{template_file}' e '{sql_file}' generati con successo.")
