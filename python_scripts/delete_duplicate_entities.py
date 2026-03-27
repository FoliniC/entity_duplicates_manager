# Script Python per ELIMINARE le Entità Duplicate
# Versione: 1.1 (No imports version)

# Ottieni il parametro per conferma
confirm = data.get('confirm', False)

if not confirm:
    logger.error("ERRORE: Devi confermare l'eliminazione impostando confirm=true")
    hass.states.set(
        'sensor.last_deletion_result',
        'Errore: Conferma richiesta',
        {'friendly_name': 'Risultato Ultima Eliminazione', 'icon': 'mdi:alert'}
    )
else:
    # Ottieni tutte le entità
    all_entities = hass.states.all()
    
    # Lista entità da rimuovere
    entities_removed = []
    entities_failed = []
    
    # Analizza e rimuovi
    for state in all_entities:
        entity_id = state.entity_id
        
        if "_" in entity_id:
            parts = entity_id.split("_")
            last_part = parts[-1]
            
            if last_part.isdigit():
                # Verifichiamo se esiste l'entità "base"
                base_entity_id = "_".join(parts[:-1])
                if hass.states.get(base_entity_id) is not None:
                    try:
                        # Rimuovi l'entità dallo stato attuale
                        hass.states.remove(entity_id)
                        entities_removed.append(entity_id)
                        logger.info("✓ Rimossa (stato): " + entity_id)
                    except Exception as e:
                        entities_failed.append(entity_id)
                        logger.error("✗ Errore rimozione " + entity_id + ": " + str(e))
    
    # Aggiorna il sensore con i risultati
    result_text = "Rimosse: " + str(len(entities_removed)) + ", Errori: " + str(len(entities_failed))
    
    hass.states.set(
        'sensor.last_deletion_result',
        result_text,
        {
            'friendly_name': 'Risultato Ultima Eliminazione',
            'icon': 'mdi:check-circle' if len(entities_failed) == 0 else 'mdi:alert',
            'removed_count': len(entities_removed),
            'failed_count': len(entities_failed)
        }
    )
    
    # Reset conferma
    hass.states.set('input_boolean.confirm_entity_deletion', 'off', {
        'friendly_name': 'Conferma Eliminazione Entità',
        'icon': 'mdi:alert-circle'
    })
    
    # Reset lista e conteggio
    hass.states.set('sensor.duplicate_entities_count', '0', {
        'friendly_name': 'Numero Entità Duplicate',
        'icon': 'mdi:numeric',
        'unit_of_measurement': 'entità'
    })
    hass.states.set('input_text.duplicate_entities_list', 'Operazione completata', {
        'friendly_name': 'Lista Entità Duplicate',
        'icon': 'mdi:check-circle'
    })
    
    logger.info("Operazione completata: " + result_text)
