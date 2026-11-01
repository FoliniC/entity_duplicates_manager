# Controllo configurazione
## 1. Include del master dei template
- Include a file singolo: 47; a directory: 2
- Include verso file/directory MANCANTI: 0
- File generati in managed_* ma NON inclusi nel master: 0

## 2. Riferimenti a entita' (761 entity_id citati nei file)
- MAI_REGISTRATA: 85, MUTA: 42, OK: 627, UNAVAILABLE: 7 (finestra: ultime 24 h)

**Mai registrate nel recorder (nome sbagliato o entita' mai creata)** (85):

| entita' | ultimo stato | citata in |
|---|---|---|
| automation.blocca_ricarica_temporaneamente | - | yaml_generator/managed_sensors/template_sensors_static.yaml |
| automation.btc_tracker_phone_affordable | - | automations/btc_investment_tracker.yaml |
| automation.btc_tracker_significant_loss | - | automations/btc_investment_tracker.yaml |
| automation.ev_charging_automatic_mode_control | - | yaml_generator/scripts/ev_charging_scripts.yaml |
| automation.ev_charging_manual_mode_control | - | yaml_generator/scripts/ev_charging_scripts.yaml |
| automation.ev_charging_mode_sync | - | yaml_generator/scripts/ev_charging_scripts.yaml |
| automation.ev_charging_scheduled_control | - | yaml_generator/scripts/ev_charging_control_scripts.yaml |
| automation.frigate_cucina_person | - | automations/frigate_cucina_person.yaml |
| automation.frigate_locale_tecnico_person | - | automations/frigate_locale_tecnico_person.yaml |
| automation.trigger | - | yaml_generator/scripts/ev_charging_scripts.yaml |
| automation.turn_off | - | yaml_generator/scripts/ev_charging_control_scripts.yaml, yaml_generator/scripts/ev_charging_scripts.yaml |
| automation.turn_on | - | yaml_generator/scripts/ev_charging_control_scripts.yaml, yaml_generator/scripts/ev_charging_scripts.yaml |
| automation.verifica_e_sistema_connessione_internet_2 | - | automations/generated_automations/automations_not_generated_keep_it.yaml |
| climate.set_fan_mode | - | automations/bagno_automation.yaml, automations/camera_automation.yaml, automations/camera_grande_automation.yaml ... |
| climate.set_hvac_mode | - | automations/bagno_automation.yaml, automations/camera_automation.yaml, automations/camera_grande_automation.yaml ... |
| climate.set_temperature | - | automations/bagno_automation.yaml, automations/camera_automation.yaml, automations/camera_grande_automation.yaml ... |
| climate.turn_off | - | automations/bagno_automation.yaml, automations/camera_automation.yaml, automations/camera_grande_automation.yaml ... |
| cover.open_cover | - | automations/alexa_buongiorno.yaml, automations/alexa_ritorno_a_casa.yaml |
| cover.sonoff_10024024c4 | - | yaml_generator/managed_sensors/template_sensors_static.yaml |
| input_boolean.ev_charging_manual_mode | - | yaml_generator/scripts/ev_charging_scripts.yaml |
| input_boolean.ev_charging_use_cronostar | - | yaml_generator/scripts/ev_charging_scripts.yaml |
| input_boolean.logging_enabled | - | automations/generated_automations/automations_not_generated_keep_it.yaml |
| input_boolean.turn_off | - | automations/alexa_accendi_verifica.yaml, automations/alexa_buongiorno.yaml, automations/alexa_cleanup_block_door.yaml ... |
| input_boolean.turn_on | - | automations/alexa_modalita_entrata.yaml, automations/alexa_modalita_uscita.yaml, automations/alexa_ritorno_a_casa.yaml ... |
| input_button.press | - | yaml_generator/scripts/ev_charging_scripts.yaml |
| input_datetime.set_datetime | - | automations/bagno_automation.yaml, automations/camera_automation.yaml, automations/camera_grande_automation.yaml ... |
| input_number.decrement | - | yaml_generator/generated_dashboards/generated_riscaldamento_dashboard.yaml, yaml_generator/templates/dashboard_room_details.j2 |
| input_number.increment | - | yaml_generator/generated_dashboards/generated_riscaldamento_dashboard.yaml, yaml_generator/templates/dashboard_room_details.j2 |
| input_number.manual_charging_power_kw | - | yaml_generator/scripts/ev_charging_scripts.yaml |
| input_number.set_value | - | automations/bagno_automation.yaml, automations/bagno_memorizza_umidita_valida.yaml, automations/camera_automation.yaml ... |
| input_select.mode | - | packages/usb_tether.yaml |
| input_select.select_option | - | automations/bagno_restore.yaml, automations/camera_grande_restore.yaml, automations/camera_restore.yaml ... |
| input_select.set_options | - | automations/bagno_restore.yaml, automations/camera_grande_restore.yaml, automations/camera_restore.yaml ... |
| input_text.set_value | - | automations/automations.yaml, automations/bagno_restore.yaml, automations/camera_grande_restore.yaml ... |
| light.luce_balcone_switch_1 | - | automations/debug_fancoil_resets.yaml |
| light.luce_scale_switch | - | configuration.yaml, yaml_generator/luce_scale_template.yaml, yaml_generator/templates/luce_scale_light.yaml |
| light.turn_off | - | automations/alexa_modalita_entrata.yaml, automations/alexa_modalita_uscita.yaml, automations/generated_automations/automations_not_generated_keep_it.yaml ... |
| light.turn_on | - | automations/alexa_modalita_uscita.yaml, automations/alexa_ritorno_a_casa.yaml, automations/automations.yaml ... |
| person.attributes | - | automations/generated_automations/log_scale_light_state.yaml, automations/log_luce_balcone_state.yaml, automations/log_luce_scale_state.yaml ... |
| script.turn_on | - | automations/alexa_buongiorno.yaml, automations/alexa_modalita_entrata.yaml, automations/alexa_modalita_uscita.yaml ... |
| sensor.bitcoin_24h_change_pct | - | automations/btc_investment_tracker.yaml |
| sensor.effective_charging_power | - | yaml_generator/scripts/ev_charging_scripts.yaml |
| sensor.fancoil_bagno_hum_delta_th_vs_internal | - | yaml_generator/managed_sensors/bagno_coherence.yaml |
| sensor.fancoil_bagno_temp_delta_th_internal | - | yaml_generator/generated_dashboards/generated_riscaldamento_dashboard.yaml |
| sensor.fancoil_bagno_temp_delta_th_vs_internal | - | yaml_generator/managed_sensors/bagno_coherence.yaml |
| sensor.fancoil_corridoio_hum_delta_th_vs_internal | - | yaml_generator/managed_sensors/corridoio_coherence.yaml |
| sensor.fancoil_corridoio_temp_delta_knx_vs_ref | - | yaml_generator/managed_sensors/corridoio_coherence.yaml |
| sensor.fancoil_corridoio_temp_delta_th_vs_internal | - | yaml_generator/managed_sensors/corridoio_coherence.yaml |
| sensor.fancoil_cucina_temp_delta_knx_th | - | yaml_generator/generated_dashboards/generated_riscaldamento_dashboard.yaml |
| sensor.fancoil_cucina_temp_delta_knx_vs_ref | - | yaml_generator/managed_sensors/cucina_coherence.yaml |
| sensor.fancoil_sala_hum_delta_th_vs_internal | - | yaml_generator/managed_sensors/sala_coherence.yaml |
| sensor.fancoil_sala_temp_delta_th_internal | - | yaml_generator/generated_dashboards/generated_riscaldamento_dashboard.yaml |
| sensor.fancoil_sala_temp_delta_th_vs_internal | - | yaml_generator/managed_sensors/sala_coherence.yaml |
| sensor.locale_tecnico_solarnet_power_battery | - | yaml_generator/managed_sensors/template_sensors_static.yaml |
| sensor.luce_balcone_switch_1_current | - | automations/debug_fancoil_resets.yaml |
| sensor.luce_balcone_switch_1_load_power | - | automations/debug_fancoil_resets.yaml |
| sensor.luce_balcone_switch_1_power | - | automations/debug_fancoil_resets.yaml |
| sensor.luce_balcone_switch_1_voltage | - | automations/debug_fancoil_resets.yaml |
| sensor.phone_current_pct_of_launch | - | packages/btc_investment_tracker.yaml |
| sensor.stanza_th | - | yaml_generator/generated_dashboards/generated_riscaldamento_dashboard.yaml, yaml_generator/templates/dashboard_room_details.j2 |

**Ultimo stato unavailable/unknown** (7):

| entita' | ultimo stato | citata in |
|---|---|---|
| input_button.reset_network_counters | unknown | packages/network_monitoring.yaml |
| input_button.start_scheduled_charging | unknown | yaml_generator/scripts/ev_charging_scripts.yaml |
| sensor.ev_charge_2025_saved_byd_max_discharge_power | unknown | automations/generated_automations/ev_charge_2025_restore.yaml |
| sensor.ev_charge_2025_saved_byd_min_soc | unknown | automations/generated_automations/ev_charge_2025_restore.yaml |
| sensor.ev_charge_2025_saved_grid_max_power | unknown | automations/generated_automations/ev_charge_2025_restore.yaml |
| sensor.ev_charge_2025_saved_manual_power | unknown | automations/generated_automations/ev_charge_2025_restore.yaml |
| sensor.ev_charge_2025_saved_target_soc | unknown | automations/generated_automations/ev_charge_2025_restore.yaml |

**Registrate ma senza aggiornamenti nel periodo** (42):

| entita' | ultimo stato | citata in |
|---|---|---|
| binary_sensor.garage_door_garage_contact_sensor | off | yaml_generator/managed_binary_sensors/garage_binary_sensors.yaml |
| cover.wifi_garage_door_module_door | open | automations/alexa_ritorno_a_casa.yaml |
| input_boolean.finestra_camera_grande_aperta | unavailable | automations/camera_grande_verification.yaml, yaml_generator/managed_trigger_sensors/camera_grande_window_advice.yaml, yaml_generator/managed_trigger_sensors/camera_grande_window_logger.yaml |
| input_text.refresh_ops_log | unavailable | packages/btc_investment_tracker.yaml |
| light.verifica | unavailable | automations/alexa_modalita_uscita.yaml |
| sensor.btc_days_to_phone_estimate | unavailable | automations/btc_investment_tracker.yaml |
| sensor.byd_battery_box_premium_hv_state_of_charge | 34.3 | automations/ev_charge_2025_send_current.yaml, automations/generated_automations/automations_not_generated_keep_it.yaml, automations/generated_automations/ev_charge_2025_automation.yaml ... |
| sensor.cucina_illuminance | 188.0 | automations/alexa_modalita_entrata.yaml, automations/alexa_ritorno_a_casa.yaml |
| sensor.envoy_122134037538_current_power_production | 3410 | automations/generated_automations/automations_not_generated_keep_it.yaml, yaml_generator/managed_sensors/template_sensors_ev_charging.yaml, yaml_generator/managed_sensors/template_sensors_ev_charging_status.yaml ... |
| sensor.fancoil_bagno_status_comunicazione | unavailable | automations/bagno_automation.yaml, yaml_generator/automations/fancoil_generated_automations/bagno_automation.yaml, yaml_generator/generated_dashboards/generated_riscaldamento_dashboard.yaml |
| sensor.fancoil_bagno_temp_delta_knx_vs_ref | unavailable | yaml_generator/generated_dashboards/generated_riscaldamento_dashboard.yaml, yaml_generator/managed_sensors/bagno_coherence.yaml |
| sensor.fancoil_camera_grande_hum_delta_th_vs_internal | unavailable | yaml_generator/generated_dashboards/generated_riscaldamento_dashboard.yaml, yaml_generator/managed_sensors/camera_grande_coherence.yaml |
| sensor.fancoil_camera_grande_status_comunicazione | unavailable | automations/camera_grande_automation.yaml, yaml_generator/automations/fancoil_generated_automations/camera_grande_automation.yaml, yaml_generator/generated_dashboards/generated_riscaldamento_dashboard.yaml |
| sensor.fancoil_camera_grande_temp_delta_knx_vs_ref | unavailable | yaml_generator/generated_dashboards/generated_riscaldamento_dashboard.yaml, yaml_generator/managed_sensors/camera_grande_coherence.yaml |
| sensor.fancoil_camera_grande_temp_delta_th_vs_internal | unavailable | yaml_generator/generated_dashboards/generated_riscaldamento_dashboard.yaml, yaml_generator/managed_sensors/camera_grande_coherence.yaml |
| sensor.fancoil_camera_hum_delta_th_vs_internal | unavailable | yaml_generator/generated_dashboards/generated_riscaldamento_dashboard.yaml, yaml_generator/managed_sensors/camera_coherence.yaml |
| sensor.fancoil_camera_status_comunicazione | unavailable | automations/camera_automation.yaml, yaml_generator/automations/fancoil_generated_automations/camera_automation.yaml, yaml_generator/generated_dashboards/generated_riscaldamento_dashboard.yaml |
| sensor.fancoil_camera_temp_delta_knx_vs_ref | unavailable | yaml_generator/generated_dashboards/generated_riscaldamento_dashboard.yaml, yaml_generator/managed_sensors/camera_coherence.yaml |
| sensor.fancoil_camera_temp_delta_th_vs_internal | unavailable | yaml_generator/generated_dashboards/generated_riscaldamento_dashboard.yaml, yaml_generator/managed_sensors/camera_coherence.yaml |
| sensor.fancoil_corridoio_status_comunicazione | unavailable | automations/corridoio_automation.yaml, yaml_generator/automations/fancoil_generated_automations/corridoio_automation.yaml, yaml_generator/generated_dashboards/generated_riscaldamento_dashboard.yaml |
| sensor.fancoil_cucina_hum_delta_th_vs_internal | unavailable | yaml_generator/generated_dashboards/generated_riscaldamento_dashboard.yaml, yaml_generator/managed_sensors/cucina_coherence.yaml |
| sensor.fancoil_cucina_status_comunicazione | unavailable | automations/cucina_automation.yaml, yaml_generator/automations/fancoil_generated_automations/cucina_automation.yaml, yaml_generator/generated_dashboards/generated_riscaldamento_dashboard.yaml |
| sensor.fancoil_cucina_temp_delta_th_vs_internal | unavailable | yaml_generator/generated_dashboards/generated_riscaldamento_dashboard.yaml, yaml_generator/managed_sensors/cucina_coherence.yaml |
| sensor.fancoil_sala_status_comunicazione | unavailable | automations/sala_automation.yaml, yaml_generator/automations/fancoil_generated_automations/sala_automation.yaml, yaml_generator/generated_dashboards/generated_riscaldamento_dashboard.yaml |
| sensor.fancoil_sala_temp_delta_knx_vs_ref | unavailable | yaml_generator/generated_dashboards/generated_riscaldamento_dashboard.yaml, yaml_generator/managed_sensors/sala_coherence.yaml |
| sensor.folini_carlo_voltage_ac | 238.2008 | automations/ev_charge_2025_send_current.yaml, automations/generated_automations/automations_not_generated_keep_it.yaml, automations/generated_automations/ev_charge_2025_automation.yaml ... |
| sensor.prism_potenza_assorbita | 0 | automations/ev_charge_2025_send_current.yaml, automations/generated_automations/ev_charge_2025_automation.yaml, packages/distacco_rete.yaml ... |
| sensor.smart_meter_ts_100a_1_potenza_reale | -3.7 | automations/ev_charge_2025_send_current.yaml, automations/generated_automations/ev_charge_2025_automation.yaml, yaml_generator/managed_sensors/ev_charge_2025.yaml |
| sensor.solarnet_power_battery | -2132.8931 | automations/generated_automations/automations_not_generated_keep_it.yaml, yaml_generator/managed_sensors/ev_charge_2025.yaml |
| sensor.solarnet_power_battery_charge | 2132.8931 | automations/ev_charge_2025_send_current.yaml, automations/generated_automations/ev_charge_2025_automation.yaml, yaml_generator/managed_sensors/ev_charge_2025.yaml |
| sensor.solarnet_power_battery_discharge | 0 | automations/ev_charge_2025_send_current.yaml, automations/generated_automations/ev_charge_2025_automation.yaml, yaml_generator/managed_sensors/ev_charge_2025.yaml |
| sensor.statistics_temperatura_bagno_variance | unavailable | automations/generated_automations/automations_not_generated_keep_it.yaml |
| sensor.statistics_temperatura_camera_grande_variance | unavailable | automations/generated_automations/automations_not_generated_keep_it.yaml |
| sensor.statistics_temperatura_camera_variance | unavailable | automations/generated_automations/automations_not_generated_keep_it.yaml |
| sensor.statistics_temperatura_cucina_variance | 0.0 | automations/generated_automations/automations_not_generated_keep_it.yaml |
| sensor.statistics_temperatura_sala_variance | unavailable | automations/generated_automations/automations_not_generated_keep_it.yaml |
| sensor.temperatura_corridoio | unavailable | yaml_generator/managed_sensors/corridoio_pilot.yaml |
| sensor.temperatura_cucina | unavailable | yaml_generator/managed_sensors/cucina_pilot.yaml |
| sensor.th1a_temperature_humidity_temperature_last | unavailable | automations/generated_automations/automations_not_generated_keep_it.yaml |
| sensor.wifi_dual_meter_b_new_a_old_power_a | 86.9 | yaml_generator/managed_sensors/template_sensors_static.yaml |
| sensor.wifi_dual_meter_b_new_a_old_power_b | 1022.1 | yaml_generator/managed_sensors/template_sensors_static.yaml |
| switch.presa_luci_natale | unavailable | configuration.yaml |
