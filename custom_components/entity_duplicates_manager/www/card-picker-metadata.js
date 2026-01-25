// Ensures Entity Duplicates Manager appears in the card picker
(function () {
    try {
        window.customCards = window.customCards || [];
        const type = 'entity-duplicates-manager-card';
        const idx = window.customCards.findIndex((c) => c.type === type || c.type === 'custom:entity-duplicates-manager-card');
        const meta = {
            type: 'entity-duplicates-manager-card',
            name: 'Entity Duplicates Manager',
            description: 'Manage and clean up duplicate entities in Home Assistant',
            preview: true,
            documentationURL: 'https://github.com/FoliniC/entity_duplicates_manager'
        };
        if (idx === -1) {
            window.customCards.push(meta);
        } else {
            window.customCards[idx] = meta;
        }
        console.debug('[Entity Duplicates Manager] card-picker-metadata applied');
    } catch (e) {
        console.warn('[Entity Duplicates Manager] Unable to set card picker metadata:', e);
    }
})();
