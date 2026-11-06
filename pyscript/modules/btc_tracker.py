"""
============================================================================
BITCOIN INVESTMENT TRACKER - Pyscript Advanced Logic (Italy 2026+)
============================================================================
Tassazione: 33% su tutte le plusvalenze (Art.1 c.24 L.Bilancio 2025, dal 1/1/2026)
Nessuna esenzione 2000€ - Bitcoin non è e-money token MiCAR
Formula netto per BTC: se prezzo>=costo → prezzo*0.67 + costo*0.33, altrimenti prezzo
Monitoraggio prezzo telefono: Xiaomi 17 Ultra 16/512GB via Trovaprezzi/Idealo
Da posizionare in: /config/pyscript/modules/btc_tracker.py
============================================================================

NOTE: This module uses JSON file persistence at /config/.storage/btc_tracker_data.json
instead of pyscript.app_config which is context-scoped.
"""

# Dummy decorators per import safety (linting)
def _dummy_decorator(*args, **kwargs):
    def decorator(func):
        return func
    if args and callable(args[0]) and not kwargs:
        return args[0]
    return decorator

service = _dummy_decorator
event_trigger = _dummy_decorator
time_trigger = _dummy_decorator
state_trigger = _dummy_decorator
task_unique = _dummy_decorator
# Real decorators injected by pyscript at runtime


# ============================================================================
# COSTANTI E CONFIGURAZIONE (ITALIA 2026+)
# ============================================================================
BTC_TRACKER_NAMESPACE = "btc_tracker"
HISTORY_MAX_ENTRIES = 1000
PRICE_HISTORY_HOURS = 168

# Tassazione Italia 2026+
TAX_RATE = 0.33          # 33% aliquota sostitutiva
TAX_EXEMPTION = 0        # NESSUNA esenzione 2000€ dal 2026
COST_BASIS_PER_BTC = 54000.0  # Costo fiscale per BTC (acquisto 29/06/2026)

# Telefono target
TARGET_PHONE_MODEL = "Xiaomi 17 Ultra 16/512GB"
TARGET_PHONE_URL = "https://www.trovaprezzi.it/prezzo_cellulari_xiaomi_17_ultra"

# Persistenza su file JSON
DATA_FILE = "/config/.storage/btc_tracker_data.json"


# ============================================================================
# HELPER FUNCTIONS - Persistence via JSON file
# ============================================================================
def _load_data():
    """Load persistent data from JSON file."""
    import json
    import os
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError):
        pass
    return {'snapshots': [], 'last_milestone': 0}


def _save_data(data):
    """Save persistent data to JSON file."""
    import json
    import os
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)


def _get_state(entity_id, default=0):
    """Safely get entity state as float."""
    try:
        state = hass.states.get(entity_id)
        if state and state.state not in ('unknown', 'unavailable', ''):
            return float(state.state)
    except (ValueError, TypeError):
        pass
    return default


def _set_state(entity_id, value, attributes=None):
    """Set state for a sensor (creates if not exists)."""
    hass.states.async_set(entity_id, value, attributes or {})


def safe_notify(message, title=None, target=None, data=None):
    """Invia una notifica FUORI dall'event loop (non bloccante).

    Le chiamate dirette a hass.services.call('notify', ...) sono sincrone e
    girano sull'event loop di HA: se il servizio notify (es. mobile_app verso
    l'app non raggiungibile) si blocca/impiega molto, INCHIODA l'intero event
    loop di Home Assistant (stall del frontend, freeze totale). Lanciando il
    notify come task separato via async_call(blocking=False), anche un notify lento o
    bloccato non può più fermare HA.
    """
    try:
        targets = target if isinstance(target, list) else ([target] if target else [])
        for t in targets:
            svc_data = {"message": message}
            if title:
                svc_data["title"] = title
            name = t.split(".")[-1] if "." in t else t
            if data:
                # Le opzioni extra (tag/importance/icon) sono accettate
                # SOLO dai servizi legacy per-device (notify.mobile_app_<nome>):
                # notify.send_message ammette unicamente message + title.
                svc_data["data"] = data
                svc = name if name.startswith("mobile_app_") else "mobile_app_" + name
                # async_call con blocking=False restituisce già un Task, non serve async_create_task
                hass.services.async_call("notify", svc, svc_data, blocking=False)
            else:
                # notify.send_message accetta solo message/title: il target va
                # indicato come entity_id. I target passati sono nomi di servizio
                # legacy (notify.mobile_app_<nome>): la corrispondente entity e'
                # notify.<nome>.
                entity = t
                if name.startswith("mobile_app_"):
                    entity = "notify." + name[len("mobile_app_"):]
                svc_data["entity_id"] = [entity]
                # async_call con blocking=False restituisce già un Task
                hass.services.async_call("notify", "send_message", svc_data, blocking=False)
    except Exception as e:
        log.warning(f"BTC Tracker: safe_notify fallita: {e}")


