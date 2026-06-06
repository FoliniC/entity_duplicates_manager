def generate_with_enriched_ctx(template_path, output_dir, vars_map, suffix):
    logger.info(f"Generating enriched files from template: {template_path}")
    template_text = read_template(template_path)
    common_ctx = get_common_context(template_path)
    ensure_dir(output_dir)
    for key, context in vars_map.items():
        # Re-derive context as in the dashboard generator loop
        local_ctx = dict(context)
        room_id = local_ctx.get("id", key)
        friendly_name = local_ctx.get("friendly_name", room_id.replace("_", " ").title())
        local_ctx["friendly_name"] = friendly_name
        local_ctx["id"] = room_id

        # Prepare Coherence Blocks
        th_id = local_ctx.get("th_id", "")
        if th_id:
            local_ctx["TH_COHERENCE_BLOCK"] = f"""- name: "Fancoil {friendly_name} Temp Delta (TH vs Internal)"
  unique_id: fancoil_{room_id}_temp_delta_th_internal
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
  unique_id: fancoil_{room_id}_hum_delta_th_internal
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
            local_ctx["TH_COHERENCE_BLOCK"] = ""

        knx_sensor = local_ctx.get("knx_temp_sensor", "")
        if knx_sensor:
            ref_for_knx = f"sensor.{th_id}_temperature" if th_id else f"sensor.fancoil_{room_id}_temperature"
            local_ctx["KNX_COHERENCE_BLOCK"] = f"""- name: "Fancoil {friendly_name} Temp Delta (KNX vs Ref)"
  unique_id: fancoil_{room_id}_temp_delta_knx_th
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
            local_ctx["KNX_COHERENCE_BLOCK"] = ""

        final_ctx = {**local_ctx, **common_ctx}
        
        # Explicitly substitute tags
        rendered = substitute_tags(template_text, final_ctx)
        
        # Ensure placeholders are removed if not populated
        rendered = rendered.replace("%%TH_COHERENCE_BLOCK%%", local_ctx.get("TH_COHERENCE_BLOCK", ""))
        rendered = rendered.replace("%%KNX_COHERENCE_BLOCK%%", local_ctx.get("KNX_COHERENCE_BLOCK", ""))
        
        rendered = rendered.strip() + "\n"
        out_name = resolve_output_name(context, key, suffix)
        out_path = os.path.join(output_dir, out_name)
        write_text_file(out_path, rendered)
