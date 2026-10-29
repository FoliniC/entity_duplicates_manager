import json
import datetime
import sys
import traceback

# Absolute path for HA docker
LIB_PATH = "/config/pyscript/lib"
if LIB_PATH not in sys.path:
    sys.path.append(LIB_PATH)

try:
    import ev_predictor_lib
except ImportError:
    log.error("EV_PREDICT: Failed to import ev_predictor_lib")

# Entity ID constants to avoid string literal issues
ENT_VEHICLE_LIMIT_SOC = 'input_number.ev_charge_2025_vehicle_limit_soc'
ENT_BATTERY_CAPACITY = 'input_number.ev_charge_2025_battery_capacity'
ENT_CURRENT_SOC = 'sensor.ev_charge_2025_current_soc'
ENT_MODE = 'input_select.ev_charge_2025_mode'
ENT_ACTIVE_PROFILE = 'select.cronostar_ev_current_profile'
ENT_VOLTAGE = 'sensor.prism_tensione_attuale'
ENT_MANUAL_POWER = 'input_number.ev_charge_2025_manual_power_kw'
ENT_POWER_ABSORBED = 'sensor.prism_potenza'
ENT_SOLAR_MAX_AMP = 'sensor.ev_charge_2025_solar_max_ampere'
ENT_CRONOSTAR_TARGET = 'input_number.ev_charge_2025_cronostar_power_target'