def _prezzo_netto_per_btc(prezzo_attuale, costo=None):
    """
    Calcola il prezzo netto equivalente per BTC dopo tasse 33%.
    Formula: se prezzo >= costo → prezzo * (1 - TAX_RATE) + costo * TAX_RATE
             altrimenti → prezzo (minusvalenza, no tasse)
    """
    if costo is None:
        costo = COST_BASIS_PER_BTC
    if prezzo_attuale >= costo:
        return prezzo_attuale * (1 - TAX_RATE) + costo * TAX_RATE
    else:
        return prezzo_attuale


# ============================================================================
# SERVIZI PUBBLICI
# ============================================================================

@service("btc_tracker.record_snapshot")
def record_snapshot():
    """
    Registra snapshot corrente dello stato dell'investimento.
    Chiamare periodicamente (es. ogni ora) per costruire storia.
    """
    from datetime import datetime
    
    prezzo_attuale = _get_state('sensor.bitcoin_price_eur')
    costo = _get_state('sensor.btc_cost_basis_eur_template')
    prezzo_netto = _prezzo_netto_per_btc(prezzo_attuale, costo)
    
    snapshot = {
        'timestamp': datetime.now().isoformat(),
        'btc_price_eur': prezzo_attuale,
        'btc_net_price_per_btc': round(prezzo_netto, 2),
        'btc_24h_change': _get_state('sensor.bitcoin_24h_change_pct'),
        'btc_amount': _get_state('sensor.btc_amount'),
        'btc_current_value': _get_state('sensor.btc_current_value'),
        'btc_investment_eur': _get_state('sensor.btc_investment_eur'),
        'btc_profit_loss': _get_state('sensor.btc_profit_loss'),
        'btc_profit_loss_net': _get_state('sensor.btc_profit_loss_net'),
        'btc_roi_pct': _get_state('sensor.btc_roi_pct'),
        'btc_roi_pct_net': _get_state('sensor.btc_roi_pct_net'),
        'btc_tax_amount': _get_state('sensor.btc_tax_amount'),
        'target_phone_price': _get_state('sensor.target_phone_price'),
        'btc_progress_net_pct': _get_state('sensor.btc_progress_to_phone_net_pct'),
        'btc_delta_phone_net': _get_state('sensor.btc_delta_to_phone_net'),
        'btc_to_sell_for_phone': _get_state('sensor.btc_to_sell_for_phone'),
        'btc_break_even_phone_price': _get_state('sensor.btc_break_even_phone_price'),
    }
    
    data = _load_data()
    data['snapshots'].append(snapshot)
    if len(data['snapshots']) > HISTORY_MAX_ENTRIES:
        data['snapshots'] = data['snapshots'][-HISTORY_MAX_ENTRIES:]
    _save_data(data)
    
    _set_state('sensor.btc_tracker_snapshots_count', len(data['snapshots']), {
        'friendly_name': 'BTC Tracker Snapshots Count',
        'unit_of_measurement': 'snapshots',
        'last_snapshot': snapshot['timestamp']
    })
    
    log.info(f"BTC Tracker: Snapshot recorded. Total: {len(data['snapshots'])}")
    return {'recorded': True, 'total_snapshots': len(data['snapshots'])}


@service("btc_tracker.get_history")
def get_history(hours=24, limit=100):
    """Restituisce storico degli snapshot."""
    from datetime import datetime, timedelta
    
    data = _load_data()
    history = data.get('snapshots', [])
    cutoff = datetime.now() - timedelta(hours=hours)
    
    filtered = [
        h for h in history
        if datetime.fromisoformat(h['timestamp']) >= cutoff
    ]
    
    return {
        'entries': filtered[-limit:],
        'total_available': len(history),
        'filtered_count': len(filtered)
    }


