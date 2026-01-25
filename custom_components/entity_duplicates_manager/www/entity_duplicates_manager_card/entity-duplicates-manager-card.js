console.log("Entity Duplicates Manager Card loaded v1.0.8");

class EntityDuplicatesManagerCard extends HTMLElement {
  set hass(hass) {
    this._hass = hass;
    if (!this.content) {
      this.init();
    }
    this.updateContent();
  }

  setConfig(config) {
    this.config = config;
  }

  static getConfigElement() {
    return document.createElement("entity-duplicates-manager-card-editor");
  }

  static getStubConfig() {
    return {
      type: "custom:entity-duplicates-manager-card"
    };
  }

  init() {
    this.innerHTML = `
      <style>
        ha-card {
          padding: 16px;
        }
        .header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
        }
        .duplicate-list {
          max-height: 400px;
          overflow-y: auto;
        }
        .duplicate-item {
          border-bottom: 1px solid var(--divider-color);
          padding: 8px 0;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .secondary {
            color: var(--secondary-text-color);
            font-size: 0.9em;
        }
      </style>
      <ha-card>
        <div class="header">
          <div class="title" style="font-size: 1.2em; font-weight: bold;">Duplicates Manager</div>
          <mwc-button id="scan-btn" raised>Scan</mwc-button>
        </div>
        <div id="status" style="margin-bottom: 8px;"></div>
        <div class="duplicate-list" id="list"></div>
      </ha-card>
    `;

    this.content = this.querySelector("ha-card");
    this.list = this.querySelector("#list");
    this.status = this.querySelector("#status");
    
    this.querySelector("#scan-btn").addEventListener("click", () => {
      this._hass.callService("entity_duplicates_manager", "scan_duplicates");
      this.status.innerText = "Scanning started...";
    });
  }

  updateContent() {
    if (!this._hass) return;
    const sensorId = "sensor.duplicates_found"; 
    const stateObj = this._hass.states[sensorId];
    
    if (!stateObj) {
        this.status.innerText = "Sensor not found (sensor.duplicates_found).";
        return;
    }

    const count = stateObj.state;
    const duplicates = stateObj.attributes.duplicates || [];

    if (this._lastCount === count && this._lastLen === duplicates.length) return;
    this._lastCount = count;
    this._lastLen = duplicates.length;

    this.status.innerText = `Found ${count} duplicates.`;
    this.list.innerHTML = "";
    
    duplicates.forEach(dup => {
        const div = document.createElement("div");
        div.className = "duplicate-item";
        div.innerHTML = `
            <div class="item-info">
                <div><strong>${dup.entity_id}</strong></div>
                <div class="secondary">Matches: ${dup.base_entity}</div>
            </div>
            <div style="display: flex; gap: 4px;">
                <mwc-button class="fix-btn" data-ent="${dup.entity_id}" data-base="${dup.base_entity}">Fix</mwc-button>
                <mwc-button class="del-btn" data-ent="${dup.entity_id}" style="--mdc-theme-primary: var(--error-color);">Del</mwc-button>
            </div>
        `;
        this.list.appendChild(div);
    });

    this.querySelectorAll(".fix-btn").forEach(btn => {
        btn.addEventListener("click", (e) => this.handleFix(e.target.dataset.ent, e.target.dataset.base));
    });
    
    this.querySelectorAll(".del-btn").forEach(btn => {
        btn.addEventListener("click", (e) => this.handleDel(e.target.dataset.ent));
    });
  }

  handleFix(entityId, baseEntity) {
      const newId = prompt("Enter new Entity ID for " + entityId, baseEntity);
      if (newId) {
          this._hass.callService("entity_duplicates_manager", "fix_entity", {
              entity_id: entityId,
              new_entity_id: newId
          });
      }
  }

  handleDel(entityId) {
      if (confirm(`Are you sure you want to delete ${entityId}?`)) {
          this._hass.callService("entity_duplicates_manager", "delete_entity", {
              entity_id: entityId
          });
      }
  }
}

class EntityDuplicatesManagerCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = config;
  }
  set hass(hass) {
    this._hass = hass;
  }
  connectedCallback() {
    this.innerHTML = `<div style="padding: 16px;">This card manages duplicate entities automatically. No configuration needed.</div>`;
  }
}

customElements.define("entity-duplicates-manager-card", EntityDuplicatesManagerCard);
customElements.define("entity-duplicates-manager-card-editor", EntityDuplicatesManagerCardEditor);