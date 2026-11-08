console.log("%c ENTITY DUPLICATES MANAGER %c v1.2.0 ", "color: white; background: #41BDF5; font-weight: 700;", "color: #41BDF5; background: #ffffff; font-weight: 700;");
const TRANSLATIONS = {
  en: {
    title: "Duplicates Manager",
    ready: "Ready.",
    scanning: "Scanning...",
    max_suffix: "Max Suffix:",
    exclusions: "Exclusions:",
    btn_scan: "SCAN",
    btn_all: "ALL",
    btn_none: "NONE",
    btn_exclude: "EXCLUDE",
    btn_delete: "DELETE",
    btn_rename: "RENAME",
    filter_duplicates: "Filter duplicates (use * as wildcard)...",
    filter_attributes: "Filter attributes (use * as wildcard)...",
    entity_details: "Entity Details",
    no_duplicates: "No duplicates found.",
    no_visible: "No visible duplicates.",
    results: "Results",
    no_matches: "No matches found.",
    state: "State",
    use_help: "Use ❓ for details.",
    confirm_delete: "Permanently delete {count} visible selected entities?",
    confirm_exclude: "Exclude {count} visible entities from future scans?",
    confirm_rename: "Restore original ID for {count} entities?",
    rename_error: "None of the visible selected entities can be renamed.",
    matches: "Matches",
    from_states: "Only in states - cannot rename",
    tab_duplicates: "Duplicates",
    tab_rename: "Rename",
    tab_entities: "Entity Manager",
    rename_entity_label: "Entity",
    rename_new_name_label: "New Name",
    rename_new_id_label: "New ID",
    rename_search_btn: "SEARCH ENTITY",
    rename_apply_btn: "RENAME",
    rename_delete_btn: "DELETE",
    rename_searching: "Searching...",
    rename_not_found: "Entity not found",
    rename_found: "Entity found",
    rename_confirm: "Rename {entity_id} to {new_id} with name '{new_name}'?",
    delete_confirm: "Permanently delete {entity_id}?",
    rename_success: "Entity renamed successfully",
    delete_success: "Entity deleted successfully",
    rename_id_auto: "Auto-generate ID from name",
    rename_id_manual: "Manual ID (edited)",
    single_selection: "Select one entity only",
    entities_filter_domain: "Domain Filter",
    entities_filter_search: "Search",
    entities_filter_placeholder: "Filter entities...",
    entities_fetch: "FETCH ENTITIES",
    entities_loading: "Loading entities...",
    entities_no_results: "No entities found.",
    entities_selected: "{count} selected",
    entities_delete_selected: "DELETE SELECTED",
    entities_dry_run: "DRY RUN",
    entities_force: "FORCE ACTIVE",
    entities_confirm_delete: "Delete {count} selected entities?",
    entities_confirm_force: "Force delete active entities? This may cause integrations to recreate them.",
    entities_dry_run_title: "Dry Run Results",
    entities_would_delete: "Would delete:",
    entities_skipped_active: "Skipped (active, use FORCE):",
    entities_rejected: "Rejected (not in last scan or changed):",
    entities_failed: "Failed:",
    entities_results: "Delete Results",
    entities_removed: "Removed:",
    entities_confirm_dry_run: "Run dry-run first to see what would be deleted?",
  },
  it: {
    title: "Gestione Duplicati",
    ready: "Pronto.",
    scanning: "Scansione...",
    max_suffix: "Max Suffisso:",
    exclusions: "Esclusioni:",
    btn_scan: "SCANSIONA",
    btn_all: "TUTTI",
    btn_none: "NESSUNO",
    btn_exclude: "ESCLUDI",
    btn_delete: "ELIMINA",
    btn_rename: "RINOMINA",
    filter_duplicates: "Filtra duplicati (usa * come jolly)...",
    filter_attributes: "Filtra attributi (usa * come jolly)...",
    entity_details: "Dettagli Entità",
    no_duplicates: "Nessun duplicato trovato.",
    no_visible: "Nessun duplicato visibile.",
    results: "Risultati",
    no_matches: "Nessuna corrispondenza.",
    state: "Stato",
    use_help: "Usa ❓ per i dettagli.",
    confirm_delete: "Eliminare permanentemente {count} entità visibili selezionate?",
    confirm_exclude: "Escludere {count} entità visibili dalle scansioni future?",
    confirm_rename: "Ripristinare l'ID originale per {count} entità?",
    rename_error: "Nessuna delle entità visibili selezionate può essere rinominata.",
    matches: "Corrisponde a",
    from_states: "Solo negli states - non rinominabile",
    tab_duplicates: "Gestione Duplicati",
    tab_rename: "Rinomina",
    tab_entities: "Gestore Entità",
    rename_entity_label: "Entità",
    rename_new_name_label: "Nuovo Nome",
    rename_new_id_label: "Nuovo ID",
    rename_search_btn: "CERCA ENTITÀ",
    rename_apply_btn: "RINOMINA",
    rename_delete_btn: "ELIMINA",
    rename_searching: "Ricerca...",
    rename_not_found: "Entità non trovata",
    rename_found: "Entità trovata",
    rename_confirm: "Rinominare {entity_id} in {new_id} con nome '{new_name}'?",
    delete_confirm: "Eliminare permanentemente {entity_id}?",
    rename_success: "Entità rinominata con successo",
    delete_success: "Entità eliminata con successo",
    rename_id_auto: "ID generato automaticamente dal nome",
    rename_id_manual: "ID manuale (modificato)",
    single_selection: "Seleziona una sola entità",
    entities_filter_domain: "Filtro Dominio",
    entities_filter_search: "Ricerca",
    entities_filter_placeholder: "Filtra entità...",
    entities_fetch: "CARICA ENTITÀ",
    entities_loading: "Caricamento entità...",
    entities_no_results: "Nessuna entità trovata.",
    entities_selected: "{count} selezionate",
    entities_delete_selected: "ELIMINA SELEZIONATE",
    entities_dry_run: "SIMULAZIONE",
    entities_force: "FORZA ATTIVE",
    entities_confirm_delete: "Eliminare {count} entità selezionate?",
    entities_confirm_force: "Forzare l'eliminazione di entità attive? Le integrazioni potrebbero ricrearle.",
    entities_dry_run_title: "Risultati Simulazione",
    entities_would_delete: "Eliminerebbe:",
    entities_skipped_active: "Saltate (attive, usa FORZA):",
    entities_rejected: "Rifiutate (non nell'ultima scansione o cambiate):",
    entities_failed: "Fallite:",
    entities_results: "Risultati Eliminazione",
    entities_removed: "Rimosse:",
    entities_confirm_dry_run: "Eseguire prima una simulazione per vedere cosa verrebbe eliminato?",
  }
};