@service("btc_tracker.calculate_trend")
def calculate_trend(hours=24):
    """Calcola trend del profitto NETTO BTC nelle ultime N ore."""
    from datetime import datetime, timedelta
    
    data = _load_data()
    history = data.get('snapshots', [])
    cutoff = datetime.now() - timedelta(hours=hours)
    
    filtered = [
        h for h in history
        if datetime.fromisoformat(h['timestamp']) >= cutoff
    ]
    
    if len(filtered) < 2:
        return {'error': 'Not enough data points'}
    
    # Linear regression sui punti profit/loss NETTO
    x_vals = list(range(len(filtered)))
    y_vals = [h.get('btc_profit_loss_net', 0) for h in filtered]
    
    n = len(x_vals)
    sum_x = sum(x_vals)
    sum_y = sum(y_vals)
    sum_xy = sum(x * y for x, y in zip(x_vals, y_vals))
    sum_x2 = sum(x * x for x in x_vals)
    
    denom = (n * sum_x2 - sum_x * sum_x)
    if denom == 0:
        return {'error': 'Cannot compute trend (zero variance)'}
    
    slope = (n * sum_xy - sum_x * sum_y) / denom
    current_profit = y_vals[-1]
    target_price = _get_state('sensor.target_phone_price')
    remaining = target_price - current_profit
    
    projection_hours = None
    if slope > 0 and remaining > 0:
        intervals = len(filtered) / max(hours, 1)
        projection_hours = remaining / (slope * intervals) if intervals > 0 else None
    
    trend = 'up' if slope > 0.01 else ('down' if slope < -0.01 else 'flat')
    
    result = {
        'trend': trend,
        'slope_per_snapshot': round(slope, 4),
        'velocity_eur_per_hour': round(slope * (len(filtered) / max(hours, 1)), 2),
        'current_profit_net': round(current_profit, 2),
        'target_price': round(target_price, 2),
        'remaining_eur': round(remaining, 2),
        'projection_hours': round(projection_hours, 1) if projection_hours else None,
        'data_points': n,
        'hours_analyzed': hours
    }
    
    _set_state('sensor.btc_tracker_trend', trend, {
        'friendly_name': 'BTC Tracker Trend (NETTO)',
        'icon': 'mdi:chart-line',
        **{k: v for k, v in result.items() if k != 'trend'}
    })
    
    return result


@service("btc_tracker.check_milestones")
def check_milestones():
    """Controlla e notifica milestone basate su profitto NETTO."""
    profit_net = _get_state('sensor.btc_profit_loss_net')
    phone_price = _get_state('sensor.target_phone_price')
    phone_name = hass.states.get('sensor.target_phone_name')
    phone_name = phone_name.state if phone_name else TARGET_PHONE_MODEL
    
    progress = (profit_net / phone_price * 100) if phone_price > 0 else 0
    
    milestones = [
        (10, "Primi passi 🌱"),
        (25, "Un quarto del percorso 📈"),
        (50, "Metà strada! 🎯"),
        (75, "Tre quarti! 🚀"),
        (90, "Ultimi metri! 🎯"),
        (100, "OBIETTIVO RAGGIUNTO! 🎉"),
        (125, "Oltre l'obiettivo! 💎"),
        (150, "1.5x l'obiettivo! 💰"),
        (200, "Doppio obiettivo! 🏆"),
    ]
    
    triggered = []
    data = _load_data()
    last_notified = data.get('last_milestone', 0)
    
    for threshold, label in milestones:
        if progress >= threshold and last_notified < threshold:
            safe_notify(
                message=f"{label}\n\nProgresso NETTO: {progress:.1f}%\nProfitto netto: {profit_net:.2f} € / {phone_price:.2f} €\n{phone_name}",
                title=f"₿ BTC Tracker: {label}",
                target=['notify.mobile_app_redmi_note_13_pro_5g'],
                data={
                                'tag': f'btc_milestone_{int(threshold)}',
                                'importance': 'high' if threshold >= 90 else 'default',
                                'icon': 'mdi:bitcoin'
                            }
            )
            triggered.append(threshold)
            data['last_milestone'] = threshold
    
    _save_data(data)
    return {'triggered': triggered, 'progress_pct': round(progress, 1)}


