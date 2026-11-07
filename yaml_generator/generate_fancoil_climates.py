#!/usr/bin/env python3
# Main generator script for fancoil climate control configurations
# Generates Home Assistant automations, sensors, and configurations
# from Jinja2 templates based on room definitions

import os
import re
import yaml
import logging
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

# CONFIGURATION
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(SCRIPT_DIR, "templates")
LOGGING_FILE = os.path.join(SCRIPT_DIR, "generator.log")
CONFIG_PATH = os.path.join(SCRIPT_DIR, "fancoil_vars.yaml")
GENERATOR_NAME = "yaml_generator/generate_fancoil_climates.py"

# Feature flags
GENERATE_RESET_STUCK_SESSION = False

def get_common_context(template_path):
    """Return common metadata for file headers."""
    return {
        "generator_name": GENERATOR_NAME,
        "template_name": os.path.basename(template_path),
        "generation_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

# Templates (input)
CLIMATE_TEMPLATE_PATH = os.path.join(SCRIPT_DIR, "templates", "fancoil_climate.j2")
AUTOMATION_TEMPLATE_PATH = os.path.join(SCRIPT_DIR, "templates", "fancoil_automation.j2")
SENSORS_TEMPLATE_PATH = os.path.join(SCRIPT_DIR, "templates", "fancoil_sensors.j2")
BINARY_SENSORS_TEMPLATE_PATH = os.path.join(SCRIPT_DIR, "templates", "fancoil_binary_sensors.j2")
ROOM_INPUT_BOOLEAN_TEMPLATE_PATH = (
    os.path.join(SCRIPT_DIR, "templates", "fancoil_room_input_booleans.j2")
)
MASTER_INPUT_BOOLEAN_TEMPLATE_PATH = (
    os.path.join(SCRIPT_DIR, "templates", "fancoil_master_input_booleans.j2")
)
ROOM_INPUT_NUMBER_TEMPLATE_PATH = (
    os.path.join(SCRIPT_DIR, "templates", "fancoil_room_input_numbers.j2")
)
MASTER_INPUT_NUMBER_TEMPLATE_PATH = (
    os.path.join(SCRIPT_DIR, "templates", "fancoil_master_input_numbers.j2")
)
MASTER_INPUT_SELECT_TEMPLATE_PATH = (
    os.path.join(SCRIPT_DIR, "templates", "fancoil_master_input_selects.j2")
)
ROOM_INPUT_SELECT_TEMPLATE_PATH = (
    os.path.join(SCRIPT_DIR, "templates", "fancoil_room_input_selects.j2")
)
MASTER_CLIMATE_TEMPLATE_PATH = os.path.join(SCRIPT_DIR, "templates", "fancoil_master_climate.j2")
ROOM_INPUT_DATETIME_TEMPLATE_PATH = (
    os.path.join(SCRIPT_DIR, "templates", "fancoil_room_input_datetime.j2")
)
MASTER_INPUT_DATETIME_TEMPLATE_PATH = (
    os.path.join(SCRIPT_DIR, "templates", "fancoil_master_input_datetime.j2")
)

ROOM_INPUT_TEXT_TEMPLATE_PATH = (
    os.path.join(SCRIPT_DIR, "templates", "fancoil_room_input_text.j2")
)
MASTER_INPUT_TEXT_TEMPLATE_PATH = (
    os.path.join(SCRIPT_DIR, "templates", "fancoil_master_input_text.j2")
)
RESTORE_TEMPLATE_PATH = (
    os.path.join(SCRIPT_DIR, "templates", "fancoil_restore.j2")
)
COHERENCE_TEMPLATE_PATH = (
    os.path.join(SCRIPT_DIR, "templates", "fancoil_coherence.j2")
)
PILOT_SENSORS_TEMPLATE_PATH = (
    os.path.join(SCRIPT_DIR, "templates", "fancoil_pilot_sensors.j2")
)
CLIMATE_COMFORT_PER_ROOM_TEMPLATE_PATH = (
    os.path.join(SCRIPT_DIR, "templates", "climate_comfort_per_room.j2")
)
TREND_SENSORS_TEMPLATE_PATH = (
    os.path.join(SCRIPT_DIR, "templates", "fancoil_trend_sensors.j2")
)
PREDICTION_SENSOR_BLOCK_TEMPLATE_PATH = (
    os.path.join(SCRIPT_DIR, "templates", "fancoil_prediction_sensor_block.j2")
)
PREDICTION_SENSOR_TEMPLATE_PATH = (
    os.path.join(SCRIPT_DIR, "templates", "fancoil_prediction_sensor.j2")
)
WINDOW_ADVICE_TEMPLATE_PATH = (
    os.path.join(SCRIPT_DIR, "templates", "fancoil_window_advice.j2")
)
WINDOW_NOTIFICATION_TEMPLATE_PATH = (
    os.path.join(SCRIPT_DIR, "templates", "fancoil_window_notification.j2")
)
WINDOW_LOGGER_TEMPLATE_PATH = (
    os.path.join(SCRIPT_DIR, "templates", "fancoil_window_logger.j2")
)
WINDOW_EFFICIENCY_TEMPLATE_PATH = (
    os.path.join(SCRIPT_DIR, "templates", "fancoil_window_efficiency.j2")
)
WINDOW_VERIFICATION_MODE_TEMPLATE_PATH = (
    os.path.join(SCRIPT_DIR, "templates", "fancoil_verification_mode.j2")
)
CLIMATE_ADVICE_TRIGGER_TEMPLATE_PATH = (
    os.path.join(SCRIPT_DIR, "templates", "climate_advice_triggered.j2")
)
DASHBOARD_GRAPHS_TEMPLATE_PATH = os.path.join(SCRIPT_DIR, "templates", "dashboard_graphs.j2")
MANUAL_ADVICE_TEMPLATE_PATH = (
    os.path.join(SCRIPT_DIR, "templates", "fancoil_manual_advice.j2")
)

# Nuovi template per Layer 2 fix e debounce
ROOM_INPUT_NUMBER_LAST_VALID_HUMIDITY_TEMPLATE_PATH = (
    os.path.join(SCRIPT_DIR, "templates", "fancoil_room_input_numbers_last_valid_humidity.j2")
)
AUTOMATION_MEMORIZZA_UMIDITA_VALIDA_TEMPLATE_PATH = (
    os.path.join(SCRIPT_DIR, "templates", "fancoil_automation_memorizza_umidita_valida.j2")
)
BINARY_SENSOR_DEBOUNCED_ADVICE_TEMPLATE_PATH = (
    os.path.join(SCRIPT_DIR, "templates", "fancoil_binary_sensor_debounced_advice.j2")
)
AUTOMATION_RESET_STUCK_SESSION_TEMPLATE_PATH = (
    os.path.join(SCRIPT_DIR, "templates", "fancoil_automation_reset_stuck_session.j2")
)

# Window-Fancoil control (stop fan on window open, resume on close)
WINDOW_FANCOIL_CONTROL_TEMPLATE_PATH = (
    os.path.join(SCRIPT_DIR, "templates", "fancoil_window_fancoil_control.j2")
)

# Platform sensors (derivative, etc.) - single file for all rooms
PLATFORM_SENSORS_TEMPLATE_PATH = (
    os.path.join(SCRIPT_DIR, "templates", "fancoil_platform_sensors.j2")
)

# External climate sensors (omega_esterno, T_dew esterno) con filtro outlier
EXTERNAL_CLIMATE_SENSORS_TEMPLATE_PATH = (
    os.path.join(SCRIPT_DIR, "templates", "external_climate_sensors.j2")
)

# Template Select per sorgente temperatura (opzioni dinamiche)
TEMPLATE_SELECT_TEMP_SOURCE_PATH = (
    os.path.join(SCRIPT_DIR, "templates", "fancoil_template_select_temp_source.j2")
)

# Input text per template select temp_source (persistenza scelta)
ROOM_INPUT_TEXT_TEMP_SOURCE_TEMPLATE_PATH = (
    os.path.join(SCRIPT_DIR, "templates", "fancoil_room_input_text_temp_source.j2")
)

# Outputs (generated)
CLIMATE_OUTPUT_DIR = "yaml_generator/generated_climates"
AUTOMATION_OUTPUT_DIR = "automations"
SENSORS_OUTPUT_DIR = "yaml_generator/managed_sensors"
TRIGGER_SENSORS_OUTPUT_DIR = "yaml_generator/managed_trigger_sensors"
CLIMATE_COMFORT_PER_ROOM_OUTPUT_FILE = os.path.join(
    SENSORS_OUTPUT_DIR, "climate_comfort_per_room.yaml"
)
BINARY_SENSORS_OUTPUT_DIR = "yaml_generator/managed_binary_sensors"
PERSISTENCE_OUTPUT_DIR = "yaml_generator/managed_persistence"
INPUT_BOOLEAN_OUTPUT_FILE = "yaml_generator/input_boolean/generated_input_booleans.yaml"
INPUT_NUMBER_OUTPUT_FILE = "yaml_generator/input_number/generated_input_numbers.yaml"
INPUT_DATETIME_OUTPUT_FILE = "yaml_generator/input_datetime/generated_input_datetime.yaml"
INPUT_TEXT_OUTPUT_FILE = "yaml_generator/input_text/generated_input_texts.yaml"
MASTER_CLIMATE_OUTPUT_FILE = (
    "yaml_generator/generated_climates/generated_master_climate.yaml"
)
DASHBOARD_OUTPUT_FILE = "ui/riscaldamento.yaml"
DASHBOARD_BACKUP_FILE = "yaml_generator/generated_dashboards/generated_riscaldamento_dashboard.yaml"
PLATFORM_SENSORS_OUTPUT_FILE = "yaml_generator/platform_sensors.yaml"
# Setup logging
os.makedirs(os.path.dirname(LOGGING_FILE), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)
file_handler = logging.FileHandler(LOGGING_FILE)
file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))
logger.addHandler(file_handler)

