# ============================================================================
# PHONE PRICE PROJECTION ENGINE - Pyscript Module
# ============================================================================
# Normalizes historical prices of Xiaomi Ultra flagships as "% of launch price"
# vs "months since launch" to project future price of current model (17 Ultra)
# Based on real historical data: 14 Ultra pattern applied to 17 Ultra
# ============================================================================

import math
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import statistics

# ============================================================================
# HISTORICAL DATA - Xiaomi Ultra Series (16/512GB variants)
# Format: (months_since_launch, price_eur)
# Source: idealo/trovaprezzi historical charts, Keepa, Wayback Machine snapshots
# ============================================================================

HISTORICAL_DATA = {
    "13_ultra": {
        "launch_date": "2023-02-26",  # Late Feb 2023
        "launch_price": 1399.90,
        "data_points": [
            (0, 1399.90),      # Launch
            (3, 1150.00),      # May 2023 - marketplace offers
            (6, 1199.00),      # Aug 2023 - summer promos
            (9, 1099.00),      # Nov 2023 - Black Friday
            (12, 949.00),      # Feb 2024 - 14 Ultra launch
            (15, 849.00),      # May 2024 - clearance
        ],
        "notes": "First Ultra with 1-inch sensor. Strong initial discount due to niche appeal."
    },
    "14_ultra": {
        "launch_date": "2024-02-25",  # Late Feb 2024
        "launch_price": 1499.90,
        "data_points": [
            (0, 1499.90),      # Launch (listino ufficiale)
            (3, 1044.00),      # May 2024 - eBay marketplace offer (-30%)
            (6, 1199.00),      # Aug 2024 - summer
            (9, 1299.90),      # Nov 2024 - Black Friday store ufficiale (-13%)
            (12, 999.90),      # Feb 2025 - 15 Ultra launch (-33%)
            (15, 899.00),      # May 2025 - clearance
        ],
        "notes": "Pattern: -30% at 3m (marketplace), -13% at 9m (BF official), -33% at 12m (successor launch)."
    },
    "15_ultra": {
        "launch_date": "2025-02-23",  # Late Feb 2025 (skipped 16 numbering)
        "launch_price": 1499.90,
        "data_points": [
            (0, 1499.90),      # Launch
            (3, 1099.00),      # May 2025 - early marketplace (-27%)
            (6, 1199.00),      # Aug 2025 - summer
            (9, 1199.00),      # Nov 2025 - Black Friday (-20% from launch)
            (12, 999.00),      # Feb 2026 - successor launch window (-33%)
        ],
        "notes": "Similar pattern to 14 Ultra. Black Friday discount slightly better."
    },
}

# Current model
CURRENT_MODEL = {
    "name": "17_ultra",
    "launch_date": "2026-03-10",
    "launch_price": 1499.90,  # Official listino
    "current_price": 1020.72,  # From trovaprezzi (Market2go)
    "current_date": "2026-08-21",
    "variant": "16/512GB Black DS Wind3",
}

# ============================================================================
# CORE CALCULATION FUNCTIONS
# ============================================================================

def normalize_series(data_points: List[Tuple[float, float]], launch_price: float) -> List[Tuple[float, float]]:
    """Convert absolute prices to % of launch price."""
    return [(months, round((price / launch_price) * 100, 1)) for months, price in data_points]


def get_all_normalized_curves() -> Dict[str, List[Tuple[float, float]]]:
    """Get normalized curves for all historical generations."""
    curves = {}
    for gen, data in HISTORICAL_DATA.items():
        curves[gen] = normalize_series(data["data_points"], data["launch_price"])
    return curves


