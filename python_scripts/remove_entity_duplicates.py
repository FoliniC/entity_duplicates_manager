# Script Python per Home Assistant - Rimozione Entità Duplicate
# Versione: 1.1 (No imports version)

# Ottieni tutte le entità
all_entities = hass.states.all()

# Lista delle entità da rimuovere
entities_to_remove = []

# Analizza tutte le entità cercando pattern tipo name_2, name_3
for state in all_entities:
    entity_id = state.entity_id
    
    # Cerchiamo l'ultimo underscore
    if "_" in entity_id:
        parts = entity_id.split("_")
        last_part = parts[-1]
        
        # Se l'ultima parte è un numero, lo consideriamo un potenziale duplicato
        if last_part.isdigit():
            # Verifichiamo se esiste l'entità "base" (senza _N)
            # Esempio: se abbiamo sensor.luce_2, verifichiamo se esiste sensor.luce
            base_entity_id = "_".join(parts[:-1])
            if hass.states.get(base_entity_id) is not None:
                entities_to_remove.append(entity_id)

# Ordina la lista alfabeticamente
entities_to_remove.sort()

# Log delle entità trovate
logger.info("Trovate " + str(len(entities_to_remove)) + " entità duplicate:")
for eid in entities_to_remove:
    logger.info("  - " + eid)

# Salva la lista in un input_text per visualizzazione nella dashboard
if len(entities_to_remove) > 0:
    entities_text = ", ".join(entities_to_remove)
    
    # Limita a 255 caratteri per input_text
    if len(entities_text) > 255:
        entities_text = entities_text[:252] + "..."
    
    hass.states.set(
        'input_text.duplicate_entities_list',
        entities_text,
        {
            'friendly_name': 'Lista Entità Duplicate',
            'icon': 'mdi:format-list-bulleted',
            'count': len(entities_to_remove)
        }
    )
    
    hass.states.set(
        'sensor.duplicate_entities_count',
        str(len(entities_to_remove)),
        {
            'friendly_name': 'Numero Entità Duplicate',
            'icon': 'mdi:numeric',
            'unit_of_measurement': 'entità'
        }
    )
else:
    logger.info("Nessuna entità duplicata trovata!")
    hass.states.set(
        'input_text.duplicate_entities_list',
        "Nessun duplicato trovato",
        {
            'friendly_name': 'Lista Entità Duplicate',
            'icon': 'mdi:check-circle'
        }
    )
    hass.states.set(
        'sensor.duplicate_entities_count',
        "0",
        {
            'friendly_name': 'Numero Entità Duplicate',
            'icon': 'mdi:numeric',
            'unit_of_measurement': 'entità'
        }
    )