def ensure_dir(path: str):
    """Ensure the directory for the given file or directory path exists."""
    if os.path.splitext(path)[1]:
        os.makedirs(os.path.dirname(path), exist_ok=True)
    else:
        os.makedirs(path, exist_ok=True)

def load_fancoil_vars(config_path):
    """Load room variables from YAML."""
    logger.info(f"Loading vars from {config_path}")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
    except Exception as e:
        logger.error(f"Error loading YAML config: {e}")
        raise

    if not isinstance(config, dict):
        raise ValueError("Top-level YAML must be a mapping")

    if "fancoil_vars" in config and isinstance(config["fancoil_vars"], dict):
        vars_map = config["fancoil_vars"]
    else:
        vars_map = config

    for k, v in vars_map.items():
        if not isinstance(v, dict):
            raise ValueError(f"Item '{k}' must be a mapping, got {type(v)}")
        
        # Ensure optional keys exist with default values
        if "knx_temp_sensor" not in v:
            v["knx_temp_sensor"] = ""
        # Fase 4 - humidity pilot fields (optional; default to empty)
        if "humidity_sensor" not in v:
            v["humidity_sensor"] = ""
        if "humidity_fallback_sensors" not in v:
            v["humidity_fallback_sensors"] = []

    logger.info(f"Loaded fancoil_vars data: {vars_map}")
    logger.info("Successfully loaded vars")
    return vars_map

def substitute_tags(template_text: str, context: dict) -> str:
    """Replace every %%key%% with its context value. Signals error if spaces are found."""
    def replace_match(match):
        raw_tag = match.group(0)
        inner = match.group(1)
        key = inner.strip()
        
        if inner != key:
            logger.error(f"Malformed tag found with spaces: '{raw_tag}'. "
                         f"Spaces are NOT allowed inside %%. Use %%{key}%%")
        
        if key in context:
            return str(context[key])
        return raw_tag

    # Regex matching %%any_content%%
    return re.sub(r"%%(.*?)%%", replace_match, template_text)

def resolve_output_name(context: dict, default_key: str, suffix: str) -> str:
    """Use context['filename'] as base name; otherwise default_key. Append suffix and '.yaml'."""
    raw = str(context.get("filename", default_key)).strip()
    raw = os.path.basename(raw)
    base, _ext = os.path.splitext(raw)
    if not base:
        base = default_key
    base = re.sub(r"[^A-Za-z0-9_.-]+", "_", base)
    return f"{base}{suffix}.yaml"

def read_template(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        # Try with latin-1 if utf-8 fails
        try:
            with open(path, "r", encoding="latin-1") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading template file {path}: {e}")
            raise
    except Exception as e:
        logger.error(f"Error reading template file {path}: {e}")
        raise

def clean_yaml_content(text: str) -> str:
    """Remove trailing whitespace from each line."""
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        # Remove trailing whitespace
        line = line.rstrip()
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines)

def write_text_file(path: str, text: str):
    ensure_dir(path)
    try:
        # Clean the content before writing
        cleaned_text = clean_yaml_content(text)
        with open(path, "w", encoding="utf-8", newline="\n") as of:
            of.write(cleaned_text)
        logger.info(f"Wrote {path}")
    except Exception as e:
        logger.error(f"Failed to write {path}: {e}")
        raise

def append_text_file(path: str, text: str):
    ensure_dir(path)
    try:
        # Clean the content before appending
        cleaned_text = clean_yaml_content(text)
        with open(path, "a", encoding="utf-8", newline="\n") as of:
            of.write(cleaned_text)
        logger.info(f"Appended to {path}")
    except Exception as e:
        logger.error(f"Failed appending {path}: {e}")
        raise

def build_delta_sensor_block(name, unique_id, unit, device_class, source_a, source_b):
    """Build a template sensor that reports abs delta and exposes signed/stability attributes."""
    return f"""- name: "{name}"
  unique_id: {unique_id}
  unit_of_measurement: "{unit}"
  state_class: measurement
  device_class: {device_class}
  state: >
    {{% set a = states('{source_a}') | float(none) %}}
    {{% set b = states('{source_b}') | float(none) %}}
    {{% if a is not none and b is not none %}}
      {{{{ ((a - b) | abs) | round(2) }}}}
    {{% else %}}
      unavailable
    {{% endif %}}
  availability: >
    {{{{ is_number(states('{source_a}')) and is_number(states('{source_b}')) }}}}
  attributes:
    source_a: "{source_a}"
    source_b: "{source_b}"
    signed_delta: >
      {{% set a = states('{source_a}') | float(none) %}}
      {{% set b = states('{source_b}') | float(none) %}}
      {{% if a is not none and b is not none %}}
        {{{{ (a - b) | round(3) }}}}
      {{% else %}}
        unknown
      {{% endif %}}
    delta_change: >
      {{% set a = states('{source_a}') | float(none) %}}
      {{% set b = states('{source_b}') | float(none) %}}
      {{% set previous = this.attributes.get('signed_delta') | float(none) %}}
      {{% if a is not none and b is not none and previous is not none %}}
        {{{{ ((a - b) - previous) | abs | round(3) }}}}
      {{% elif a is not none and b is not none %}}
        0
      {{% else %}}
        unknown
      {{% endif %}}"""