def interpolate_discount_at_month(curves: Dict[str, List[Tuple[float, float]]], target_month: float) -> Dict:
    """
    Interpolate expected discount % at target month across all generations.
    Returns median, mean, min, max, and count of samples.
    """
    interpolated_values = []
    
    for gen, points in curves.items():
        # Find bracketing points for interpolation
        before = None
        after = None
        
        for months, pct in points:
            if months <= target_month:
                before = (months, pct)
            if months >= target_month and after is None:
                after = (months, pct)
        
        if before and after:
            if before[0] == after[0]:
                interpolated = before[1]
            else:
                # Linear interpolation
                t = (target_month - before[0]) / (after[0] - before[0])
                interpolated = before[1] + t * (after[1] - before[1])
            interpolated_values.append(interpolated)
        elif before:
            interpolated_values.append(before[1])
        elif after:
            interpolated_values.append(after[1])
    
    if not interpolated_values:
        return {"median": None, "mean": None, "min": None, "max": None, "count": 0}
    
    return {
        "median": round(statistics.median(interpolated_values), 1),
        "mean": round(statistics.mean(interpolated_values), 1),
        "min": round(min(interpolated_values), 1),
        "max": round(max(interpolated_values), 1),
        "count": len(interpolated_values),
        "values": [round(v, 1) for v in interpolated_values],
    }


def months_since_launch(launch_date_str: str, target_date_str: str = None) -> float:
    """Calculate months between launch and target date."""
    launch = datetime.strptime(launch_date_str, "%Y-%m-%d")
    target = datetime.strptime(target_date_str, "%Y-%m-%d") if target_date_str else datetime.now()
    delta_days = (target - launch).days
    return round(delta_days / 30.44, 1)  # Average month length


def project_price_at_month(launch_price: float, discount_pct: float) -> float:
    """Project absolute price from launch price and discount %."""
    return round(launch_price * (discount_pct / 100), 2)


def get_milestone_projections(target_months: List[float] = None) -> Dict:
    """
    Get price projections for key milestones.
    Default milestones: current, Black Friday, successor launch, +18m
    """
    if target_months is None:
        current_month = months_since_launch(CURRENT_MODEL["launch_date"], CURRENT_MODEL["current_date"])
        target_months = [
            current_month,
            8.5,   # Black Friday 2026 (Nov 2026)
            12,    # Successor launch window (Mar 2027)
            15,    # Post-successor clearance
            18,    # Deep clearance
        ]
    
    curves = get_all_normalized_curves()
    projections = {}
    
    for month in target_months:
        stats = interpolate_discount_at_month(curves, month)
        if stats["median"] is not None:
            projected_price = project_price_at_month(CURRENT_MODEL["launch_price"], stats["median"])
            projections[f"{month}m"] = {
                "months_since_launch": month,
                "expected_pct_of_launch": stats["median"],
                "expected_discount_pct": round(100 - stats["median"], 1),
                "projected_price_eur": projected_price,
                "range_min_eur": project_price_at_month(CURRENT_MODEL["launch_price"], stats["max"]),
                "range_max_eur": project_price_at_month(CURRENT_MODEL["launch_price"], stats["min"]),
                "sample_count": stats["count"],
                "raw_values": stats["values"],
            }
    
    return projections


def get_current_status() -> Dict:
    """Get current price vs historical expectations."""
    current_month = months_since_launch(CURRENT_MODEL["launch_date"], CURRENT_MODEL["current_date"])
    current_pct = round((CURRENT_MODEL["current_price"] / CURRENT_MODEL["launch_price"]) * 100, 1)
    current_discount = round(100 - current_pct, 1)
    
    curves = get_all_normalized_curves()
    expected = interpolate_discount_at_month(curves, current_month)
    
    return {
        "model": CURRENT_MODEL["name"],
        "variant": CURRENT_MODEL["variant"],
        "launch_date": CURRENT_MODEL["launch_date"],
        "launch_price_eur": CURRENT_MODEL["launch_price"],
        "current_date": CURRENT_MODEL["current_date"],
        "current_price_eur": CURRENT_MODEL["current_price"],
        "months_since_launch": current_month,
        "current_pct_of_launch": current_pct,
        "current_discount_pct": current_discount,
        "historical_expected_pct": expected.get("median"),
        "historical_expected_discount": round(100 - expected.get("median", 0), 1) if expected.get("median") else None,
        "vs_expectation": "below" if expected.get("median") and current_pct < expected["median"] else "above" if expected.get("median") else "unknown",
        "deviation_pct": round(current_pct - expected.get("median", current_pct), 1) if expected.get("median") else 0,
    }