@service("btc_tracker.export_data")
def export_data(format='json'):
    """Esporta tutti i dati per backup/analisi esterna."""
    data = _load_data()
    config = {
        'investment_eur': _get_state('sensor.btc_investment_eur'),
        'btc_amount': _get_state('sensor.btc_amount'),
        'avg_buy_price': _get_state('sensor.btc_cost_basis_eur_template'),
        'cost_basis_per_btc': COST_BASIS_PER_BTC,
        'tax_rate': TAX_RATE,
        'tax_exemption': TAX_EXEMPTION,
        'target_phone_price': _get_state('sensor.target_phone_price'),
        'target_phone_name': TARGET_PHONE_MODEL,
        'target_phone_url': TARGET_PHONE_URL,
    }
    
    from datetime import datetime
    export = {
        'exported_at': datetime.now().isoformat(),
        'config': config,
        'current_state': {
            'btc_price_eur': _get_state('sensor.bitcoin_price_eur'),
            'btc_net_price_per_btc': _get_state('sensor.btc_net_price_per_btc'),
            'btc_current_value': _get_state('sensor.btc_current_value'),
            'btc_profit_loss': _get_state('sensor.btc_profit_loss'),
            'btc_profit_loss_net': _get_state('sensor.btc_profit_loss_net'),
            'btc_roi_pct': _get_state('sensor.btc_roi_pct'),
            'btc_roi_pct_net': _get_state('sensor.btc_roi_pct_net'),
            'btc_tax_amount': _get_state('sensor.btc_tax_amount'),
            'btc_progress_net_pct': _get_state('sensor.btc_progress_to_phone_net_pct'),
            'btc_to_sell_for_phone': _get_state('sensor.btc_to_sell_for_phone'),
            'btc_break_even_phone_price': _get_state('sensor.btc_break_even_phone_price'),
        },
        'history': data.get('snapshots', [])
    }
    
    can_buy_state = hass.states.get('sensor.btc_can_buy_phone_net')
    if can_buy_state:
        export['current_state']['btc_can_buy_phone_net'] = can_buy_state.state
    
    if format == 'csv':
        import csv
        import io
        output = io.StringIO()
        history = data.get('snapshots', [])
        if history:
            writer = csv.DictWriter(output, fieldnames=history[0].keys())
            writer.writeheader()
            writer.writerows(history)
        return {'csv': output.getvalue(), 'config': config}
    
    return export


@service("btc_tracker.reset_history")
def reset_history(confirm=False):
    """Reset storico snapshot (richiede confirm=True)."""
    if not confirm:
        return {'error': 'Confirmation required. Call with confirm=true'}
    
    data = {'snapshots': [], 'last_milestone': 0}
    _save_data(data)
    _set_state('sensor.btc_tracker_snapshots_count', 0)
    return {'reset': True}


@service("btc_tracker.fetch_phone_price")
def fetch_phone_price():
    """
    Tenta di recuperare il prezzo minimo del telefono da Trovaprezzi.
    NOTA: Richiede libreria requests e beautifulsoup4.
    """
    import requests
    from bs4 import BeautifulSoup
    import re
    
    try:
        url = TARGET_PHONE_URL
        headers = {'User-Agent': 'Mozilla/5.0 (Home Assistant BTC Tracker)'}
        resp = requests.get(url, headers=headers, timeout=10)
        
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            # Selettori Trovaprezzi (da adattare)
            price_elem = soup.select_one('.price.min-price, .offer-price, [itemprop="price"]')
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                match = re.search(r'[\d.,]+', price_text.replace('.', '').replace(',', '.'))
                if match:
                    price = float(match.group())
                    current = _get_state('input_number.target_phone_price')
                    if price < current:
                        hass.services.call('input_number', 'set_value', {
                            'entity_id': 'input_number.target_phone_price',
                            'value': price
                        })
                        log.info(f"BTC Tracker: Nuovo prezzo minimo telefono: {price}€")
                        return {'updated': True, 'new_price': price}
    except Exception as e:
        log.warning(f"BTC Tracker: Errore fetch telefono: {e}")
    
    return {'updated': False, 'source': 'fallback_input_number'}