def generate_from_template(template_path, output_dir, vars_map, suffix):
    logger.info(f"Generating files from template: {template_path}")
    template_text = read_template(template_path)
    common_ctx = get_common_context(template_path)
    ensure_dir(output_dir)
    for key, context in vars_map.items():
        # Setup local context
        local_ctx = dict(context)
        room_id = local_ctx.get("id", key)
        friendly_name = local_ctx.get("friendly_name", room_id.replace("_", " ").title())
        local_ctx["friendly_name"] = friendly_name
        local_ctx["id"] = room_id

        # Unique options for temp_source
        opts = [
            f"sensor.fancoil_{room_id}_temperature",
            local_ctx.get("ref_sensor", ""),
            local_ctx.get("knx_temp_sensor", ""),
        ]
        unique_opts = []
        for o in opts:
            if o and o not in unique_opts:
                unique_opts.append(o)

        # Format as YAML list string
        local_ctx["TEMP_SOURCE_OPTIONS"] = "[" + ", ".join([f'"{o}"' for o in unique_opts]) + "]"

        if "_coherence" in suffix:
            th_id = local_ctx.get("th_id", "")
            if th_id:
                temp_block = build_delta_sensor_block(
                    f"Fancoil {friendly_name} Temp Delta TH Internal",
                    f"fancoil_{room_id}_temp_delta_th_vs_internal",
                    "°C",
                    "temperature",
                    f"sensor.{th_id}_temperature",
                    f"sensor.fancoil_{room_id}_temperature",
                )
                hum_block = build_delta_sensor_block(
                    f"Fancoil {friendly_name} Hum Delta TH Internal",
                    f"fancoil_{room_id}_hum_delta_th_vs_internal",
                    "%",
                    "humidity",
                    f"sensor.{th_id}_humidity",
                    f"sensor.fancoil_{room_id}_humidity",
                )
                local_ctx["TH_COHERENCE_BLOCK_SENSOR"] = temp_block + "\n\n" + hum_block
                local_ctx["HAS_TH_COHERENCE"] = "true"
            else:
                local_ctx["TH_COHERENCE_BLOCK_SENSOR"] = ""
                local_ctx["HAS_TH_COHERENCE"] = "false"

            knx_sensor = local_ctx.get("knx_temp_sensor", "")
            if knx_sensor:
                ref_for_knx = f"sensor.{th_id}_temperature" if th_id else f"sensor.fancoil_{room_id}_temperature"
                knx_block = build_delta_sensor_block(
                    f"Fancoil {friendly_name} Temp Delta KNX TH",
                    f"fancoil_{room_id}_temp_delta_knx_vs_ref",
                    "°C",
                    "temperature",
                    knx_sensor,
                    ref_for_knx,
                )
                local_ctx["KNX_COHERENCE_BLOCK"] = knx_block
                local_ctx["KNX_COHERENCE_BLOCK_SENSOR"] = knx_block
                local_ctx["HAS_KNX_COHERENCE"] = "true"
            else:
                local_ctx["KNX_COHERENCE_BLOCK"] = ""
                local_ctx["KNX_COHERENCE_BLOCK_SENSOR"] = ""
                local_ctx["HAS_KNX_COHERENCE"] = "false"
        else:
            local_ctx["TH_COHERENCE_BLOCK"] = ""
            local_ctx["TH_COHERENCE_BLOCK_SENSOR"] = ""
            local_ctx["KNX_COHERENCE_BLOCK"] = ""
            local_ctx["KNX_COHERENCE_BLOCK_SENSOR"] = ""

        # Add TH humidity sensor and external humidity sensor for cross-validation
        local_ctx["TH_HUMIDITY_SENSOR"] = local_ctx.get("th_humidity_sensor", "")
        local_ctx["EXTERNAL_HUMIDITY_SENSOR"] = local_ctx.get("external_humidity_sensor", "sensor.meteo_castionetto_umidita")
        # Window contact sensor for stop_condition and window-related logic
        has_win = local_ctx.get("has_window", True)
        local_ctx["has_window"] = has_win
        local_ctx["HAS_WINDOW"] = "true" if has_win else "false"
        window_contact = local_ctx.get("window_contact_sensor", "")
        local_ctx["WINDOW_CONTACT_SENSOR"] = window_contact
        if not has_win:
            local_ctx["WINDOW_STOP_CONDITION_EXPR"] = "false"
        elif window_contact:
            local_ctx["WINDOW_STOP_CONDITION_EXPR"] = f"is_state('{window_contact}', 'on')"
        else:
            local_ctx["WINDOW_STOP_CONDITION_EXPR"] = f"is_state('input_boolean.finestra_{room_id}_aperta', 'on')"
        
        # Render
        final_ctx = {**local_ctx, **common_ctx}
        rendered = substitute_tags(template_text, final_ctx)
        
        # Post-process blocks
        rendered = rendered.replace("%%TH_COHERENCE_BLOCK_SENSOR%%", local_ctx.get("TH_COHERENCE_BLOCK_SENSOR", ""))
        rendered = rendered.replace("%%KNX_COHERENCE_BLOCK_SENSOR%%", local_ctx.get("KNX_COHERENCE_BLOCK_SENSOR", ""))
        rendered = rendered.strip() + "\n"

        out_name = resolve_output_name(context, key, suffix)
        out_path = os.path.join(output_dir, out_name)
        write_text_file(out_path, rendered)

def generate_aggregated(template_path, output_file, vars_map):
    logger.info(f"Generating aggregated from {template_path} -> {output_file}")
    template_text = read_template(template_path)
    common_ctx = get_common_context(template_path)
    pieces = []
    for _, context in vars_map.items():
        local_ctx = {**context, **common_ctx}
        pieces.append(substitute_tags(template_text, local_ctx).strip())
    result = "\n".join(pieces).strip() + "\n"
    write_text_file(output_file, result)

def generate_single(template_path, output_file, context):
    """Render a template once with the given context (no per-room iteration) using Jinja2."""
    logger.info(f"Generating single file from {template_path} -> {output_file}")
    template_name = os.path.basename(template_path)
    template = _jinja_env.get_template(template_name)
    common_ctx = get_common_context(template_path)
    final_ctx = {**context, **common_ctx}
    rendered = template.render(**final_ctx)
    write_text_file(output_file, rendered)

def build_humidity_fallback_context(room_data):
    """Fase 4 - Build Jinja-ready strings for the humidity pilot/fallback template tags.

    Produces:
      HUMIDITY_PRIMARY          -> 'sensor.xxx'
      HUMIDITY_FALLBACK_LIST_JINJA -> ["sensor.a", "sensor.b"]   (valid Jinja literal list)
      HUMIDITY_AVAIL_JINJA       -> has_value('primary') or has_value('fb1') or ...
    """
    primary = str(room_data.get("humidity_sensor", "")).strip()
    fallback = room_data.get("humidity_fallback_sensors") or []
    if isinstance(fallback, str):
        fallback = [fallback]
    fallback = [str(s).strip() for s in fallback if str(s).strip()]

    if not primary:
        logger.warning(
            "Room '%s' has no humidity_sensor defined; pilot will be unavailable.",
            room_data.get("id", "?"),
        )

    def _quote(ent):
        return f"'{ent}'"

    fallback_list = "[" + ", ".join(_quote(s) for s in fallback) + "]"

    all_sensors = [primary] + fallback if primary else fallback
    avail_parts = [f"has_value({ _quote(s) })" for s in all_sensors]
    avail_expr = " or ".join(avail_parts) if avail_parts else "false"

    return {
        "HUMIDITY_PRIMARY": primary,
        "HUMIDITY_FALLBACK_LIST_JINJA": fallback_list,
        "HUMIDITY_AVAIL_JINJA": avail_expr,
    }