function slugify(text) {
  return text.toLowerCase().trim().replace(/[^\w\s-]/g, '').replace(/[\s_-]+/g, '_').replace(/^-+|-+$/g, '');
}

class EntityDuplicatesManagerCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._selected = new Set();
    this._duplicates = [];
    this._loading = false;
    this._max_suffix = 9;
    this._exclusion_patterns = "";
    this._initialized = false;
    this._infoFilter = "";
    this._listFilter = "";
    this._activeTab = "duplicates";
    this._renameEntityInput = "";
    this._renameNewNameInput = "";
    this._renameNewIdInput = "";
    this._renameNewIdManual = false;
    this._renameSearchResults = null;
    this._renameLoading = false;
    // Entity Manager state
    this._entities = [];
    this._entitiesDomainFilter = "";
    this._entitiesSearchFilter = "";
    this._entitiesLoading = false;
    this._entitiesDryRun = false;
    this._entitiesForce = false;
    this._entitiesLastResult = null;
  }

  _t(key, params = {}) {
    const lang = "it" === this._hass?.language?.split("-")[0] ? "it" : "en";
    let text = TRANSLATIONS[lang][key] || TRANSLATIONS.en[key] || key;
    Object.keys(params).forEach(k => { text = text.replace(`{${k}}`, params[k]); });
    return text;
  }

  static getConfigElement() {
    return document.createElement("entity-duplicates-manager-card-editor");
  }

  static getStubConfig() {
    return { type: "custom:entity-duplicates-manager-card" };
  }

  setConfig(config) {
    this._config = config;
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._eventListenerAdded && hass.connection) {
      hass.connection.subscribeEvents(msg => this._handleScanComplete(msg), "entity_duplicates_manager_scan_complete");
      hass.connection.subscribeEvents(msg => this._handleDeleteComplete(msg), "entity_duplicates_manager_delete_complete");
      hass.connection.subscribeEvents(msg => this._handleEntitiesComplete(msg), "entity_duplicates_manager_entities");
      this._eventListenerAdded = true;
    }
    if (!this._initialized) {
      this._initialized = true;
      this._firstRender();
    }
    this._updateContent();
  }

  _handleScanComplete(msg) {
    const duplicates = msg.data.duplicates || [];
    this._duplicates = duplicates.map(d => ({
      ...d,
      can_rename: d.can_rename !== undefined ? d.can_rename : (d.in_registry !== false && d.base_entity !== d.entity_id),
      base_id: d.base_entity,
      source: d.source || (d.in_registry === false ? "states" : "registry"),
      in_registry: d.in_registry !== false
    }));
    if (msg.data.config) {
      this._max_suffix = msg.data.config.max_suffix;
      this._exclusion_patterns = msg.data.config.exclusion_patterns;
      this._excluded_entities = msg.data.config.excluded_entities || [];
      const sensor = this._hass.states["sensor.entity_duplicates_manager_duplicates_found"] || this._hass.states["sensor.duplicates_found"];
      if (sensor && sensor.attributes && sensor.attributes.excluded_entities) {
        this._excluded_entities = sensor.attributes.excluded_entities;
      }
      const inpMax = this.shadowRoot.getElementById("inpMax");
      const inpExc = this.shadowRoot.getElementById("inpExc");
      if (inpMax) inpMax.value = this._max_suffix;
      if (inpExc) inpExc.value = this._exclusion_patterns;
    }
    this._selected.clear();
    this._loading = false;
    this._updateContent();
  }

  _handleDeleteComplete(msg) {
    this._loading = false;
    this._entitiesLoading = false;
    this._entitiesLastResult = msg.data;
    this._updateContent();
    // Re-scan if we're on duplicates tab
    if (this._activeTab === "duplicates") {
      this._scan();
    }
  }

  _handleEntitiesComplete(msg) {
    this._entities = msg.data.entities || [];
    this._entitiesLoading = false;
    this._updateContent();
  }

  async _scan() {
    this._loading = true;
    this._updateContent();
    try {
      const limit = this._max_suffix === "" ? null : parseInt(this._max_suffix);
      await this._hass.callService("entity_duplicates_manager", "scan_duplicates", { max_suffix: limit, exclusion_patterns: this._exclusion_patterns });
    } catch (err) {
      this._loading = false;
      this._updateContent();
    }
  }

  async _deleteSelected() {
    const filtered = this._getFilteredDuplicates();
    const toDelete = Array.from(this._selected).filter(id => filtered.some(d => d.entity_id === id));
    if (toDelete.length === 0) return;
    if (!confirm(this._t("confirm_delete", { count: toDelete.length }))) return;
    this._loading = true;
    this._updateContent();
    try {
      // Use the secure delete with dry_run=false, force=false for duplicates
      await this._hass.callService("entity_duplicates_manager", "delete_entities", { entity_ids: toDelete, dry_run: false, force: false });
      this._clearFilters();
    } catch (err) {
      this._loading = false;
      this._updateContent();
    }
  }

  async _excludeSelected() {
    const filtered = this._getFilteredDuplicates();
    const toExclude = Array.from(this._selected).filter(id => filtered.some(d => d.entity_id === id));
    if (toExclude.length === 0) return;
    if (!confirm(this._t("confirm_exclude", { count: toExclude.length }))) return;
    this._loading = true;
    this._updateContent();
    try {
      await this._hass.callService("entity_duplicates_manager", "exclude_entities", { entity_ids: toExclude });
      this._clearFilters();
    } catch (err) {
      this._loading = false;
      this._updateContent();
    }
  }

  async _renameSelected() {
    const filtered = this._getFilteredDuplicates();
    const toRename = Array.from(this._selected).filter(id => {
      const item = filtered.find(d => d.entity_id === id);
      return item && item.can_rename;
    });
    if (toRename.length === 0) {
      alert(this._t("rename_error"));
      return;
    }
    if (!confirm(this._t("confirm_rename", { count: toRename.length }))) return;
    this._loading = true;
    this._updateContent();
    try {
      await this._hass.callService("entity_duplicates_manager", "rename_entities_to_base", { entity_ids: toRename });
      this._clearFilters();
    } catch (err) {
      this._loading = false;
      this._updateContent();
    }
  }

  async _fetchEntities() {
    this._entitiesLoading = true;
    this._entitiesLastResult = null;
    this._updateContent();
    try {
      await this._hass.callService("entity_duplicates_manager", "get_entities", { 
        domain: this._entitiesDomainFilter || undefined,
        search: this._entitiesSearchFilter || undefined 
      });
    } catch (err) {
      this._entitiesLoading = false;
      this._updateContent();
    }
  }

  async _deleteEntitiesFromManager() {
    const filtered = this._getFilteredEntities();
    const toDelete = Array.from(this._selected).filter(id => filtered.some(d => d.entity_id === id));
    if (toDelete.length === 0) return;
    
    if (this._entitiesDryRun) {
      // Just do dry run
      this._entitiesLoading = true;
      this._updateContent();
      try {
        await this._hass.callService("entity_duplicates_manager", "delete_entities", { 
          entity_ids: toDelete, 
          dry_run: true, 
          force: this._entitiesForce 
        });
      } catch (err) {
        this._entitiesLoading = false;
        this._updateContent();
      }
      return;
    }

    if (!confirm(this._t("entities_confirm_delete", { count: toDelete.length }))) return;
    
    if (this._entitiesForce && !confirm(this._t("entities_confirm_force"))) return;

    this._entitiesLoading = true;
    this._updateContent();
    try {
      await this._hass.callService("entity_duplicates_manager", "delete_entities", { 
        entity_ids: toDelete, 
        dry_run: false, 
        force: this._entitiesForce 
      });
      this._clearFilters();
    } catch (err) {
      this._entitiesLoading = false;
      this._updateContent();
    }
  }

  _toggleEntity(id) {
    if (this._selected.has(id)) this._selected.delete(id);
    else this._selected.add(id);
    this._updateContent();
  }

  _showInfo(entity_id) {
    this._infoFilter = entity_id;
    this._listFilter = entity_id;
    const listInput = this.shadowRoot.getElementById("listFilterInput");
    const infoInput = this.shadowRoot.getElementById("infoFilterInput");
    if (listInput) listInput.value = entity_id;
    if (infoInput) infoInput.value = entity_id;
    this._updateContent();
  }

  _matchFilter(text, filter) {
    if (!filter) return true;
    const f = filter.toLowerCase();
    const t = text.toLowerCase();
    if (!f.includes("*")) return t.includes(f);
    const regex = "^" + f.replace(/[.*+?^${}()|[\]\\]/g, "\\$&").replace(/%/g, ".*") + "$";
    try { return new RegExp(regex).test(t); } catch { return t.includes(f.replace(/%/g, "")); }
  }

  _clearFilters() {
    this._listFilter = "";
    this._infoFilter = "";
    const listInput = this.shadowRoot.getElementById("listFilterInput");
    if (listInput) listInput.value = "";
    this._updateContent();
  }

  _getFilteredDuplicates() {
    if (!this._listFilter) return this._duplicates;
    return this._duplicates.filter(d => this._matchFilter(d.entity_id, this._listFilter) || (d.friendly_name && this._matchFilter(d.friendly_name, this._listFilter)));
  }

  _getFilteredEntities() {
    let filtered = this._entities;
    if (this._entitiesSearchFilter) {
      const f = this._entitiesSearchFilter.toLowerCase();
      filtered = filtered.filter(e => e.entity_id.toLowerCase().includes(f) || (e.friendly_name && e.friendly_name.toLowerCase().includes(f)));
    }
    return filtered;
  }

  _generateIdFromName(name) {
    if (!this._renameNewIdManual) {
      this._renameNewIdInput = slugify(name);
    }
  }

  _onNewNameInput(e) {
    this._renameNewNameInput = e.target.value;
    this._generateIdFromName(this._renameNewNameInput);
    this._updateContent();
  }

  _onNewIdInput(e) {
    this._renameNewIdInput = e.target.value;
    this._renameNewIdManual = true;
    this._updateContent();
  }

  async _searchEntity() {
    const query = this._renameEntityInput.trim();
    if (!query) return;
    this._renameLoading = true;
    this._renameSearchResults = null;
    this._updateContent();
    try {
      let stateObj = this._hass.states[query];
      if (!stateObj) {
        const allStates = Object.entries(this._hass.states);
        const found = allStates.find(([id, obj]) => obj.attributes?.friendly_name?.toLowerCase() === query.toLowerCase());
        if (found) stateObj = found[1];
      }
      if (stateObj) {
        this._renameSearchResults = {
          entity_id: query,
          friendly_name: stateObj.attributes?.friendly_name || query,
          state: stateObj.state
        };
      } else {
        this._renameSearchResults = { error: this._t("rename_not_found") };
      }
    } catch (err) {
      this._renameSearchResults = { error: err.message };
    }
    this._renameLoading = false;
    this._updateContent();
  }

  async _applyRename() {
    if (!this._renameSearchResults || this._renameSearchResults.error) return;
    const { entity_id } = this._renameSearchResults;
    const newId = this._renameNewIdInput.trim();
    const newName = this._renameNewNameInput.trim();
    if (!newId || !newName) return;
    if (!confirm(this._t("rename_confirm", { entity_id, new_id: newId, new_name: newName }))) return;
    this._loading = true;
    this._updateContent();
    try {
      await this._hass.callService("entity_duplicates_manager", "fix_entity", { entity_id, new_entity_id: newId });
      await this._hass.callService("homeassistant", "set_state", { entity_id: newId, state: this._renameSearchResults.state, attributes: { friendly_name: newName } });
      alert(this._t("rename_success"));
      this._renameEntityInput = "";
      this._renameNewNameInput = "";
      this._renameNewIdInput = "";
      this._renameNewIdManual = false;
      this._renameSearchResults = null;
      this._scan();
    } catch (err) {
      alert("Error: " + err.message);
      this._loading = false;
      this._updateContent();
    }
  }

  async _applyDelete() {
    if (!this._renameSearchResults || this._renameSearchResults.error) return;
    const { entity_id } = this._renameSearchResults;
    if (!confirm(this._t("delete_confirm", { entity_id }))) return;
    this._loading = true;
    this._updateContent();
    try {
      await this._hass.callService("entity_duplicates_manager", "delete_entity", { entity_id });
      alert(this._t("delete_success"));
      this._renameEntityInput = "";
      this._renameNewNameInput = "";
      this._renameNewIdInput = "";
      this._renameNewIdManual = false;
      this._renameSearchResults = null;
      this._scan();
    } catch (err) {
      alert("Error: " + err.message);
      this._loading = false;
      this._updateContent();
    }
  }

  _firstRender() {
    this.shadowRoot.innerHTML = `
      <style>
        ha-card { padding: 16px; display: flex; flex-direction: column; gap: 12px; user-select: text !important; width: 100%; box-sizing: border-box; }
        .header { display: flex; justify-content: space-between; align-items: center; }
        .title { font-weight: bold; font-size: 1.1em; display: flex; align-items: center; gap: 8px; }
        .version { font-size: 0.6em; opacity: 0.5; font-weight: normal; }
        .tabs { display: flex; gap: 4px; border-bottom: 2px solid var(--divider-color); margin-bottom: 12px; }
        .tab { padding: 10px 16px; cursor: pointer; font-weight: 600; font-size: 0.85rem; color: var(--secondary-text-color); border-bottom: 2px solid transparent; margin-bottom: -2px; transition: all 0.2s; }
        .tab.active { color: var(--primary-color); border-bottom-color: var(--primary-color); }
        .tab:hover:not(.active) { color: var(--primary-text-color); }
        .main-layout { display: flex; gap: 12px; flex-wrap: wrap; width: 100%; }
        .list-section { flex: 1; min-width: 300px; display: flex; flex-direction: column; gap: 8px; }
        .info-section { flex: 1; min-width: 300px; background: var(--secondary-background-color); border-radius: 8px; padding: 12px; border: 1px solid var(--divider-color); display: flex; flex-direction: column; }
        .filter-section { background: var(--secondary-background-color); padding: 10px; border-radius: 8px; display: flex; flex-direction: column; gap: 6px; }
        .filter-row { display: flex; gap: 8px; align-items: center; font-size: 0.8rem; }
        .filter-row label { min-width: 120px; }
        .filter-row input { flex: 1; padding: 6px; border-radius: 4px; border: 1px solid var(--divider-color); background: var(--card-background-color); color: var(--primary-text-color); width: 100%; box-sizing: border-box; }
        .filter-row select { flex: 1; padding: 6px; border-radius: 4px; border: 1px solid var(--divider-color); background: var(--card-background-color); color: var(--primary-text-color); }
        .actions { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 8px; }
        .btn { padding: 8px 12px; border-radius: 4px; border: none; cursor: pointer; font-weight: bold; font-size: 0.75rem; transition: opacity 0.2s; }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; }
        .btn-main { background: var(--primary-color); color: white; }
        .btn-outline { background: transparent; border: 1px solid var(--primary-color); color: var(--primary-color); }
        .btn-danger { background: var(--error-color); color: white; }
        .btn-warning { background: #f4b400; color: white; }
        .btn-success { background: #4caf50; color: white; }
        .list-container { flex: 1; max-height: 500px; min-height: 200px; overflow-y: auto; border: 1px solid var(--divider-color); border-radius: 4px; background: var(--card-background-color); }
        .section-header { background: var(--secondary-background-color); padding: 6px 10px; font-weight: bold; font-size: 0.75rem; position: sticky; top: 0; z-index: 2; }
        .item { display: flex; align-items: center; padding: 10px 12px; border-bottom: 1px solid var(--divider-color); cursor: pointer; }
        .item:hover { background: var(--secondary-background-color); }
        .item-content { display: flex; flex-direction: column; flex: 1; overflow: hidden; }
        .item-id { font-family: monospace; font-size: 0.75rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .rename-hint { color: var(--success-color); font-weight: bold; font-size: 0.7rem; font-family: monospace; }
        .source-hint { color: var(--warning-color); font-weight: bold; font-size: 0.7rem; font-family: monospace; }
        .checkbox { margin-right: 8px; width: 16px; height: 16px; flex-shrink: 0; }
        .item-icons { display: flex; gap: 4px; align-items: center; flex-shrink: 0; }
        .help-icon { padding: 4px 8px; cursor: help; color: var(--primary-color); font-size: 1rem; }
        .info-attrs { font-size: 0.75rem; white-space: pre-wrap; background: rgba(0,0,0,0.05); padding: 6px; border-radius: 4px; font-family: monospace; border: 1px solid var(--divider-color); }
        .item.can-rename { border-left: 4px solid var(--success-color); padding-left: 8px; }
        .item.states-only { border-left: 4px solid var(--warning-color); padding-left: 8px; }
        .search-box { padding: 6px; border-radius: 4px; border: 1px solid var(--divider-color); background: var(--card-background-color); color: var(--primary-text-color); width: 100%; box-sizing: border-box; font-size: 0.8rem; }
        .rename-form { display: flex; flex-direction: column; gap: 12px; padding: 8px; }
        .rename-field { display: flex; flex-direction: column; gap: 4px; }
        .rename-field label { font-weight: 600; font-size: 0.8rem; }
        .rename-field input { padding: 8px; border-radius: 4px; border: 1px solid var(--divider-color); background: var(--card-background-color); color: var(--primary-text-color); font-size: 0.85rem; }
        .rename-field input[readonly] { opacity: 0.6; background: var(--secondary-background-color); }
        .rename-hint-text { font-size: 0.7rem; color: var(--secondary-text-color); }
        .rename-results { background: var(--secondary-background-color); border: 1px solid var(--divider-color); border-radius: 8px; padding: 12px; margin-top: 8px; }
        .rename-result-item { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid var(--divider-color); }
        .rename-result-item:last-child { border-bottom: none; }
        .rename-result-label { font-weight: 600; font-family: monospace; font-size: 0.8rem; }
        .rename-result-value { color: var(--secondary-text-color); font-family: monospace; font-size: 0.75rem; }
        .rename-actions { display: flex; gap: 8px; margin-top: 16px; }
        .id-status { font-size: 0.7rem; padding: 2px 6px; border-radius: 3px; }
        .id-status.auto { background: var(--success-color); color: white; }
        .id-status.manual { background: var(--warning-color); color: white; }
        .entities-options { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; margin-top: 8px; padding: 8px; background: var(--secondary-background-color); border-radius: 4px; }
        .entities-options label { display: flex; align-items: center; gap: 4px; font-size: 0.75rem; cursor: pointer; }
        .entities-options input[type=checkbox] { width: 16px; height: 16px; }
        .results-panel { background: var(--secondary-background-color); border: 1px solid var(--divider-color); border-radius: 8px; padding: 12px; margin-top: 12px; font-size: 0.8rem; }
        .results-panel h4 { margin: 0 0 8px 0; }
        .results-panel ul { margin: 0; padding-left: 20px; }
        .results-panel li { margin: 4px 0; font-family: monospace; font-size: 0.75rem; }
        .results-panel .removed { color: var(--error-color); }
        .results-panel .would-delete { color: #f4b400; }
        .results-panel .skipped { color: var(--warning-color); }
        .results-panel .rejected { color: var(--secondary-text-color); }
        .results-panel .failed { color: var(--error-color); }
      </style>
      <ha-card>
        <div class="header">
          <div class="title">🔍 <span id="cardTitle"></span> <span class="version">v1.2.0</span></div>
          <div id="loader"></div>
        </div>

        <div class="tabs" id="tabs">
          <div class="tab" id="tabDuplicates" data-tab="duplicates"></div>
          <div class="tab" id="tabRename" data-tab="rename"></div>
          <div class="tab" id="tabEntities" data-tab="entities"></div>
        </div>

        <div id="tabContent"></div>
      </ha-card>
    `;

    this.shadowRoot.getElementById("tabDuplicates").onclick = () => { this._activeTab = "duplicates"; this._updateContent(); };
    this.shadowRoot.getElementById("tabRename").onclick = () => { this._activeTab = "rename"; this._updateContent(); };
    this.shadowRoot.getElementById("tabEntities").onclick = () => { this._activeTab = "entities"; this._updateContent(); };
  }

  _updateContent() {
    if (!this._initialized) return;

    this.shadowRoot.getElementById("cardTitle").innerText = this._t("title");
    const loader = this.shadowRoot.getElementById("loader");
    if (loader) loader.innerHTML = (this._loading || this._entitiesLoading) ? '<ha-circular-progress active size="small"></ha-circular-progress>' : "";

    const tabDuplicates = this.shadowRoot.getElementById("tabDuplicates");
    const tabRename = this.shadowRoot.getElementById("tabRename");
    const tabEntities = this.shadowRoot.getElementById("tabEntities");
    if (tabDuplicates) {
      tabDuplicates.innerText = this._t("tab_duplicates");
      tabDuplicates.classList.toggle("active", this._activeTab === "duplicates");
    }
    if (tabRename) {
      tabRename.innerText = this._t("tab_rename");
      tabRename.classList.toggle("active", this._activeTab === "rename");
    }
    if (tabEntities) {
      tabEntities.innerText = this._t("tab_entities");
      tabEntities.classList.toggle("active", this._activeTab === "entities");
    }

    const tabContent = this.shadowRoot.getElementById("tabContent");
    if (!tabContent) return;

    if (this._activeTab === "duplicates") {
      tabContent.innerHTML = this._renderDuplicatesTab();
      this._bindDuplicatesTabEvents();
    } else if (this._activeTab === "rename") {
      tabContent.innerHTML = this._renderRenameTab();
      this._bindRenameTabEvents();
    } else {
      tabContent.innerHTML = this._renderEntitiesTab();
      this._bindEntitiesTabEvents();
    }
  }

  _renderDuplicatesTab() {
    const filtered = this._getFilteredDuplicates();
    const selectedVisible = Array.from(this._selected).filter(id => filtered.some(d => d.entity_id === id)).length;
    const selectedCanRename = Array.from(this._selected).filter(id => {
      const item = filtered.find(d => d.entity_id === id);
      return item && item.can_rename;
    }).length;

    return `
      <div class="filter-section">
        <div class="filter-row"><label id="lblMax"></label><input type="number" id="inpMax"></div>
        <div class="filter-row"><label id="lblExc"></label><input type="text" id="inpExc"></div>
      </div>

      <div class="actions" id="actionButtons"></div>

      <div class="main-layout">
        <div class="list-section">
          <input type="text" id="listFilterInput" class="search-box">
          <div class="list-container" id="listContainer"></div>
        </div>
        <div class="info-section">
          <div id="infoTitle" style="font-weight:bold;font-size:0.8rem;margin-bottom:8px"></div>
          <input type="text" id="infoFilterInput" class="search-box" style="margin-bottom:8px">
          <div id="infoContent" style="overflow-y:auto;max-height:450px"></div>
        </div>
      </div>
    `;
  }

  _bindDuplicatesTabEvents() {
    this.shadowRoot.getElementById("listFilterInput")?.addEventListener("input", e => { this._listFilter = e.target.value; this._updateContent(); });
    this.shadowRoot.getElementById("infoFilterInput")?.addEventListener("input", e => { this._infoFilter = e.target.value; this._updateInfoSection(); });
    this.shadowRoot.getElementById("inpMax")?.addEventListener("change", e => { this._max_suffix = e.target.value; });
    this.shadowRoot.getElementById("inpExc")?.addEventListener("change", e => { this._exclusion_patterns = e.target.value; });

    this.shadowRoot.getElementById("lblMax").innerText = this._t("max_suffix");
    this.shadowRoot.getElementById("lblExc").innerText = this._t("exclusions");
    this.shadowRoot.getElementById("infoTitle").innerText = "ℹ️ " + this._t("entity_details");
    this.shadowRoot.getElementById("listFilterInput").placeholder = this._t("filter_duplicates");
    this.shadowRoot.getElementById("infoFilterInput").placeholder = this._t("filter_attributes");

    const filtered = this._getFilteredDuplicates();
    const selectedVisible = Array.from(this._selected).filter(id => filtered.some(d => d.entity_id === id)).length;
    const selectedCanRename = Array.from(this._selected).filter(id => {
      const item = filtered.find(d => d.entity_id === id);
      return item && item.can_rename;
    }).length;

    const actions = this.shadowRoot.getElementById("actionButtons");
    if (actions) {
      actions.innerHTML = `
        <button id="btnScan" class="btn btn-main">${this._t("btn_scan")}</button>
        <button id="btnAll" class="btn btn-outline" ${filtered.length === 0 ? "disabled" : ""}>${this._t("btn_all")}</button>
        <button id="btnNone" class="btn btn-outline" ${selectedVisible === 0 ? "disabled" : ""}>${this._t("btn_none")}</button>
        <button id="btnExc" class="btn btn-warning" ${selectedVisible === 0 ? "disabled" : ""}>${this._t("btn_exclude")} (${selectedVisible})</button>
        <button id="btnDel" class="btn btn-danger" ${selectedVisible === 0 ? "disabled" : ""}>${this._t("btn_delete")} (${selectedVisible})</button>
        ${selectedCanRename > 0 ? `<button id="btnRename" class="btn btn-success">${this._t("btn_rename")} (${selectedCanRename})</button>` : ""}
      `;
      this.shadowRoot.getElementById("btnScan")?.addEventListener("click", () => this._scan());
      this.shadowRoot.getElementById("btnAll")?.addEventListener("click", () => { filtered.forEach(d => this._selected.add(d.entity_id)); this._updateContent(); });
      this.shadowRoot.getElementById("btnNone")?.addEventListener("click", () => { filtered.forEach(d => this._selected.delete(d.entity_id)); this._updateContent(); });
      this.shadowRoot.getElementById("btnDel")?.addEventListener("click", () => this._deleteSelected());
      this.shadowRoot.getElementById("btnExc")?.addEventListener("click", () => this._excludeSelected());
      this.shadowRoot.getElementById("btnRename")?.addEventListener("click", () => this._renameSelected());
    }

    const container = this.shadowRoot.getElementById("listContainer");
    if (container) {
      if (filtered.length === 0) {
        container.innerHTML = `<div style="padding:20px;text-align:center;font-size:0.8rem">${this._duplicates.length === 0 ? this._t("no_duplicates") : this._t("no_visible")}</div>`;
      } else {
        container.innerHTML = `<div class="section-header">📋 ${this._t("results")} (${filtered.length})</div>` + filtered.map(d => this._renderItemHtml(d)).join("");
        container.querySelectorAll(".item").forEach(el => {
          el.onclick = () => this._toggleEntity(el.dataset.id);
          const checkbox = el.querySelector("input");
          checkbox?.addEventListener("click", e => { e.stopPropagation(); this._toggleEntity(el.dataset.id); });
          const help = el.querySelector(".help-icon");
          help?.addEventListener("click", e => { e.stopPropagation(); this._showInfo(el.dataset.id); });
        });
      }
    }
    this._updateInfoSection();
  }

  _renderRenameTab() {
    const hasResults = this._renameSearchResults && !this._renameSearchResults.error;
    const hasError = this._renameSearchResults && this._renameSearchResults.error;
    const idStatusClass = this._renameNewIdManual ? "manual" : "auto";
    const idStatusText = this._renameNewIdManual ? this._t("rename_id_manual") : this._t("rename_id_auto");

    return `
      <div class="rename-form">
        <div class="rename-field">
          <label>${this._t("rename_entity_label")}</label>
          <input type="text" id="renameEntityInput" class="search-box" placeholder="es. switch.luce_bancone_2 o Luce Bancone" value="${this._renameEntityInput}">
          <button id="renameSearchBtn" class="btn btn-main" ${this._renameLoading ? "disabled" : ""} style="margin-top: 8px; align-self: flex-start;">${this._renameLoading ? this._t("rename_searching") : this._t("rename_search_btn")}</button>
        </div>

        ${this._renameSearchResults ? `
          <div class="rename-results">
            ${hasError ? `
              <div style="color: var(--error-color); font-weight: bold;">${this._renameSearchResults.error}</div>
            ` : `
              <div class="rename-result-item"><span class="rename-result-label">${this._t("rename_entity_label")}:</span><span class="rename-result-value">${this._renameSearchResults.entity_id}</span></div>
              <div class="rename-result-item"><span class="rename-result-label">${this._t("state")}:</span><span class="rename-result-value">${this._renameSearchResults.state}</span></div>
            `}
          </div>
        ` : ""}

        ${hasResults ? `
          <div class="rename-field">
            <label>${this._t("rename_new_name_label")}</label>
            <input type="text" id="renameNewNameInput" value="${this._renameNewNameInput}" placeholder="es. Luce Bancone">
          </div>
          <div class="rename-field">
            <label>${this._t("rename_new_id_label")} <span class="id-status ${idStatusClass}">${idStatusText}</span></label>
            <input type="text" id="renameNewIdInput" value="${this._renameNewIdInput}" placeholder="es. switch.luce_bancone">
          </div>
          <div class="rename-actions">
            <button id="renameApplyBtn" class="btn btn-success">${this._t("rename_apply_btn")}</button>
            <button id="renameDeleteBtn" class="btn btn-danger">${this._t("rename_delete_btn")}</button>
          </div>
        ` : ""}

        <div style="font-size: 0.75rem; color: var(--secondary-text-color); padding: 8px; background: var(--secondary-background-color); border-radius: 4px;">
          ${this._t("single_selection")}
        </div>
      </div>
    `;
  }

  _bindRenameTabEvents() {
    const entityInput = this.shadowRoot.getElementById("renameEntityInput");
    const newNameInput = this.shadowRoot.getElementById("renameNewNameInput");
    const newIdInput = this.shadowRoot.getElementById("renameNewIdInput");
    const searchBtn = this.shadowRoot.getElementById("renameSearchBtn");
    const applyBtn = this.shadowRoot.getElementById("renameApplyBtn");
    const deleteBtn = this.shadowRoot.getElementById("renameDeleteBtn");

    if (entityInput) entityInput.addEventListener("input", e => { this._renameEntityInput = e.target.value; });
    if (newNameInput) newNameInput.addEventListener("input", e => this._onNewNameInput(e));
    if (newIdInput) newIdInput.addEventListener("input", e => this._onNewIdInput(e));
    if (searchBtn) searchBtn.addEventListener("click", () => this._searchEntity());
    if (applyBtn) applyBtn.addEventListener("click", () => this._applyRename());
    if (deleteBtn) deleteBtn.addEventListener("click", () => this._applyDelete());
  }

  _renderEntitiesTab() {
    const filtered = this._getFilteredEntities();
    const selectedVisible = Array.from(this._selected).filter(id => filtered.some(d => d.entity_id === id)).length;
    
    const domains = [...new Set(this._entities.map(e => e.domain))].sort();
    const domainOptions = [''].concat(domains).map(d => `<option value="${d}">${d || "All"}</option>`).join('');

    return `
      <div class="filter-section">
        <div class="filter-row"><label>${this._t("entities_filter_domain")}</label><select id="entitiesDomainFilter">${domainOptions}</select></div>
        <div class="filter-row"><label>${this._t("entities_filter_search")}</label><input type="text" id="entitiesSearchFilter" class="search-box" placeholder="${this._t("entities_filter_placeholder")}"></div>
      </div>

      <div class="actions" id="entitiesActions"></div>

      <div class="main-layout">
        <div class="list-section">
          <div class="list-container" id="entitiesListContainer"></div>
        </div>
        <div class="info-section">
          <div id="entitiesInfoTitle" style="font-weight:bold;font-size:0.8rem;margin-bottom:8px">ℹ️ ${this._t("entity_details")}</div>
          <div id="entitiesInfoContent" style="overflow-y:auto;max-height:450px"></div>
        </div>
      </div>

      ${this._entitiesLastResult ? this._renderEntitiesResults() : ""}
    `;
  }

  _renderEntitiesResults() {
    const r = this._entitiesLastResult;
    if (!r) return "";
    
    const isDryRun = r.dry_run === true;
    const title = isDryRun ? this._t("entities_dry_run_title") : this._t("entities_results");
    
    let html = `<div class="results-panel"><h4>${title}</h4>`;
    
    if (r.would_remove && r.would_remove.length > 0) {
      html += `<div class="entities_would_delete"><strong>${this._t("entities_would_delete")}</strong><ul>${r.would_remove.map(e => `<li>${e}</li>`).join('')}</ul></div>`;
    }
    if (r.removed && r.removed.length > 0) {
      html += `<div class="entities_removed"><strong>${this._t("entities_removed")}</strong><ul>${r.removed.map(e => `<li class="removed">${e}</li>`).join('')}</ul></div>`;
    }
    if (r.skipped_active && r.skipped_active.length > 0) {
      html += `<div class="entities_skipped"><strong>${this._t("entities_skipped_active")}</strong><ul>${r.skipped_active.map(e => `<li class="skipped">${e}</li>`).join('')}</ul></div>`;
    }
    if (r.rejected && r.rejected.length > 0) {
      html += `<div class="entities_rejected"><strong>${this._t("entities_rejected")}</strong><ul>${r.rejected.map(e => `<li class="rejected">${e}</li>`).join('')}</ul></div>`;
    }
    if (r.failed && r.failed.length > 0) {
      html += `<div class="entities_failed"><strong>${this._t("entities_failed")}</strong><ul>${r.failed.map(e => `<li class="failed">${e.entity_id}: ${e.error}</li>`).join('')}</ul></div>`;
    }
    
    html += `</div>`;
    return html;
  }

  _bindEntitiesTabEvents() {
    const domainFilter = this.shadowRoot.getElementById("entitiesDomainFilter");
    const searchFilter = this.shadowRoot.getElementById("entitiesSearchFilter");

    if (domainFilter) {
      domainFilter.value = this._entitiesDomainFilter;
      domainFilter.addEventListener("change", e => { 
        this._entitiesDomainFilter = e.target.value; 
        this._updateContent(); 
      });
    }
    if (searchFilter) {
      searchFilter.value = this._entitiesSearchFilter;
      searchFilter.addEventListener("input", e => { 
        this._entitiesSearchFilter = e.target.value; 
        this._updateContent(); 
      });
    }

    const filtered = this._getFilteredEntities();
    const selectedVisible = Array.from(this._selected).filter(id => filtered.some(d => d.entity_id === id)).length;

    const actions = this.shadowRoot.getElementById("entitiesActions");
    if (actions) {
      actions.innerHTML = `
        <button id="btnFetchEntities" class="btn btn-main" ${this._entitiesLoading ? "disabled" : ""}>${this._entitiesLoading ? this._t("entities_loading") : this._t("entities_fetch")}</button>
        <button id="btnEntitiesAll" class="btn btn-outline" ${filtered.length === 0 ? "disabled" : ""}>${this._t("btn_all")}</button>
        <button id="btnEntitiesNone" class="btn btn-outline" ${selectedVisible === 0 ? "disabled" : ""}>${this._t("btn_none")}</button>
        <div class="entities-options">
          <label><input type="checkbox" id="entitiesDryRun" ${this._entitiesDryRun ? "checked" : ""}> ${this._t("entities_dry_run")}</label>
          <label><input type="checkbox" id="entitiesForce" ${this._entitiesForce ? "checked" : ""}> ${this._t("entities_force")}</label>
        </div>
        <button id="btnEntitiesDel" class="btn btn-danger" ${selectedVisible === 0 ? "disabled" : ""}>${this._t("entities_delete_selected")} (${selectedVisible})</button>
      `;

      this.shadowRoot.getElementById("btnFetchEntities")?.addEventListener("click", () => this._fetchEntities());
      this.shadowRoot.getElementById("btnEntitiesAll")?.addEventListener("click", () => { filtered.forEach(d => this._selected.add(d.entity_id)); this._updateContent(); });
      this.shadowRoot.getElementById("btnEntitiesNone")?.addEventListener("click", () => { filtered.forEach(d => this._selected.delete(d.entity_id)); this._updateContent(); });
      this.shadowRoot.getElementById("btnEntitiesDel")?.addEventListener("click", () => this._deleteEntitiesFromManager());
      
      const dryRunCheckbox = this.shadowRoot.getElementById("entitiesDryRun");
      const forceCheckbox = this.shadowRoot.getElementById("entitiesForce");
      if (dryRunCheckbox) dryRunCheckbox.addEventListener("change", e => { this._entitiesDryRun = e.target.checked; this._updateContent(); });
      if (forceCheckbox) forceCheckbox.addEventListener("change", e => { this._entitiesForce = e.target.checked; this._updateContent(); });
    }

    const container = this.shadowRoot.getElementById("entitiesListContainer");
    if (container) {
      if (filtered.length === 0) {
        container.innerHTML = `<div style="padding:20px;text-align:center;font-size:0.8rem">${this._entities.length === 0 ? this._t("entities_no_results") : this._t("no_visible")}</div>`;
      } else {
        container.innerHTML = `<div class="section-header">📋 ${this._t("results")} (${filtered.length}) ${this._t("entities_selected", { count: selectedVisible })}</div>` + filtered.map(d => this._renderEntityItemHtml(d)).join("");
        container.querySelectorAll(".item").forEach(el => {
          el.onclick = () => this._toggleEntity(el.dataset.id);
          const checkbox = el.querySelector("input");
          checkbox?.addEventListener("click", e => { e.stopPropagation(); this._toggleEntity(el.dataset.id); });
          const help = el.querySelector(".help-icon");
          help?.addEventListener("click", e => { e.stopPropagation(); this._showInfo(el.dataset.id); });
        });
      }
    }
    this._updateEntitiesInfoSection();
  }

  _renderEntityItemHtml(item) {
    const checked = this._selected.has(item.entity_id) ? "checked" : "";
    const activeClass = item.is_active ? "active" : "stale";
    const activeLabel = item.is_active ? "● Active" : "○ Stale";
    const activeColor = item.is_active ? "var(--success-color)" : "var(--warning-color)";
    
    return `
      <div class="item ${item.in_registry ? "can-rename" : "states-only"}" data-id="${item.entity_id}" style="border-left-color: ${activeColor};">
        <input type="checkbox" class="checkbox" ${checked}>
        <div class="item-content">
            <div class="item-id" title="${item.entity_id}">${item.entity_id}</div>
            <div style="font-size:0.65rem;color:${activeColor}">${activeLabel} • ${item.domain} • ${item.in_registry ? "Registry" : "States only"}</div>
        </div>
        <div class="item-icons">
            <div class="help-icon" title="Dettagli">❓</div>
        </div>
      </div>
    `;
  }

  _updateEntitiesInfoSection() {
    const content = this.shadowRoot.getElementById("entitiesInfoContent");
    if (content) content.innerHTML = this._renderInfo();
  }

  _updateInfoSection() {
    const content = this.shadowRoot.getElementById("infoContent");
    if (content) content.innerHTML = this._renderInfo();
  }

  _renderItemHtml(item) {
    const checked = this._selected.has(item.entity_id) ? "checked" : "";
    const hint = item.can_rename ? `<div class="rename-hint">➔ ${item.base_id}</div>` : item.in_registry === false ? `<div class="source-hint">${this._t("from_states")}</div>` : "";
    return `
      <div class="item ${item.can_rename ? "can-rename" : item.in_registry === false ? "states-only" : ""}" data-id="${item.entity_id}">
        <input type="checkbox" class="checkbox" ${checked}>
        <div class="item-content">
            <div class="item-id" title="${item.entity_id}">${item.entity_id}</div>
            ${hint}
        </div>
        <div class="item-icons">
            <div class="help-icon" title="Dettagli">❓</div>
        </div>
      </div>
    `;
  }

  _isExcluded(entity_id) {
    if (!this._exclusion_patterns && !this._excluded_entities) return false;
    if (this._excluded_entities && this._excluded_entities.includes(entity_id)) return "excluded_entities";
    if (!this._exclusion_patterns) return false;
    const patterns = this._exclusion_patterns.split(",").map(p => p.trim()).filter(p => p);
    for (const pattern of patterns) if (this._matchPattern(entity_id, pattern)) return pattern;
    return false;
  }

  _matchPattern(text, pattern) {
    if (!pattern.includes("*")) return text === pattern;
    const regex = "^" + pattern.replace(/[.*+?^${}()|[\]\\]/g, "\\$&").replace(/%/g, ".*") + "$";
    try { return new RegExp(regex).test(text); } catch { return false; }
  }

  _renderInfo() {
    if (!this._hass || !this._infoFilter) return `<div style='font-size:0.75rem;text-align:center;padding:10px'>${this._t("use_help")}</div>`;
    const matches = Object.keys(this._hass.states).filter(id => this._matchFilter(id, this._infoFilter)).sort().slice(0, 30);
    if (matches.length === 0) return `<div style='font-size:0.75rem;text-align:center;padding:10px'>${this._t("no_matches")}</div>`;
    return matches.map(entity_id => {
      const stateObj = this._hass.states[entity_id];
      let attrs = "";
      if (stateObj && stateObj.attributes) {
        for (const [k, v] of Object.entries(stateObj.attributes)) {
          attrs += `${k}: ${JSON.stringify(v)}\n`;
        }
      }
      const excluded = this._isExcluded(entity_id);
      attrs += `\nexcluded: ${excluded ? "yes (" + excluded + ")" : "no"}`;
      return `
        <div style="margin-bottom:10px;border-bottom:1px solid var(--divider-color);padding-bottom:5px">
          <div style="font-weight:bold;font-size:0.75rem;color:var(--accent-color)">${entity_id}</div>
          <div style="font-size:0.8rem">${this._t("state")}: ${stateObj ? stateObj.state : "N/A"}</div>
          <div class="info-attrs">${attrs}</div>
        </div>
      `;
    }).join("");
  }
}

class EntityDuplicatesManagerCardEditor extends HTMLElement {
  setConfig(config) { this._config = config; }
  set hass(hass) { this._hass = hass; }
  connectedCallback() {
    this.innerHTML = '<div style="padding: 16px;"><h3>Entity Duplicates Manager</h3><p>Version 1.2.0 - With Entity Manager Tab</p></div>';
  }
}

customElements.define("entity-duplicates-manager-card", EntityDuplicatesManagerCard);
customElements.define("entity-duplicates-manager-card-editor", EntityDuplicatesManagerCardEditor);