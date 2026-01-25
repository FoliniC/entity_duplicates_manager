console.log("Entity Duplicates Manager Card loaded v1.0.5");

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
        .actions {
          display: flex;
          gap: 8px;
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
        .item-info {
          flex-grow: 1;
        }
        .item-actions {
          display: flex;
          gap: 4px;
        }
        .secondary {
            color: var(--secondary-text-color);
            font-size: 0.9em;
        }
      </style>
      <ha-card>
        <div class="header">
          <div class="title">Duplicates Manager</div>
          <div class="actions">
            <mwc-button id="scan-btn" raised>Scan</mwc-button>
          </div>
        </div>
        <div id="status"></div>
        <div class="duplicate-list" id="list">
          <!-- Items will be injected here -->
        </div>
      </ha-card>
    `;

    this.content = this.querySelector(".card-content");
    this.list = this.querySelector("#list");
    this.status = this.querySelector("#status");
    
    this.querySelector("#scan-btn").addEventListener("click", () => {
      this._hass.callService("entity_duplicates_manager", "scan_duplicates");
      this.status.innerText = "Scanning started...";
    });
  }

  updateContent() {
    // Assuming the sensor entity is predictable or configured
    // We try to find it
    const sensorId = "sensor.duplicates_found"; 
    // Note: The unique_id was 'duplicate_count_sensor', but HA generates entity_id from name.
    // Name was "Duplicates Found" -> "sensor.duplicates_found" likely.
    
    const stateObj = this._hass.states[sensorId];
    
    if (!stateObj) {
        this.status.innerText = "Sensor not found (sensor.duplicates_found). Waiting...";
        return;
    }

    const count = stateObj.state;
    const duplicates = stateObj.attributes.duplicates || [];

    this.status.innerText = `Found ${count} duplicates.`;

    // Simple render (in a real LitElement this would be more efficient)
    // Only update if changed (naive check)
    if (this._lastCount === count && this._lastLen === duplicates.length) return;
    this._lastCount = count;
    this._lastLen = duplicates.length;

    this.list.innerHTML = "";
    
    duplicates.forEach(dup => {
        const div = document.createElement("div");
        div.className = "duplicate-item";
        div.innerHTML = `
            <div class="item-info">
                <div><strong>${dup.entity_id}</strong></div>
                <div class="secondary">Matches: ${dup.base_entity}</div>
                <div class="secondary">Integration: ${dup.integration}</div>
            </div>
            <div class="item-actions">
                <mwc-button class="fix-btn" data-ent="${dup.entity_id}" data-base="${dup.base_entity}">Fix</mwc-button>
                <mwc-button class="del-btn" data-ent="${dup.entity_id}">Del</mwc-button>
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
      // Logic to ask user or just do it? 
      // For now, let's assume we rename TO the base entity (merging/replacing?)
      // Or maybe renaming the duplicate to something else?
      // The prompt implied "Fix Entity ID".
      // Let's prompt.
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

customElements.define("entity-duplicates-manager-card", EntityDuplicatesManagerCard);