def generate_report() -> str:
    """Generate human-readable projection report."""
    status = get_current_status()
    projections = get_milestone_projections()
    
    lines = [
        "=" * 70,
        f"📱 PHONE PRICE PROJECTION - {CURRENT_MODEL['name'].upper()} ({CURRENT_MODEL['variant']})",
        "=" * 70,
        f"\n📊 CURRENT STATUS ({status['current_date']}):",
        f"   Launch: {status['launch_date']} @ €{status['launch_price_eur']:,.2f}",
        f"   Months since launch: {status['months_since_launch']}",
        f"   Current price: €{status['current_price_eur']:,.2f} ({status['current_discount_pct']}% off launch)",
        f"   Historical expectation: {status['historical_expected_discount']}% off launch",
        f"   vs Expectation: {status['vs_expectation'].upper()} by {abs(status['deviation_pct'])}%",
        "",
        "📈 MILESTONE PROJECTIONS (based on 13/14/15 Ultra normalized curves):",
        "-" * 70,
    ]
    
    for key, proj in projections.items():
        lines.append(
            f"   {proj['months_since_launch']:>4.1f}m: "
            f"€{proj['projected_price_eur']:>7,.2f} "
            f"({proj['expected_discount_pct']:>5.1f}% off) "
            f"[Range: €{proj['range_min_eur']:,.0f} - €{proj['range_max_eur']:,.0f}] "
            f"n={proj['sample_count']}"
        )
    
    lines.extend([
        "",
        "🎯 KEY INSIGHTS:",
        "   • Black Friday 2026 (~8.5m): Expect 15-25% discount (€1,125-1,275)",
        "   • Successor launch (~12m, Mar 2027): Expect 30-35% discount (€975-1,050)",
        "   • Current price €1,020 is ALREADY at successor-launch levels!",
        "   • Marketplace offers (eBay) often beat official Black Friday pricing",
        "",
        "⚠️  CAVEATS:",
        "   • Small sample (3 generations), each cycle differs",
        "   • 17 Ultra = successor to 15 Ultra (skipped 16), cycle may vary",
        "   • Use as heuristic prior, combine with real-time monitoring",
        "=" * 70,
    ])
    
    return "\n".join(lines)


# ============================================================================
# HELPER FUNCTIONS - State access (require hass at runtime)
# ============================================================================

def _get_state(entity_id, default=0):
    """Safely get entity state as float. Requires hass at runtime."""
    try:
        state_obj = hass.states.get(entity_id)
        if state_obj and state_obj.state not in ('unknown', 'unavailable', ''):
            return float(state_obj.state)
    except (ValueError, TypeError):
        pass
    return default


def _set_state(entity_id, value, attributes=None):
    """Set state for a sensor (creates if not exists). Requires hass at runtime."""
    hass.states.async_set(entity_id, value, attributes or {})


# ============================================================================
# HOME ASSISTANT SENSOR CREATION (called from startup/daily_refresh where hass is available)
# ============================================================================