@service
def ev_charge_predict_time():
    """Simulates EV charging based on Cronostar schedule and SOC with detailed logging."""
    try:
        # 1. Recupera parametri base
        s_cur_soc = state.get(ENT_CURRENT_SOC)
        s_limit_soc = state.get(ENT_VEHICLE_LIMIT_SOC)
        s_capacity_kwh = state.get(ENT_BATTERY_CAPACITY)
        s_mode = state.get(ENT_MODE)
        s_active_profile = state.get(ENT_ACTIVE_PROFILE)
        # Voltage sensor may not exist, handle gracefully
        try:
            s_voltage = state.get(ENT_VOLTAGE)
        except NameError:
            s_voltage = None
        s_voltage = s_voltage or 230.0

        if s_cur_soc in [None, 'unknown', 'unavailable']: return
        
        cur_soc = float(s_cur_soc)
        limit_soc = float(s_limit_soc or 100)
        capacity_kwh = float(s_capacity_kwh or 55.0)
        voltage = float(s_voltage)
        
        if cur_soc >= limit_soc:
            state.set('sensor.ev_charge_2025_time_to_limit_sim', 0, {'unit_of_measurement': 'min', 'friendly_name': 'EV Charge 2025 Time to Limit'})
            return

        energy_needed_kwh = (limit_soc - cur_soc) / 100.0 * capacity_kwh
        log.info(f"EV_PREDICT: Avvio calcolo. SOC: {cur_soc}%, Target: {limit_soc}%, Serve: {energy_needed_kwh:.2f} kWh")

        # 2. Logica Manuale
        if s_mode == 'Manuale':
            try:
                manual_kw = float(state.get(ENT_MANUAL_POWER) or 2.0)
            except NameError:
                manual_kw = 2.0
            try:
                power_w = float(state.get(ENT_POWER_ABSORBED) or 0.0)
            except NameError:
                power_w = 0.0
            calc_kw = max(manual_kw, power_w / 1000.0)
            if calc_kw < 0.1: calc_kw = 1.4
            total_minutes = int(energy_needed_kwh / calc_kw * 60)
            log.info(f"EV_PREDICT: [Manuale] Potenza: {calc_kw}kW, Tempo: {total_minutes}min")
            state.set('sensor.ev_charge_2025_time_to_limit_sim', total_minutes, {'unit_of_measurement': 'min', 'friendly_name': 'EV Charge 2025 Time to Limit'})
            return

        # 3. Logica Automatica
        try:
            raw_data = task.executor(ev_predictor_lib.read_cronostar_profiles, '/config/cronostar/profiles/cronostar_ev_data.json')
            profiles = raw_data.get('profiles', {})
            
            if s_active_profile in profiles:
                schedule = profiles[s_active_profile].get('schedule', [])
                if schedule:
                    points = []
                    for p in schedule:
                        h, m = map(int, p['time'].split(':'))
                        val = float(p['value'])
                        
                        # LOGICA CRONOSTAR CORRETTA:
                        # - Valori < 7.5 sono kW reali
                        # - Valori >= 7.5 sono codici (7.9=Solar, 8.0=Max)
                        
                        if val > 7.95:
                             # F3 Max (8.0): 32 Ampere
                             p_kw = 32.0 * voltage / 1000.0
                        elif val >= 7.5:
                            # Solar (7.9): Surplus solare stimato
                            try:
                                solar_amp = float(state.get(ENT_SOLAR_MAX_AMP) or 0)
                            except NameError:
                                solar_amp = 0
                            p_kw = max(solar_amp * voltage / 1000.0, 1.4)
                        else:
                            # Altri: Valore kW nominale
                            p_kw = val
                        
                        points.append({'min': h * 60 + m, 'kw': p_kw})
                    
                    points.sort(key=lambda x: x['min'])

                    now = datetime.datetime.now()
                    current_total_min = now.hour * 60 + now.minute
                    sim_energy = 0.0
                    sim_min = 0
                    last_kw = -1.0
                    
                    while sim_energy < energy_needed_kwh and sim_min < 2880:
                        t_sim = (current_total_min + sim_min) % 1440
                        
                        # Step-function logic
                        current_kw = 0.0
                        if t_sim < points[0]['min']:
                            current_kw = points[-1]['kw']
                        else:
                            for p in points:
                                if t_sim >= p['min']: current_kw = p['kw']
                                else: break
                        # Logging cambi fascia (logga l'intervallo concluso)
                        if current_kw != last_kw:
                            if sim_min > 0:
                                t_start_str = (now + datetime.timedelta(minutes=interval_start_min)).strftime('%H:%M')
                                t_end_str = (now + datetime.timedelta(minutes=sim_min)).strftime('%H:%M')
                                log.info(f"EV_PREDICT: Ore {t_start_str} fino alle {t_end_str} -> {last_kw:.2f}kW. Al termine accumulati: {sim_energy:.2f}/{energy_needed_kwh:.2f} kWh")

                            last_kw = current_kw
                            interval_start_min = sim_min


                        if current_kw > 0.1:
                            sim_energy += (current_kw / 60.0)
                        sim_min += 1

                    log.info(f"EV_PREDICT: [Auto - {s_active_profile}] Fine. Tempo: {sim_min}min ({sim_energy:.2f}kWh)")
                    state.set('sensor.ev_charge_2025_time_to_limit_sim', sim_min, {'unit_of_measurement': 'min', 'friendly_name': 'EV Charge 2025 Time to Limit'})
                    return
        except Exception as e:
            log.error(f"EV_PREDICT SIM ERROR: {e}")

        # Fallback
        try:
            target_kw = float(state.get(ENT_CRONOSTAR_TARGET) or 1.4)
        except NameError:
            target_kw = 1.4
        total_minutes = int(energy_needed_kwh / max(target_kw, 0.1) * 60)
        state.set('sensor.ev_charge_2025_time_to_limit_sim', total_minutes, {'unit_of_measurement': 'min', 'friendly_name': 'EV Charge 2025 Time to Limit'})

    except Exception as e:
        log.error(f"EV_PREDICT TOTAL ERROR v2: {e}\n{traceback.format_exc()}")

@state_trigger(ENT_ACTIVE_PROFILE,
               ENT_CURRENT_SOC,
               ENT_VEHICLE_LIMIT_SOC,
               ENT_MODE,
               ENT_CRONOSTAR_TARGET)
def ev_charge_trigger(**kwargs):
    ev_charge_predict_time()

@time_trigger('cron(* * * * *)')
def ev_charge_periodic():
    ev_charge_predict_time()
