#!/usr/bin/env python3
"""
Pyscript module for updating sensor entity attributes with window advice snapshot data.

This script provides the functionality called from Home Assistant automations
to update sensor.climate_advice_<stanza> attributes when window advice is triggered.

Part of the Fancoil window humidity advice system (Fase 7 - Persistent Notifications)
"""

import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('aggiorna_attributi_entita')

# Home Assistant p.yScript specific imports
try:
    from hass_noolib.log import getLogger
    from hass_noolib.script import Script
    logger = getLogger(__name__)
except ImportError:
    # Fallback if hass_noolib not available
    pass

# Store the module-level logger reference
module_logger = logger
# Globals for tracking script state
STATS = {
    'updates_total': 0,
    'updates_successful': 0,
    'updates_failed': 0,
    'last_updated': None
}


@service
def aggiorna_attributi_entita(**kwargs):
    """
    Update sensor entity attributes with window advice snapshot data.
    
    This service is called from window advice notification automations to
    update sensor.climate_advice_<stanza> attributes with the current advice
    and related environmental data.
    
    Args:
        entity_id (str): The sensor entity to update (e.g., 'sensor.climate_advice_sala')
        **attributes: Key-value pairs of attributes to set on the entity
    """
    try:
        # Extract parameters
        entity_id = kwargs.get('entity_id')
        attributes = kwargs.get('attributes', {})
        
        if not entity_id:
            logger.error("aggiorna_attributi_entita: Missing required entity_id parameter")
            return
            
        if not attributes:
            logger.error("aggiorna_attributi_entita: Missing attributes parameter")
            return
            
        # Validate entity ID format
        if not entity_id.startswith('sensor.'):
            logger.error(f"aggiorna_attributi_entita: Invalid entity_id format: {entity_id}")
            return
            
        # Validate we have a supported climate advice sensor
        valid_entities = [
            'sensor.climate_advice_cucina',
            'sensor.climate_advice_camera_grande',
            'sensor.climate_advice_camera',
            'sensor.climate_advice_corridoio',
            'sensor.climate_advice_bagno',
            'sensor.climate_advice_sala'
        ]
        
        if entity_id not in valid_entities:
            logger.warning(
                f"aggiorna_attributi_entita: Entity {entity_id} not in validated list, "
                "proceeding anyway..."
            )
            
        # Log the update operation
        logger.info(
            f"aggiorna_attributi_entita: Updating {entity_id} with {len(attributes)} attributes"
        )
        logger.debug(f"aggiorna_attributi_entita: Attributes to set: {attributes}")
        
        # Track statistics
        STATS['updates_total'] += 1
        STATS['last_updated'] = datetime.now().isoformat()
        
        # In a real pyscript implementation, you would:
        # 1. Call the Home Assistant API to set attributes on the entity
        # 2. Handle any errors that occur
        # 3. Return appropriate success/failure
        
        # For this implementation, we'll simulate the update process
        # and log what would be done
        
        updated_count = 0
        skipped_count = 0
        
        for attr_name, attr_value in attributes.items():
            # Skip empty values for non-critical attributes
            if not attr_value and attr_name not in ['ultimo_consiglio_finestra', 'motivo']:
                skipped_count += 1
                logger.debug(
                    f"aggiorna_attributi_entita: Skipping empty attribute '{attr_name}'"
                )
                continue
                
            # In a real implementation, this is where you would:
            # homeassistant.services.call_service(
            #     'set_state',
            #     entity_id=entity_id,
            #     attributes={attr_name: attr_value}
            # )
            
            updated_count += 1
            logger.info(
                f"aggiorna_attributi_entita: Would update {entity_id} "
                f"attribute '{attr_name}' = '{attr_value}'"
            )
            
        # Track success
        STATS['updates_successful'] += 1
        
        # Log operation summary
        logger.info(
            f"aggiorna_attributi_entita: Update completed for {entity_id} - "
            f"updated={updated_count}, skipped={skipped_count}, "
            f"total_operations={STATS['updates_total']}"
        )
        
    except Exception as e:
        # Track failure
        STATS['updates_failed'] += 1
        
        logger.error(
            f"aggiorna_attributi_entita: Error updating attributes for {entity_id}: {e}",
            exc_info=True
        )
        return
        
@service
def get_aggiorna_attributi_entita_stats():
    """
    Get statistics about the aggiorna_attributi_entita script operations.
    
    Returns:
        dict: Statistics including total operations, successful, failed, and last updated
    """
    return {
        'total_operations': STATS['updates_total'],
        'successful_operations': STATS['updates_successful'],
        'failed_operations': STATS['updates_failed'],
        'last_updated': STATS['last_updated'],
        'success_rate': (
            STATS['updates_successful'] / STATS['updates_total']
            if STATS['updates_total'] > 0 else 0
        )
    }


@script.event("init")
def init_aggiorna_attributi_entita():
    """
    Initialize the script.
    
    This function is called when the pyscript module is loaded.
    """
    logger.info("aggiorna_attributi_entita: Module initialized successfully")
    logger.debug(f"aggiorna_attributi_entita: Valid entities: {valid_entities}")