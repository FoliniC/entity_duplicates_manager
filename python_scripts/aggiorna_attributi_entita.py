allowed_entities = [
    "sensor.climate_advice_cucina",
    "sensor.climate_advice_camera_grande",
    "sensor.climate_advice_camera",
    "sensor.climate_advice_corridoio",
    "sensor.climate_advice_bagno",
    "sensor.climate_advice_sala",
]

allowed_attributes = [
    "ultimo_consiglio_finestra",
    "snapshot_consiglio_finestra_timestamp",
    "snapshot_consiglio_finestra_umidita",
    "snapshot_consiglio_finestra_omega_interna",
    "snapshot_consiglio_finestra_omega_esterna",
    "snapshot_consiglio_finestra_delta_omega",
    "snapshot_consiglio_finestra_trend",
    "snapshot_consiglio_finestra_finestra",
    "snapshot_consiglio_finestra_fancoil",
]

entity_id = data.get("entity_id")
attributes = data.get("attributes", {})

if entity_id not in allowed_entities:
    logger.error("aggiorna_attributi_entita: entity_id non consentito: %s", entity_id)
else:
    current = hass.states.get(entity_id)
    if current is None:
        logger.error("aggiorna_attributi_entita: entita non trovata: %s", entity_id)
    elif not isinstance(attributes, dict):
        logger.error("aggiorna_attributi_entita: attributes deve essere un dizionario")
    else:
        new_attributes = dict(current.attributes)
        updated_count = 0

        for attr_name, attr_value in attributes.items():
            if attr_name in allowed_attributes:
                if attr_value is None:
                    attr_value = ""
                if isinstance(attr_value, bool):
                    attr_value = "true" if attr_value else "false"
                if new_attributes.get(attr_name) != attr_value:
                    new_attributes[attr_name] = attr_value
                    updated_count += 1
            else:
                logger.warning(
                    "aggiorna_attributi_entita: attributo ignorato per %s: %s",
                    entity_id,
                    attr_name,
                )

        hass.states.set(entity_id, current.state, new_attributes)
        logger.info(
            "aggiorna_attributi_entita: aggiornati %s attributi su %s",
            updated_count,
            entity_id,
        )