def build_master_context(vars_map):
    """Build dynamic context for master climate."""
    sensors_exprs = [
        f"states('sensor.stox_fancoil_{ctx['id']}_temperature') | float(0)"
        for ctx in vars_map.values()
    ]
    sensors_list = ", ".join(sensors_exprs) if sensors_exprs else ""

    # Build rooms array for master climate
    rooms_array = []
    climate_entities_list = []
    room_sensor_ids = []
    for ctx in vars_map.values():
        room_id = ctx["id"]
        rooms_array.append(
            f"{{'id': '{room_id}', "
            f"'climate': 'climate.controllo_temperatura_{room_id}', "
            f"'follow': 'input_boolean.fancoil_{room_id}_hvac_mode_follow_master'}}"
        )
        climate_entities_list.append(f"'climate.controllo_temperatura_{room_id}'")
        room_sensor_ids.append(f"'sensor.temperatura_{room_id}_reale_calcolata'")

    rooms_array_str = "[" + ", ".join(rooms_array) + "]"
    climate_entities_list_str = "[" + ", ".join(climate_entities_list) + "]"
    room_sensors_list_str = "[" + ", ".join(room_sensor_ids) + "]"

    return {
        "sensors_list": sensors_list,
        "rooms_array": rooms_array_str,
        "climate_entities_list": climate_entities_list_str,
        "room_sensors_list": room_sensors_list_str,
    }

def generate_master_and_rooms(
    master_template_path, room_template_path, output_file, vars_map, extra_context=None, append_mode=False
):
    """Write master block then append every room block."""
    logger.info(f"Generating combined master+rooms -> {output_file}")
    master_text = read_template(master_template_path)
    common_master_ctx = get_common_context(master_template_path)

    if extra_context:
        master_rendered = substitute_tags(master_text, {**extra_context, **common_master_ctx}).strip()
    else:
        master_rendered = substitute_tags(master_text, common_master_ctx).strip()

    if append_mode:
        append_text_file(output_file, master_rendered + "\n")
    else:
        write_text_file(output_file, master_rendered + "\n")

    if room_template_path is None:
        return

    room_text = read_template(room_template_path)
    common_room_ctx = get_common_context(room_template_path)
    # First pass: substitute_tags for %%...%% placeholders
    # Then use Jinja2 for conditionals
    for key, context in vars_map.items():
        # Setup local context
        local_room_ctx = {**context, **common_room_ctx}
        room_id = local_room_ctx.get("id", key)
        
        # Unique options for temp_source
        opts = [
            f"sensor.fancoil_{room_id}_temperature",
            local_room_ctx.get("ref_sensor", ""),
            local_room_ctx.get("knx_temp_sensor", ""),
        ]
        unique_opts = []
        for o in opts:
            if o and o not in unique_opts:
                unique_opts.append(o)
        
        # Format as YAML list string
        local_room_ctx["TEMP_SOURCE_OPTIONS"] = "[" + ", ".join([f'"{o}"' for o in unique_opts]) + "]"

        # First pass: substitute %%...%% tags
        rendered = substitute_tags(room_text, local_room_ctx)
        # Second pass: Jinja2 render for conditionals
        room_template = _jinja_env.from_string(rendered)
        rendered = room_template.render(**local_room_ctx)
        
        append_text_file(
            output_file, rendered.strip() + "\n"
        )

# ------------------------ DASHBOARD GENERATION ------------------------
def generate_dashboard(vars_map):
    """Generates the full dashboard YAML."""
    logger.info("Generating dashboard")
    
    main_tpl_path = os.path.join(SCRIPT_DIR, "templates", "dashboard_main.j2")
    termostati_tpl_path = os.path.join(SCRIPT_DIR, "templates", "dashboard_termostati_card.j2")
    impostazioni_tpl_path = os.path.join(SCRIPT_DIR, "templates", "dashboard_impostazioni_card.j2")
    room_details_tpl_path = os.path.join(SCRIPT_DIR, "templates", "dashboard_room_details.j2")
    coherence_tpl_path = os.path.join(SCRIPT_DIR, "templates", "dashboard_coherence_card.j2")
    coherence_temp_tpl_path = os.path.join(SCRIPT_DIR, "templates", "dashboard_coherence_temp_card.j2")
    coherence_hum_tpl_path = os.path.join(SCRIPT_DIR, "templates", "dashboard_coherence_hum_card.j2")

    main_tpl = read_template(main_tpl_path)
    termostati_tpl = read_template(termostati_tpl_path)
    impostazioni_tpl = read_template(impostazioni_tpl_path)
    room_details_tpl = read_template(room_details_tpl_path)
    coherence_tpl = read_template(coherence_tpl_path)
    coherence_temp_tpl = read_template(coherence_temp_tpl_path)
    coherence_hum_tpl = read_template(coherence_hum_tpl_path)

    common_main_ctx = get_common_context(main_tpl_path)
    common_termostati_ctx = get_common_context(termostati_tpl_path)
    common_impostazioni_ctx = get_common_context(impostazioni_tpl_path)
    common_room_details_ctx = get_common_context(room_details_tpl_path)
    common_coherence_ctx = get_common_context(coherence_tpl_path)

    termostati_cards = []
    impostazioni_cards = []
    room_subviews = []
    coherence_cards = []

    for key, context in vars_map.items():
        # Ensure friendly_name is available
        local_ctx = dict(context)
        room_id = local_ctx.get("id", key)
        friendly_name = local_ctx.get("friendly_name", room_id.replace("_", " ").title())
        local_ctx["friendly_name"] = friendly_name
        local_ctx["id"] = room_id