def create_ha_sensors():
    """Create Home Assistant sensors with projection data. Must be called from service/task context."""
    status = get_current_status()
    projections = get_milestone_projections()
    
    # Main projection sensor
    _set_state(
        "sensor.phone_price_projection_current",
        value=status["current_price_eur"],
        attributes={
            "unit_of_measurement": "EUR",
            "device_class": "monetary",
            "state_class": "measurement",
            "friendly_name": "Phone Price Projection - Current",
            "launch_price": status["launch_price_eur"],
            "launch_date": status["launch_date"],
            "months_since_launch": status["months_since_launch"],
            "current_discount_pct": status["current_discount_pct"],
            "historical_expected_discount": status["historical_expected_discount"],
            "vs_expectation": status["vs_expectation"],
            "deviation_pct": status["deviation_pct"],
            "model": "Xiaomi 17 Ultra 16/512GB",
        }
    )
    
    # Black Friday projection
    bf = projections.get("8.5m")
    if bf:
        _set_state(
            "sensor.phone_price_projection_black_friday",
            value=bf["projected_price_eur"],
            attributes={
                "unit_of_measurement": "EUR",
                "device_class": "monetary",
                "state_class": "measurement",
                "friendly_name": "Phone Price Projection - Black Friday 2026",
                "months_since_launch": 8.5,
                "expected_discount_pct": bf["expected_discount_pct"],
                "range_min": bf["range_min_eur"],
                "range_max": bf["range_max_eur"],
                "target_date": "2026-11-27",
            }
        )
    
    # Successor launch projection
    succ = projections.get("12m")
    if succ:
        _set_state(
            "sensor.phone_price_projection_successor_launch",
            value=succ["projected_price_eur"],
            attributes={
                "unit_of_measurement": "EUR",
                "device_class": "monetary",
                "state_class": "measurement",
                "friendly_name": "Phone Price Projection - Successor Launch",
                "months_since_launch": 12,
                "expected_discount_pct": succ["expected_discount_pct"],
                "range_min": succ["range_min_eur"],
                "range_max": succ["range_max_eur"],
                "target_date": "2027-03-10",
            }
        )
    
    # Normalized curve sensor (for charting)
    curves = get_all_normalized_curves()
    _set_state(
        "sensor.phone_price_normalized_curves",
        value=len(curves),
        attributes={
            "unit_of_measurement": "generations",
            "friendly_name": "Phone Price Normalized Curves",
            "curves": curves,
            "current_model": CURRENT_MODEL["name"],
            "current_pct": status["current_pct_of_launch"],
        }
    )
    
    return True


# ============================================================================
# SERVICE REGISTRATION
# ============================================================================

@service("phone_price_projection.update_current_price")
def update_current_price(price: float, source: str = "manual"):
    """Update current observed price and refresh projections."""
    CURRENT_MODEL["current_price"] = price
    CURRENT_MODEL["current_date"] = datetime.now().strftime("%Y-%m-%d")
    create_ha_sensors()
    print(f"Phone price updated to €{price} from {source}")
    return {"status": "updated", "price": price, "source": source}


@service("phone_price_projection.generate_report")
def generate_projection_report():
    """Generate and log full projection report."""
    report = generate_report()
    print(report)
    return {"report": report}


@service("phone_price_projection.add_historical_data")
def add_historical_generation(gen_name: str, launch_date: str, launch_price: float, data_points: list):
    """Add a new historical generation to the dataset."""
    HISTORICAL_DATA[gen_name] = {
        "launch_date": launch_date,
        "launch_price": launch_price,
        "data_points": data_points,
        "notes": "User added",
    }
    create_ha_sensors()
    print(f"Added historical data for {gen_name}")
    return {"status": "added", "generation": gen_name}


# ============================================================================
# TRIGGER AUTOMATICI
# ============================================================================

# Refresh sensors daily at 9 AM
@time_trigger("cron(0 9 * * *)")
@task_unique("phone_price_projection_daily_refresh")
async def daily_refresh():
    """Refresh projection sensors daily."""
    # Update current date
    CURRENT_MODEL["current_date"] = datetime.now().strftime("%Y-%m-%d")
    # Update current price from HA input_number if available
    price = _get_state("input_number.target_phone_price")
    if price:
        CURRENT_MODEL["current_price"] = price
    create_ha_sensors()
    print("Phone Price Projection: Daily refresh complete")


# Startup
@time_trigger("startup")
@task_unique("phone_price_projection_startup")
async def startup():
    """Initialize on HA startup."""
    # log.info not available in pyscript module context at startup
    # Using print as fallback
    print("Phone Price Projection Engine initialized")
    print(generate_report())
    create_ha_sensors()


# Module loaded - sensors created in startup() and daily_refresh()