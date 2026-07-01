# File: yaml_generator/generate_fancoil_climates.py
# MODIFIED to remove Pyscript persistence and use only trigger-based templates
import os
import re
import yaml
import logging
from datetime import datetime

# CONFIGURATION
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(SCRIPT_DIR, "templates")
LOGGING_FILE = os.path.join(SCRIPT_DIR, "generator.log")
CONFIG_PATH = os.path.join(SCRIPT_DIR, "fancoil_vars.yaml")
GENERATOR_NAME = "yaml_generator/generate_fancoil_climates.py"

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
ROOM_INPUT_SELECT_TEMPLATE_PATH = (
    os.path.join(SCRIPT_DIR, "templates", "fancoil_room_input_selects.j2")
)
ROOM_INPUT_NUMBER_TEMPLATE_PATH = (
    os.path.join(SCRIPT_DIR, "templates", "fancoil_room_input_numbers.j2")
)
MASTER_INPUT_SELECT_TEMPLATE_PATH = (
    os.path.join(SCRIPT_DIR, "templates", "fancoil_master_input_selects.j2")
)
MASTER_INPUT_NUMBER_TEMPLATE_PATH = (
    os.path.join(SCRIPT_DIR, "templates", "fancoil_master_input_numbers.j2")
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
WINDOW_ADVICE_TEMPLATE_PATH = (
    os.path.join(SCRIPT_DIR, "templates", "fancoil_window_advice.j2")
)
WINDOW_NOTIFICATION_TEMPLATE_PATH = (
    os.path.join(SCRIPT_DIR, "templates", "fancoil_window_notification.j2")
)
CLIMATE_ADVICE_TRIGGER_TEMPLATE_PATH = (
    os.path.join(SCRIPT_DIR, "templates", "climate_advice_triggered.j2")
)

# Outputs (generated)
CLIMATE_OUTPUT_DIR = "yaml_generator/generated_climates"
AUTOMATION_OUTPUT_DIR = "automations/fancoil_generated_automations"
SENSORS_OUTPUT_DIR = "yaml_generator/managed_sensors"
TRIGGER_SENSORS_OUTPUT_DIR = "yaml_generator/managed_trigger_sensors"
CLIMATE_COMFORT_PER_ROOM_OUTPUT_FILE = os.path.join(
    SENSORS_OUTPUT_DIR, "climate_comfort_per_room.yaml"
)
BINARY_SENSORS_OUTPUT_DIR = "yaml_generator/managed_binary_sensors"
PERSISTENCE_OUTPUT_DIR = "yaml_generator/managed_persistence"
INPUT_BOOLEAN_OUTPUT_FILE = "yaml_generator/input_boolean/generated_input_booleans.yaml"
INPUT_SELECT_OUTPUT_FILE = "yaml_generator/input_select/generated_input_selects.yaml"
INPUT_NUMBER_OUTPUT_FILE = "yaml_generator/input_number/generated_input_numbers.yaml"
INPUT_DATETIME_OUTPUT_FILE = "yaml_generator/input_datetime/generated_input_datetime.yaml"
INPUT_TEXT_OUTPUT_FILE = "yaml_generator/input_text/generated_input_texts.yaml"
MASTER_CLIMATE_OUTPUT_FILE = (
    "yaml_generator/generated_climates/generated_master_climate.yaml"
)
DASHBOARD_OUTPUT_FILE = "ui/riscaldamento.yaml"
DASHBOARD_BACKUP_FILE = "yaml_generator/generated_dashboards/generated_riscaldamento_dashboard.yaml"


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
            f"sensor.stox_fancoil_{room_id}_temperature"
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
            else:
                local_ctx["TH_COHERENCE_BLOCK_SENSOR"] = ""

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
            else:
                local_ctx["KNX_COHERENCE_BLOCK"] = ""
                local_ctx["KNX_COHERENCE_BLOCK_SENSOR"] = ""
        else:
            local_ctx["TH_COHERENCE_BLOCK"] = ""
            local_ctx["TH_COHERENCE_BLOCK_SENSOR"] = ""
            local_ctx["KNX_COHERENCE_BLOCK"] = ""
            local_ctx["KNX_COHERENCE_BLOCK_SENSOR"] = ""

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
        room_sensor_ids.append(f"'sensor.stox_fancoil_{room_id}'")

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
    master_template_path, room_template_path, output_file, vars_map, extra_context=None
):
    """Write master block then append every room block."""
    logger.info(f"Generating combined master+rooms -> {output_file}")
    master_text = read_template(master_template_path)
    common_master_ctx = get_common_context(master_template_path)
    
    if extra_context:
        master_rendered = substitute_tags(master_text, {**extra_context, **common_master_ctx}).strip()
    else:
        master_rendered = substitute_tags(master_text, common_master_ctx).strip()
    write_text_file(output_file, master_rendered + "\n")

    room_text = read_template(room_template_path)
    common_room_ctx = get_common_context(room_template_path)
    for key, context in vars_map.items():
        # Setup local context
        local_room_ctx = {**context, **common_room_ctx}
        room_id = local_room_ctx.get("id", key)
        
        # Unique options for temp_source
        opts = [
            f"sensor.fancoil_{room_id}_temperature",
            local_room_ctx.get("ref_sensor", ""),
            f"sensor.stox_fancoil_{room_id}_temperature"
        ]
        unique_opts = []
        for o in opts:
            if o and o not in unique_opts:
                unique_opts.append(o)
        
        # Format as YAML list string
        local_room_ctx["TEMP_SOURCE_OPTIONS"] = "[" + ", ".join([f'"{o}"' for o in unique_opts]) + "]"

        append_text_file(
            output_file, substitute_tags(room_text, local_room_ctx).strip() + "\n"
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
        room_subviews.append(substitute_tags(room_details_tpl, {**local_ctx, **common_room_details_ctx}))
        
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

    # Fase 4 - Per-room climate comfort (Omega+attr / T_dew / Comfort / Advice)
    # Generato aggregato da template (climate_comfort_per_room.j2): il blocco per
    # stanza esiste una sola volta, cosi aggiungere una stanza non richiede edit
    # manuali. Generato in climate_comfort_per_room.yaml.
    generate_aggregated(
        CLIMATE_COMFORT_PER_ROOM_TEMPLATE_PATH,
        CLIMATE_COMFORT_PER_ROOM_OUTPUT_FILE,
        vars_map,
    )

    # Fase 5 - Per-room trend sensors (trend umidità)
    generate_from_template(
        TREND_SENSORS_TEMPLATE_PATH,
        SENSORS_OUTPUT_DIR,
        vars_map,
        "_trend",
    )

    # Fase 6 - Per-room window advice sensors (consiglio finestra)
    generate_from_template(
        WINDOW_ADVICE_TEMPLATE_PATH,
        TRIGGER_SENSORS_OUTPUT_DIR,
        vars_map,
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
    generate_from_template(
        WINDOW_NOTIFICATION_TEMPLATE_PATH,
        AUTOMATION_OUTPUT_DIR,
        vars_map,
        "_window_notification",
    )

    # Per-room restore automations
    generate_from_template(
        RESTORE_TEMPLATE_PATH,
        AUTOMATION_OUTPUT_DIR,
        vars_map,
        "_restore",
    )

    # Aggregated helpers
    generate_master_and_rooms(
        MASTER_INPUT_BOOLEAN_TEMPLATE_PATH,
        ROOM_INPUT_BOOLEAN_TEMPLATE_PATH,
        INPUT_BOOLEAN_OUTPUT_FILE,
        vars_map,
        extra_context=None,
    )
    generate_master_and_rooms(
        MASTER_INPUT_SELECT_TEMPLATE_PATH,
        ROOM_INPUT_SELECT_TEMPLATE_PATH,
        INPUT_SELECT_OUTPUT_FILE,
        vars_map,
        extra_context=None,
    )
    generate_master_and_rooms(
        MASTER_INPUT_NUMBER_TEMPLATE_PATH,
        ROOM_INPUT_NUMBER_TEMPLATE_PATH,
        INPUT_NUMBER_OUTPUT_FILE,
        vars_map,
        extra_context=None,
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

    # Generate master include file for Home Assistant
    master_lines = [
        "- sensor: !include_dir_merge_list managed_sensors/",
        "- binary_sensor: !include_dir_merge_list managed_binary_sensors/",
        "- !include ev_charge_2025_triggers.yaml",
        "- !include luce_scale_template.yaml"
    ]
    for key in vars_map.keys():
        master_lines.append(f"- !include managed_trigger_sensors/{key}_climate_advice.yaml")
    for key in vars_map.keys():
        master_lines.append(f"- !include managed_trigger_sensors/{key}_window_advice.yaml")
    for key in vars_map.keys():
        master_lines.append(f"- !include managed_persistence/{key}_persistence.yaml")
    
    # TH Persistence (Tuya sensors)
    master_lines.append("- !include managed_persistence/th_persistence.yaml")
    
    write_text_file("yaml_generator/fancoil_templates_master.yaml", "\n".join(master_lines))

    # Dashboard generation
    generate_dashboard(vars_map)

    logger.info("Generate fancoil files terminated")


if __name__ == "__main__":
    main()