# Prepare Coherence Blocks (Sensor definitions only)
        th_id = local_ctx.get("th_id", "")
        if th_id:
            local_ctx["TH_COHERENCE_BLOCK_SENSOR"] = f"""- name: "Fancoil {friendly_name} Temp Delta (TH vs Internal)"
  unique_id: fancoil_{room_id}_temp_delta_th_vs_internal
  unit_of_measurement: "°C"
  state_class: measurement
  device_class: temperature
  state: >
    {{% set s1 = states('sensor.{th_id}_temperature') | float(None) %}}
    {{% set s2 = states('sensor.fancoil_{room_id}_temperature') | float(None) %}}
    {{% if s1 is not none and s2 is not none %}}
      {{{{ (s1 - s2) | abs | round(2) }}}}
    {{% else %}}
      unavailable
    {{% endif %}}

- name: "Fancoil {friendly_name} Hum Delta (TH vs Internal)"
  unique_id: fancoil_{room_id}_hum_delta_th_vs_internal
  unit_of_measurement: "%"
  state_class: measurement
  device_class: humidity
  state: >
    {{% set s1 = states('sensor.{th_id}_humidity') | float(None) %}}
    {{% set s2 = states('sensor.fancoil_{room_id}_humidity') | float(None) %}}
    {{% if s1 is not none and s2 is not none %}}
      {{{{ (s1 - s2) | abs | round(2) }}}}
    {{% else %}}
      unavailable
    {{% endif %}}"""
        else:
            local_ctx["TH_COHERENCE_BLOCK_SENSOR"] = ""

        knx_sensor = local_ctx.get("knx_temp_sensor", "")
        if knx_sensor:
            ref_for_knx = f"sensor.{th_id}_temperature" if th_id else f"sensor.fancoil_{room_id}_temperature"
            local_ctx["KNX_COHERENCE_BLOCK_SENSOR"] = f"""- name: "Fancoil {friendly_name} Temp Delta (KNX vs Ref)"
  unique_id: fancoil_{room_id}_temp_delta_knx_vs_ref
  unit_of_measurement: "°C"
  state_class: measurement
  device_class: temperature
  state: >
    {{% set s1 = states('{knx_sensor}') | float(None) %}}
    {{% set s2 = states('{ref_for_knx}') | float(None) %}}
    {{% if s1 is not none and s2 is not none %}}
      {{{{ (s1 - s2) | abs | round(2) }}}}
    {{% else %}}
      unavailable
    {{% endif %}}"""
        else:
            local_ctx["KNX_COHERENCE_BLOCK_SENSOR"] = ""

        termostati_cards.append(substitute_tags(termostati_tpl, {**local_ctx, **common_termostati_ctx}))
        impostazioni_cards.append(substitute_tags(impostazioni_tpl, {**local_ctx, **common_impostazioni_ctx}))
        
        # Two-pass rendering for room details: first substitute_tags, then Jinja2 for conditionals
        room_rendered = substitute_tags(room_details_tpl, {**local_ctx, **common_room_details_ctx})
        room_template = _jinja_env.from_string(room_rendered)
        room_subviews.append(room_template.render(**{**local_ctx, **common_room_details_ctx}))
        
        # We need two separate passes for coherence because they belong to different domains
        # We'll use coherence_cards for dashboard, and generate two separate files for HA
        coherence_cards.append(substitute_tags(coherence_tpl, {**local_ctx, **common_coherence_ctx}))
        
    coherence_cards_temp = []
    coherence_cards_hum = []
    with open(os.path.join(TEMPLATE_DIR, "dashboard_coherence_temp_card.j2"), "r") as f:
        coherence_temp_tpl = f.read()
    with open(os.path.join(TEMPLATE_DIR, "dashboard_coherence_hum_card.j2"), "r") as f:
        coherence_hum_tpl = f.read()

    for room_id, room_data in vars_map.items():
        local_ctx = {**room_data}
        if local_ctx.get("th_id") or local_ctx.get("knx_temp_sensor"):
            coherence_cards_temp.append(substitute_tags(coherence_temp_tpl, {**local_ctx, **common_coherence_ctx}))
        if local_ctx.get("th_id"):
            coherence_cards_hum.append(substitute_tags(coherence_hum_tpl, {**local_ctx, **common_coherence_ctx}))

    # Join the cards with the correct indentation
    termostati_section = "\n".join(termostati_cards)
    impostazioni_section = "\n".join(impostazioni_cards)
    room_subviews_section = "\n".join(room_subviews)
    coherence_temp_section = "\n".join(coherence_cards_temp)
    coherence_hum_section = "\n".join(coherence_cards_hum)
    
    # Substitute the placeholders in the main template
    final_dashboard = substitute_tags(main_tpl, common_main_ctx)
    final_dashboard = final_dashboard.replace("%%TERMOSTATI_CARDS%%", termostati_section)
    final_dashboard = final_dashboard.replace("%%IMPOSTAZIONI_CARDS%%", impostazioni_section)
    final_dashboard = final_dashboard.replace("%%ROOM_SUBVIEWS%%", room_subviews_section)
    final_dashboard = final_dashboard.replace("%%COHERENCE_CARDS_TEMP%%", coherence_temp_section)
    final_dashboard = final_dashboard.replace("%%COHERENCE_CARDS_HUM%%", coherence_hum_section)

    write_text_file(DASHBOARD_OUTPUT_FILE, final_dashboard)
    write_text_file(DASHBOARD_BACKUP_FILE, final_dashboard)
    logger.info(f"Dashboard written to {DASHBOARD_OUTPUT_FILE} and {DASHBOARD_BACKUP_FILE}")


# Create Jinja2 environment for graph template
_jinja_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=False)


def generate_graph_views(vars_map):
    """Generates the graph subviews for each room using Jinja2."""
    logger.info("Generating graph views")
    
    graphs_tpl = _jinja_env.get_template("dashboard_graphs.j2")
    graphs_external_tpl = _jinja_env.get_template("dashboard_graphs_external.j2")
    
    graph_views = []
    
    for key, context in vars_map.items():
        # Ensure friendly_name is available
        local_ctx = dict(context)
        room_id = local_ctx.get("id", key)
        friendly_name = local_ctx.get("friendly_name", room_id.replace("_", " ").title())
        local_ctx["friendly_name"] = friendly_name
        local_ctx["id"] = room_id
        
        # Render with Jinja2
        rendered = graphs_tpl.render(**local_ctx)
        
        # Apply substitute_tags to handle %%key%% placeholders
        common_graphs_ctx = get_common_context("dashboard_graphs.j2")
        rendered = substitute_tags(rendered, common_graphs_ctx)
        
        graph_views.append(rendered)
    
    # Add external conditions graph view
    common_external_ctx = get_common_context("dashboard_graphs_external.j2")
    external_rendered = graphs_external_tpl.render()
    external_rendered = substitute_tags(external_rendered, common_external_ctx)
    graph_views.append(external_rendered)
    
    graph_views_section = "\n".join(graph_views)
    
    # Append graph views to the dashboard file
    append_text_file(DASHBOARD_OUTPUT_FILE, graph_views_section + "\n")
    append_text_file(DASHBOARD_BACKUP_FILE, graph_views_section + "\n")
    logger.info(f"Graph views written to {DASHBOARD_OUTPUT_FILE} and {DASHBOARD_BACKUP_FILE}")


