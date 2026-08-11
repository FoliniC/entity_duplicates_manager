/**
 * HA Clipboards Dashboard Card - Versione migliorata
 * Una custom Lovelace card per gestire multiple text clipboards
 */
class HaClipboardsCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._hass = null;
    this._config = {};
    this._entityId = 'sensor.ha_clipboards';
    this._attributes = {};
    this._activeAttribute = null;
    this._unsubscribe = null;
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error('Entity ID is required');
    }
    this._config = config;
    this._entityId = config.entity || 'sensor.ha_clipboards';
  }

  set hass(hass) {
    this._hass = hass;
    this._updateFromState();
    this.render();
  }

  connectedCallback() {
    if (this._hass) {
      this._unsubscribe = this._hass.connection.subscribeEvents(
        () => this._updateAndRender(),
        'state_changed',
        { entity_id: this._entityId }
      );
    }
  }

  disconnectedCallback() {
    if (this._unsubscribe) {
      this._unsubscribe();
      this._unsubscribe = null;
    }
  }

  _updateAndRender() {
    this._updateFromState();
    this.render();
  }

  _updateFromState() {
    if (!this._hass) return;
    const state = this._hass.states[this._entityId];
    if (state) {
      this._attributes = state.attributes.attributes || {};
      this._activeAttribute = state.attributes.active_attribute;
    }
  }

  _getAttributeNames() {
    return Object.keys(this._attributes);
  }

  _createNewAttribute() {
    const name = prompt('Nome del nuovo attributo:');
    if (!name) return;
    
    this._hass.callService('ha_clipboards', 'create_attribute', { name });
  }

  _setActiveAttribute(name) {
    this._hass.callService('ha_clipboards', 'set_active', { name });
  }

  _saveText() {
    const textarea = this.shadowRoot.querySelector('#clipboard-text');
    if (textarea) {
      this._hass.callService('ha_clipboards', 'save_text', { text: textarea.value });
    }
  }

  _deleteAttribute(name) {
    if (confirm(`Eliminare l'attributo "${name}"?`)) {
      this._hass.callService('ha_clipboards', 'delete_attribute', { name });
    }
  }

  render() {
    if (!this._hass) {
      this.shadowRoot.innerHTML = '<div class="loading">Caricamento...</div>';
      return;
    }

    const attributeNames = this._getAttributeNames();
    const activeText = this._activeAttribute ? this._attributes[this._activeAttribute] || '' : '';
    const hasActive = this._activeAttribute !== null && this._activeAttribute !== undefined;

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          font-family: var(--ha-card-font-family, 'Roboto', sans-serif);
        }
        .card {
          padding: 16px;
          background: var(--ha-card-background, #fff);
          border-radius: var(--ha-card-border-radius, 12px);
          box-shadow: var(--ha-card-box-shadow, 0 2px 4px rgba(0,0,0,0.1));
        }
        .header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
        }
        .title {
          font-size: 18px;
          font-weight: 500;
          color: var(--primary-text-color, #212121);
        }
        .btn {
          padding: 8px 16px;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-size: 14px;
          font-weight: 500;
          transition: background-color 0.2s;
        }
        .btn-primary {
          background: var(--primary-color, #1976d2);
          color: white;
        }
        .btn-primary:hover {
          background: var(--primary-dark-color, #1565c0);
        }
        .btn-secondary {
          background: var(--secondary-background-color, #f5f5f5);
          color: var(--primary-text-color, #212121);
        }
        .btn-secondary:hover {
          background: var(--secondary-background-color, #e0e0e0);
        }
        .btn-danger {
          background: #f44336;
          color: white;
          padding: 4px 8px;
          font-size: 12px;
        }
        .btn-danger:hover {
          background: #d32f2f;
        }
        .attributes-list {
          margin-bottom: 16px;
        }
        .attributes-list label {
          display: block;
          margin-bottom: 8px;
          font-weight: 500;
          color: var(--primary-text-color, #212121);
        }
        .attribute-select {
          width: 100%;
          padding: 10px 12px;
          border: 1px solid var(--divider-color, #e0e0e0);
          border-radius: 4px;
          font-size: 14px;
          background: var(--card-background-color, #fff);
          color: var(--primary-text-color, #212121);
        }
        .attribute-select:focus {
          outline: none;
          border-color: var(--primary-color, #1976d2);
          box-shadow: 0 0 0 2px rgba(25, 118, 210, 0.2);
        }
        .attribute-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 8px 12px;
          background: var(--secondary-background-color, #f5f5f5);
          border-radius: 4px;
          margin-bottom: 4px;
        }
        .attribute-item.active {
          background: var(--primary-light-color, #e3f2fd);
          border: 1px solid var(--primary-color, #1976d2);
        }
        .attribute-name {
          font-weight: 500;
        }
        .attribute-actions {
          display: flex;
          gap: 8px;
        }
        .text-area-container {
          margin-bottom: 16px;
        }
        .text-area-container label {
          display: block;
          margin-bottom: 8px;
          font-weight: 500;
          color: var(--primary-text-color, #212121);
        }
        #clipboard-text {
          width: 100%;
          min-height: 200px;
          padding: 12px;
          border: 1px solid var(--divider-color, #e0e0e0);
          border-radius: 4px;
          font-family: 'Monospace', monospace;
          font-size: 14px;
          line-height: 1.5;
          background: var(--card-background-color, #fff);
          color: var(--primary-text-color, #212121);
          resize: vertical;
          box-sizing: border-box;
        }
        #clipboard-text:focus {
          outline: none;
          border-color: var(--primary-color, #1976d2);
          box-shadow: 0 0 0 2px rgba(25, 118, 210, 0.2);
        }
        #clipboard-text:disabled {
          background: var(--disabled-background-color, #f5f5f5);
          color: var(--disabled-text-color, #9e9e9e);
        }
        .save-btn {
          width: 100%;
          padding: 12px;
          font-size: 16px;
        }
        .empty-state {
          text-align: center;
          padding: 32px;
          color: var(--secondary-text-color, #757575);
        }
        .attribute-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }
      </style>
      <ha-card class="card">
        <div class="header">
          <div class="title">📋 HA Clipboards</div>
          <button class="btn btn-primary" id="create-attr-btn">+ Nuovo Attributo</button>
        </div>

        <div class="attributes-list">
          <div class="attribute-header">
            <label>Attributi (${attributeNames.length})</label>
            ${hasActive ? `<span class="attribute-name">Attivo: <strong>${this._activeAttribute}</strong></span>` : ''}
          </div>
          
          ${attributeNames.length === 0 ? `
            <div class="empty-state">
              Nessun attributo creato. Clicca "Nuovo Attributo" per iniziare.
            </div>
          ` : `
            <select class="attribute-select" id="attribute-select">
              ${attributeNames.map(name => `
                <option value="${name}" ${name === this._activeAttribute ? 'selected' : ''}>
                  ${name} ${name === this._activeAttribute ? '✓' : ''}
                </option>
              `).join('')}
            </select>
            
            <div class="attribute-list-items">
              ${attributeNames.map(name => `
                <div class="attribute-item ${name === this._activeAttribute ? 'active' : ''}" data-name="${name}">
                  <span class="attribute-name">${name}</span>
                  <div class="attribute-actions">
                    ${name !== this._activeAttribute ? `
                      <button class="btn btn-secondary set-active-btn" data-name="${name}">
                        Attiva
                      </button>
                    ` : ''}
                    <button class="btn btn-danger delete-btn" data-name="${name}">
                      Elimina
                    </button>
                  </div>
                </div>
              `).join('')}
            </div>
          `}
        </div>

        <div class="text-area-container">
          <label>Contenuto: ${hasActive ? this._activeAttribute : 'Nessun attributo attivo'}</label>
          <textarea 
            id="clipboard-text" 
            ${!hasActive ? 'disabled' : ''} 
            placeholder="${hasActive ? 'Scrivi qui il tuo testo...' : 'Crea o seleziona un attributo per iniziare'}"
          >${activeText}</textarea>
        </div>

        <button class="btn btn-primary save-btn" id="save-btn" ${!hasActive ? 'disabled' : ''}>
          💾 Salva
        </button>
      </ha-card>
    `;

    // Add event listeners after rendering
    this._attachEventListeners();
  }

  _attachEventListeners() {
    // Create attribute button
    const createBtn = this.shadowRoot.querySelector('#create-attr-btn');
    if (createBtn) {
      createBtn.addEventListener('click', () => this._createNewAttribute());
    }

    // Save button
    const saveBtn = this.shadowRoot.querySelector('#save-btn');
    if (saveBtn) {
      saveBtn.addEventListener('click', () => this._saveText());
    }

    // Attribute select dropdown
    const select = this.shadowRoot.querySelector('#attribute-select');
    if (select) {
      select.addEventListener('change', (e) => this._setActiveAttribute(e.target.value));
    }

    // Set active buttons
    this.shadowRoot.querySelectorAll('.set-active-btn').forEach(btn => {
      btn.addEventListener('click', (e) => this._setActiveAttribute(e.target.dataset.name));
    });

    // Delete buttons
    this.shadowRoot.querySelectorAll('.delete-btn').forEach(btn => {
      btn.addEventListener('click', (e) => this._deleteAttribute(e.target.dataset.name));
    });
  }

  getCardSize() {
    return 10;
  }
}

customElements.define('ha-clipboards-card', HaClipboardsCard);