# ============================================================================
# TRIGGER AUTOMATICI
# ============================================================================

# Snapshot ogni ora
@time_trigger("cron(0 * * * *)")
@task_unique("btc_tracker_hourly_snapshot")
async def hourly_snapshot():
    """Snapshot automatico ogni ora."""
    record_snapshot()
    
    # Ogni 6 ore calcola trend e milestone
    from datetime import datetime
    if datetime.now().hour % 6 == 0:
        calculate_trend(24)
        check_milestones()


# Report giornaliero alle 9:00 (in aggiunta all'automazione YAML)
@time_trigger("cron(0 9 * * *)")
@task_unique("btc_tracker_daily_report_pyscript")
async def daily_report_pyscript():
    """Report giornaliero arricchito con trend e dati NETTO 33%."""
    from datetime import datetime
    
    trend = calculate_trend(24)
    profit_net = _get_state('sensor.btc_profit_loss_net')
    phone_price = _get_state('sensor.target_phone_price')
    phone_name = TARGET_PHONE_MODEL
    
    trend_str = trend.get('trend', 'N/A').upper() if isinstance(trend, dict) and 'trend' in trend else 'N/A'
    velocity = trend.get('velocity_eur_per_hour', 0) if isinstance(trend, dict) else 0
    projection = trend.get('projection_hours', 'N/A') if isinstance(trend, dict) else 'N/A'
    
    message = f"""**₿ Bitcoin Daily Report - {datetime.now().strftime('%d/%m/%Y')}** (Tasse 33%)

**Mercato:**
• BTC: {_get_state('sensor.bitcoin_price_eur'):.2f} € (24h: {_get_state('sensor.bitcoin_24h_change_pct'):.2f}%)
• Netto per BTC (dopo tasse): {_get_state('sensor.btc_net_price_per_btc'):.2f} €

**Portafoglio:**
• BTC: {_get_state('sensor.btc_amount')} 
• Valore: {_get_state('sensor.btc_current_value'):.2f} €
• Investito: {_get_state('sensor.btc_investment_eur'):.2f} €
• P/L LORDO: {_get_state('sensor.btc_profit_loss'):.2f} € ({_get_state('sensor.btc_roi_pct'):.2f}%)
• Tasse (33%): {_get_state('sensor.btc_tax_amount'):.2f} €
• P/L NETTO: {profit_net:.2f} € ({_get_state('sensor.btc_roi_pct_net'):.2f}%)

**Trend 24h NETTO:** {trend_str}
• Velocità: {velocity:.2f} €/h
• Proiezione target: {projection} ore

**Obiettivo {phone_name} ({phone_price:.2f}€):**
• Progresso NETTO: {_get_state('sensor.btc_progress_to_phone_net_pct'):.1f}%
• Delta NETTO: {_get_state('sensor.btc_delta_to_phone_net'):.2f} €
• BTC da vendere: {_get_state('sensor.btc_to_sell_for_phone'):.8f} BTC
• Break-even BTC price: {_get_state('sensor.btc_break_even_phone_price'):.0f} €/BTC
    """.strip()
    
    safe_notify(
        message=message,
        title="📊 BTC Tracker: Report Giornaliero (NETTO 33%)",
        target=['notify.mobile_app_redmi_note_13_pro_5g'],
        data={
            'tag': 'btc_daily_report_pyscript',
            'importance': 'default',
            'icon': 'mdi:chart-line'
        }
    )


# Startup: verifica stato e ripristina milestone tracking
@time_trigger("startup")
@task_unique("btc_tracker_startup")
async def startup():
    """Inizializzazione all'avvio di HA."""
    log.info("BTC Tracker: Starting up... (Italia 2026+ tasse 33%)")
    
    data = _load_data()
    if 'snapshots' not in data:
        data['snapshots'] = []
    if 'last_milestone' not in data:
        data['last_milestone'] = 0
    _save_data(data)
    
    record_snapshot()
    calculate_trend(24)
    
    log.info("BTC Tracker: Startup complete")