def main():
    logger.info("Generate fancoil files started")
    # Ensure working directory is the homeassistant config directory so relative paths resolve correctly
    os.chdir(os.path.dirname(SCRIPT_DIR))
    vars_map = load_fancoil_vars(CONFIG_PATH)

    # Enrich vars_map with derived fields
    for room_id, room_data in vars_map.items():
        ref_sensor = room_data.get("ref_sensor", "")
        th_id = ""
        if ref_sensor and "sensor.th" in ref_sensor:
            match = re.search(r"sensor\.(th[0-9][a-z])", ref_sensor)
            if match:
                th_id = match.group(1)
        room_data["th_id"] = th_id

    # Per-room climate
    generate_from_template(CLIMATE_TEMPLATE_PATH, CLIMATE_OUTPUT_DIR, vars_map, "")

    # Per-room HVAC mode sync automation
    generate_from_template(
        "yaml_generator/templates/fancoil_hvac_mode_sync.j2",
        AUTOMATION_OUTPUT_DIR,
        vars_map,
        "_hvac_mode_sync",
    )

    # Per-room automations
    generate_from_template(
        AUTOMATION_TEMPLATE_PATH, AUTOMATION_OUTPUT_DIR, vars_map, "_automation"
    )

    # Per-room sensors
    generate_from_template(
        SENSORS_TEMPLATE_PATH, SENSORS_OUTPUT_DIR, vars_map, "_sensors"
    )

    # Per-room binary sensors
    generate_from_template(
        BINARY_SENSORS_TEMPLATE_PATH,
        BINARY_SENSORS_OUTPUT_DIR,
        vars_map,
        "_binary_sensors",
    )

    # Fase 4 - Per-room pilot sensors (umidita + temperatura pilota)
    pilot_ctx_map = {}
    for room_id, room_data in vars_map.items():
        pilot_ctx_map[room_id] = {**room_data, **build_humidity_fallback_context(room_data)}
    generate_from_template(
        PILOT_SENSORS_TEMPLATE_PATH,
        SENSORS_OUTPUT_DIR,
        pilot_ctx_map,
        "_pilot",
    )

    # External omega sensor (omega_esterno) - per-room omega sensors come from climate_comfort_per_room.j2
    external_ctx = {"external": {"id": "external", "friendly_name": "Esterno", "filename": "external_climate"}}
    generate_from_template(
        "yaml_generator/templates/fancoil_omega_external_sensor.j2",
        SENSORS_OUTPUT_DIR,
        external_ctx,
        "",
    )

    # Fase 4 - Per-room climate comfort (Omega+attr / T_dew / Comfort / Advice)
    # Generato aggregato da template (climate_comfort_per_room.j2): il blocco per
    # stanza esiste una sola volta, cosi aggiungere una stanza non richiede edit
    # manuali. Generato in climate_comfort_per_room.yaml.
    generate_aggregated(
        CLIMATE_COMFORT_PER_ROOM_TEMPLATE_PATH,
        CLIMATE_COMFORT_PER_ROOM_OUTPUT_FILE,
        vars_map,
    )

    # Trigger-based prediction sensors (per room, modern template format)
    for key, context in vars_map.items():
        local_ctx = {**context, **get_common_context(PREDICTION_SENSOR_TEMPLATE_PATH)}
        template_text = read_template(PREDICTION_SENSOR_TEMPLATE_PATH)
        rendered = substitute_tags(template_text, local_ctx).strip()
        out_name = resolve_output_name(context, key, "_prediction")
        out_path = os.path.join(TRIGGER_SENSORS_OUTPUT_DIR, out_name)
        write_text_file(out_path, rendered + "\n")

    # Fase 5 - Per-room trend sensors (trend umidità)
    generate_from_template(
        TREND_SENSORS_TEMPLATE_PATH,
        SENSORS_OUTPUT_DIR,
        vars_map,
        "_trend",
    )

    # Fase 6 - Per-room window advice sensors (consiglio finestra)
    # Build trigger entities list based on has_window
    window_advice_vars = {}
    for key, context in vars_map.items():
        local_ctx = dict(context)
        room_id = local_ctx.get("id", key)
        has_win = local_ctx.get("has_window", True)
        local_ctx["has_window"] = has_win
        local_ctx["HAS_WINDOW"] = "true" if has_win else "false"
        
        trigger_entities = [
            f"sensor.temperatura_{room_id}_reale_calcolata",
            f"sensor.umidita_{room_id}_pilota",
            f"sensor.omega_{room_id}",
            "sensor.omega_esterno",
            f"sensor.previsione_finestra_{room_id}",
            f"sensor.trend_umidita_{room_id}",
        ]
        if has_win:
            if local_ctx.get("window_contact_sensor"):
                trigger_entities.append(local_ctx["window_contact_sensor"])
            else:
                trigger_entities.append(f"input_boolean.finestra_{room_id}_aperta")
        trigger_entities.append("sensor.castionetto_precipitazione")
        
        local_ctx["TRIGGER_ENTITIES"] = "\n      - " + "\n      - ".join(trigger_entities)
        local_ctx["WINDOW_CONTACT_SENSOR"] = local_ctx.get("window_contact_sensor", "")
        window_advice_vars[key] = local_ctx
    
    generate_from_template(
        WINDOW_ADVICE_TEMPLATE_PATH,
        TRIGGER_SENSORS_OUTPUT_DIR,
        window_advice_vars,
        "_window_advice",
    )

    # Trigger-based climate advice sensors with restored state/attributes.
    generate_from_template(
        CLIMATE_ADVICE_TRIGGER_TEMPLATE_PATH,
        TRIGGER_SENSORS_OUTPUT_DIR,
        vars_map,
        "_climate_advice",
    )

    # Fase 7 - Per-room window notification automations
    # Only generate for rooms with windows
    window_vars_map = {k: v for k, v in vars_map.items() if v.get("has_window", True)}
    generate_from_template(
        WINDOW_NOTIFICATION_TEMPLATE_PATH,
        AUTOMATION_OUTPUT_DIR,
        window_vars_map,
        "_window_notification",
    )

    # Fase 8 - Per-room window logger (logs window state & advice changes)
    window_logger_vars = {}
    for key, context in vars_map.items():
        local_ctx = dict(context)
        room_id = local_ctx.get("id", key)
        has_win = local_ctx.get("has_window", True)
        
        # Build trigger entities for this room
        trigger_entities = [
            f"sensor.consiglio_finestra_{room_id}",
        ]
        if has_win:
            if local_ctx.get("window_contact_sensor"):
                trigger_entities.append(local_ctx["window_contact_sensor"])
            else:
                trigger_entities.append(f"input_boolean.finestra_{room_id}_aperta")
        
        local_ctx["TRIGGER_ENTITIES"] = "\n      - " + "\n      - ".join(trigger_entities)
        local_ctx["window_contact_sensor"] = local_ctx.get("window_contact_sensor", "")
        local_ctx["WINDOW_CONTACT_SENSOR"] = local_ctx.get("window_contact_sensor", "")
        window_logger_vars[key] = local_ctx
    generate_from_template(
        WINDOW_LOGGER_TEMPLATE_PATH,
        TRIGGER_SENSORS_OUTPUT_DIR,
        window_logger_vars,
        "_window_logger",
    )

    # Fase 9 - Per-room window advice efficiency evaluation (valutazione esito consiglio)
    # Build trigger entities based on has_window
    window_efficiency_vars = {}
    for key, context in vars_map.items():
        if not context.get("has_window", True):  # Skip rooms without windows
            continue
        local_ctx = dict(context)
        room_id = local_ctx.get("id", key)
        has_win = local_ctx.get("has_window", True)
        local_ctx["has_window"] = has_win
        local_ctx["HAS_WINDOW"] = "true" if has_win else "false"
        
        # Add TH humidity sensor and external humidity sensor for cross-validation (used in window_efficiency template)
        local_ctx["TH_HUMIDITY_SENSOR"] = local_ctx.get("th_humidity_sensor", "")
        local_ctx["EXTERNAL_HUMIDITY_SENSOR"] = local_ctx.get("external_humidity_sensor", "sensor.meteo_castionetto_umidita")
        
        # Build trigger YAML for this room
        triggers = [
            {"platform": "state", "entity_id": f"sensor.consiglio_finestra_{room_id}", "id": "advice_changed"},
        ]
        if has_win:
            if local_ctx.get("window_contact_sensor"):
                triggers.append({"platform": "state", "entity_id": local_ctx["window_contact_sensor"], "id": "window_changed"})
            triggers.append({"platform": "state", "entity_id": f"input_boolean.finestra_{room_id}_aperta", "id": "window_changed"})
        triggers.append({"platform": "time_pattern", "minutes": "/1", "id": "time_tick"})
        
        # Convert triggers to YAML string
        trigger_yaml = "\n".join(
            f"  - platform: {t['platform']}"
            + (f"\n    entity_id: {t['entity_id']}" if 'entity_id' in t else "")
            + (f"\n    minutes: {t['minutes']}" if 'minutes' in t else "")
            + f"\n    id: {t['id']}"
            for t in triggers
        )
        local_ctx["TRIGGERS_YAML"] = trigger_yaml
        local_ctx["WINDOW_CONTACT_SENSOR"] = local_ctx.get("window_contact_sensor", "")
        
        window_efficiency_vars[key] = local_ctx
    
    generate_from_template(
        WINDOW_EFFICIENCY_TEMPLATE_PATH,
        TRIGGER_SENSORS_OUTPUT_DIR,
        window_efficiency_vars,
        "_window_efficiency",
    )

    # Per-room restore automations (REMOVED - template select handles dynamic options natively)
    # generate_from_template(
    #     RESTORE_TEMPLATE_PATH,
    #     AUTOMATION_OUTPUT_DIR,
    #     vars_map,
    #     "_restore",
    # )

    # Fase 13 - Per-room verification mode logging automations (only for rooms with windows)
    for key, context in vars_map.items():
        if context.get("has_window", True):  # Default true, only skip if explicitly false
            local_ctx = dict(context)
            room_id = local_ctx.get("id", key)
            has_win = local_ctx.get("has_window", True)
            
            # Build trigger entities for this room
            trigger_entities = []
            if has_win:
                if local_ctx.get("window_contact_sensor"):
                    trigger_entities.append(local_ctx["window_contact_sensor"])
                else:
                    trigger_entities.append(f"input_boolean.finestra_{room_id}_aperta")
            
            local_ctx["WINDOW_CONTACT_SENSOR"] = local_ctx.get("window_contact_sensor", "")
            local_ctx["WINDOW_TRIGGER_ENTITY"] = trigger_entities[0] if trigger_entities else ""
            generate_from_template(
                WINDOW_VERIFICATION_MODE_TEMPLATE_PATH,
                AUTOMATION_OUTPUT_DIR,
                {key: local_ctx},
                "_verification",
            )

    # Fase 13 - Manual advice sensors
    generate_from_template(
        MANUAL_ADVICE_TEMPLATE_PATH,
        TRIGGER_SENSORS_OUTPUT_DIR,
        vars_map,
        "_manual_advice",
    )

    # Window-Fancoil control: stop fan on window open, resume on close (for all rooms with windows)
    import uuid as uuid_module
    window_control_vars = {k: v for k, v in vars_map.items() if v.get("has_window", True)}
    for key, context in window_control_vars.items():
        local_ctx = dict(context)
        room_id = local_ctx.get("id", key)
        window_contact = local_ctx.get("window_contact_sensor", "")
        local_ctx["WINDOW_CONTACT_SENSOR"] = window_contact

        # Generate deterministic UUIDs for this room's automations (consistent across runs)
        uuid_seed = f"wcfs_{room_id}".encode()
        uuid_hash = uuid_module.uuid5(uuid_module.NAMESPACE_DNS, uuid_seed.hex())
        short_uuid = uuid_hash.hex[:8]
        local_ctx["WCFS_OPEN_ID"] = f"wcfs_{room_id}_open_{short_uuid}"
        local_ctx["WCFS_CLOSE_ID"] = f"wcfs_{room_id}_close_{short_uuid}"

        if window_contact:
            local_ctx["WINDOW_OPEN_TRIGGERS"] = f"""    - trigger: state
      entity_id: {window_contact}
      to: "on"
      for: "00:00:10"
    - trigger: state
      entity_id: input_boolean.finestra_{room_id}_aperta
      to: "on"
      for: "00:00:05" """
            local_ctx["WINDOW_CLOSE_TRIGGERS"] = f"""    - trigger: state
      entity_id: {window_contact}
      to: "off"
      for: "00:00:05"
    - trigger: state
      entity_id: {window_contact}
      to: "unavailable"
      for: "00:05:00"
    - trigger: state
      entity_id: input_boolean.finestra_{room_id}_aperta
      to: "off"
      for: "00:00:05" """
            local_ctx["WINDOW_CLOSED_CHECK"] = f"""(states('input_boolean.finestra_{room_id}_aperta') != 'on' and states('{window_contact}') != 'on')"""
            local_ctx["WINDOW_CONTACT_STATE_VAR"] = f"""states('{window_contact}')"""
            local_ctx["SYNC_TO_INPUT_BOOLEAN"] = f"""    # Sincronizza input_boolean su ON se aperto da sensore fisico
    - if:
        - condition: template
          value_template: "{{{{ is_state('input_boolean.finestra_{room_id}_aperta', 'off') and is_state('{window_contact}', 'on') }}}}"
      then:
        - action: input_boolean.turn_on
          target:
            entity_id: input_boolean.finestra_{room_id}_aperta"""
        else:
            local_ctx["WINDOW_OPEN_TRIGGERS"] = f"""    - trigger: state
      entity_id: input_boolean.finestra_{room_id}_aperta
      to: "on"
      for: "00:00:05" """
            local_ctx["WINDOW_CLOSE_TRIGGERS"] = f"""    - trigger: state
      entity_id: input_boolean.finestra_{room_id}_aperta
      to: "off"
      for: "00:00:05" """
            local_ctx["WINDOW_CLOSED_CHECK"] = f"""(states('input_boolean.finestra_{room_id}_aperta') != 'on')"""
            local_ctx["WINDOW_CONTACT_STATE_VAR"] = "'off'"
            local_ctx["SYNC_TO_INPUT_BOOLEAN"] = ""

        generate_from_template(
            WINDOW_FANCOIL_CONTROL_TEMPLATE_PATH,
            AUTOMATION_OUTPUT_DIR,
            {key: local_ctx},
            "_window_fancoil_control",
        )

    # Filter rooms with windows for new templates (exclude corridoio)
    vars_map_with_windows = {k: v for k, v in vars_map.items() if v.get("has_window", True)}

    # Nuovi: Input Number helper per ultima umidità valida (Layer 2 fix)
    generate_from_template(
        ROOM_INPUT_NUMBER_LAST_VALID_HUMIDITY_TEMPLATE_PATH,
        "yaml_generator/input_number",
        vars_map_with_windows,
        "_last_valid_humidity",
    )

    # Nuovi: Automazione memorizza ultima umidità valida (Layer 2 fix)
    generate_from_template(
        AUTOMATION_MEMORIZZA_UMIDITA_VALIDA_TEMPLATE_PATH,
        AUTOMATION_OUTPUT_DIR,
        vars_map_with_windows,
        "_memorizza_umidita_valida",
    )

    # Nuovi: Binary Sensor debounced per consiglio finestra
    generate_from_template(
        BINARY_SENSOR_DEBOUNCED_ADVICE_TEMPLATE_PATH,
        BINARY_SENSORS_OUTPUT_DIR,
        vars_map_with_windows,
        "_debounced_advice",
    )

    # Nuovi: Automazione reset sessioni bloccate (Layer 2 fix)
    if GENERATE_RESET_STUCK_SESSION:
        generate_from_template(
            AUTOMATION_RESET_STUCK_SESSION_TEMPLATE_PATH,
            AUTOMATION_OUTPUT_DIR,
            vars_map_with_windows,
            "_reset_stuck_session",
        )

    # Aggregated helpers
    # Input booleans - use all rooms; template handles window_contact_sensor condition
    generate_master_and_rooms(
        MASTER_INPUT_BOOLEAN_TEMPLATE_PATH,
        ROOM_INPUT_BOOLEAN_TEMPLATE_PATH,
        INPUT_BOOLEAN_OUTPUT_FILE,
        vars_map,
        extra_context=None,
    )
    # Template Select per sorgente temperatura (opzioni dinamiche - sostituisce input_select)
    # Pre-compute static options list for each room (evaluated at generation time)
    for key, context in vars_map.items():
        local_ctx = dict(context)
        room_id = local_ctx.get("id", key)
        ref_sensor = local_ctx.get("ref_sensor", "")
        knx_temp_sensor = local_ctx.get("knx_temp_sensor", "")
        candidates = [
            f"sensor.fancoil_{room_id}_temperature",
            ref_sensor,
            knx_temp_sensor,
        ]
        unique_opts = []
        for o in candidates:
            if o and o not in unique_opts:
                unique_opts.append(o)
        # Format as YAML list string with quoted elements (for legacy template compatibility)
        context["TEMP_SOURCE_OPTIONS"] = "[" + ", ".join([f'"{o}"' for o in unique_opts]) + "]"
        # Jinja2-formatted list string for template select options (required to be a template string)
        context["TEMP_SOURCE_OPTIONS_JINJA"] = "[" + ", ".join([f"'{o}'" for o in unique_opts]) + "]"
        # First option for default state
        context["TEMP_SOURCE_FIRST_OPTION"] = unique_opts[0] if unique_opts else f"sensor.fancoil_{room_id}_temperature"

    generate_from_template(
        TEMPLATE_SELECT_TEMP_SOURCE_PATH,
        "yaml_generator/managed_selects",
        vars_map,
        "_template_select_temp_source",
    )
    generate_master_and_rooms(
        MASTER_INPUT_NUMBER_TEMPLATE_PATH,
        ROOM_INPUT_NUMBER_TEMPLATE_PATH,
        INPUT_NUMBER_OUTPUT_FILE,
        vars_map,
        extra_context=None,
    )
    # Master operating mode and thermal profile.
    generate_master_and_rooms(
        MASTER_INPUT_SELECT_TEMPLATE_PATH,
        None,
        "yaml_generator/input_select/generated_master_input_selects.yaml",
        {},
        extra_context=None,
    )
    # Room HVAC mode local (follow_master off)
    generate_aggregated(
        ROOM_INPUT_SELECT_TEMPLATE_PATH,
        "yaml_generator/input_select/generated_room_input_selects.yaml",
        vars_map,
    )
    generate_master_and_rooms(
        MASTER_INPUT_DATETIME_TEMPLATE_PATH,
        ROOM_INPUT_DATETIME_TEMPLATE_PATH,
        INPUT_DATETIME_OUTPUT_FILE,
        vars_map,
        extra_context=None,
    )
    generate_master_and_rooms(
        MASTER_INPUT_TEXT_TEMPLATE_PATH,
        ROOM_INPUT_TEXT_TEMPLATE_PATH,
        INPUT_TEXT_OUTPUT_FILE,
        vars_map,
        extra_context=None,
    )
    # Input text per template select temp_source (persistenza scelta per stanza)
    generate_master_and_rooms(
        MASTER_INPUT_TEXT_TEMPLATE_PATH,
        ROOM_INPUT_TEXT_TEMP_SOURCE_TEMPLATE_PATH,
        INPUT_TEXT_OUTPUT_FILE,
        vars_map,
        extra_context=None,
        append_mode=True,
    )
    # Window-Fancoil control helpers (input_text per saved speeds + input_datetime per timestamp + input_boolean per flag)
    generate_from_template(
        "yaml_generator/templates/fancoil_window_fancoil_helpers_input_text.j2",
        "yaml_generator/input_text",
        {k: v for k, v in vars_map.items() if v.get("has_window", True)},
        "_window_fancoil_helpers",
    )
    generate_from_template(
        "yaml_generator/templates/fancoil_window_fancoil_helpers_input_datetime.j2",
        "yaml_generator/input_datetime",
        {k: v for k, v in vars_map.items() if v.get("has_window", True)},
        "_window_fancoil_helpers",
    )
    generate_from_template(
        "yaml_generator/templates/fancoil_window_fancoil_helpers_input_boolean.j2",
        "yaml_generator/input_boolean",
        {k: v for k, v in vars_map.items() if v.get("has_window", True)},
        "_window_fancoil_helpers",
    )
    # Master climate (single file)
    master_ctx = build_master_context(vars_map)
    master_template = read_template(MASTER_CLIMATE_TEMPLATE_PATH)
    common_master_ctx = get_common_context(MASTER_CLIMATE_TEMPLATE_PATH)
    write_text_file(
        MASTER_CLIMATE_OUTPUT_FILE,
        substitute_tags(master_template, {**master_ctx, **common_master_ctx}).strip() + "\n",
    )

    # Per-room persistence sensors (trigger-based templates)
    generate_from_template(
        "yaml_generator/templates/fancoil_persistence.j2",
        PERSISTENCE_OUTPUT_DIR,
        vars_map,
        "_persistence",
    )

    # Window advice persistence (save/restore state across HA restarts)
    generate_from_template(
        "yaml_generator/templates/fancoil_window_advice_persistence.j2",
        TRIGGER_SENSORS_OUTPUT_DIR,  # trigger-based, so goes to managed_trigger_sensors
        {k: v for k, v in vars_map.items() if v.get("has_window", True)},
        "_window_advice_persistence",
    )

    # Coherence sensors
    generate_from_template(
        "yaml_generator/templates/fancoil_coherence_sensors.j2",
        SENSORS_OUTPUT_DIR,
        vars_map,
        "_coherence",
    )
    generate_from_template(
        "yaml_generator/templates/fancoil_coherence_binary_sensors.j2",
        BINARY_SENSORS_OUTPUT_DIR,
        vars_map,
        "_coherence_error",
    )

    # Platform sensors (derivative) - single file for all rooms
    # This uses Jinja2 template with loop over vars_map
    logger.info(f"Generating platform sensors -> {PLATFORM_SENSORS_OUTPUT_FILE}")
    platform_template = read_template(PLATFORM_SENSORS_TEMPLATE_PATH)
    common_platform_ctx = get_common_context(PLATFORM_SENSORS_TEMPLATE_PATH)
    platform_template_obj = _jinja_env.from_string(platform_template)
    platform_rendered = platform_template_obj.render(vars_map=vars_map, **common_platform_ctx)
    write_text_file(PLATFORM_SENSORS_OUTPUT_FILE, platform_rendered.strip() + "\n")

    # Generate master include file for Home Assistant
    master_lines = [
        "- sensor: !include_dir_merge_list managed_sensors/",
        "- binary_sensor: !include_dir_merge_list managed_binary_sensors/",
        "- !include ev_charge_2025_triggers.yaml",
        "- !include luce_scale_template.yaml"
    ]
    # Rooms with windows (for window_efficiency)
    window_rooms = [k for k, v in vars_map.items() if v.get("has_window", True)]
    for key in vars_map.keys():
        master_lines.append(f"- !include managed_trigger_sensors/{key}_climate_advice.yaml")
    for key in vars_map.keys():
        master_lines.append(f"- !include managed_trigger_sensors/{key}_window_advice.yaml")
    for key in vars_map.keys():
        master_lines.append(f"- !include managed_trigger_sensors/{key}_window_logger.yaml")
    for key in window_rooms:
        master_lines.append(f"- !include managed_trigger_sensors/{key}_window_efficiency.yaml")
    for key in window_rooms:
        master_lines.append(f"- !include managed_trigger_sensors/{key}_window_advice_persistence.yaml")
    for key in vars_map.keys():
        master_lines.append(f"- !include managed_persistence/{key}_persistence.yaml")
    
    # TH Persistence (Tuya sensors)
    master_lines.append("- !include managed_persistence/th_persistence.yaml")
    
    # Additional persistence files (master, EV, PDC)
    master_lines.append("- !include managed_persistence/master_persistence.yaml")
    master_lines.append("- !include managed_persistence/ev_persistence.yaml")
    master_lines.append("- !include managed_persistence/consumo_netto_pdc_persistence.yaml")
    
    # Prediction sensors (one file per room)
    for key in vars_map.keys():
        master_lines.append(f"- !include managed_trigger_sensors/{key}_prediction.yaml")
    
    # Manual advice sensors (one file per room)
    for key in vars_map.keys():
        master_lines.append(f"- !include managed_trigger_sensors/{key}_manual_advice.yaml")

    # Template Select per sorgente temperatura (one file per room)
    for key in vars_map.keys():
        master_lines.append(f"- !include managed_selects/{key}_template_select_temp_source.yaml")

    # Debounced advice sensors are in managed_binary_sensors/ (legacy format)
    # Already included via binary_sensor: !include_dir_merge_list managed_binary_sensors/

    write_text_file("yaml_generator/fancoil_templates_master.yaml", "\n".join(master_lines))

    # Dashboard generation
    generate_dashboard(vars_map)
    
    # Graph views generation
    generate_graph_views(vars_map)

    logger.info("Generate fancoil files terminated")
if __name__ == "__main__":
    main()