#!/usr/bin/env python3
"""Remove old BTC template sensors from entity registry to force recreation."""
import json

registry_path = "/config/.storage/core.entity_registry"

with open(registry_path) as f:
    data = json.load(f)

# Remove old Italian-named template sensors (keep only input_number, input_text, rest sensors, automations)
old_uids = {
    "btc_investment_eur", "btc_amount", "btc_avg_buy_price",
    "btc_current_value", "btc_profit_loss", "btc_profit_loss_pct",
    "target_phone_price", "target_phone_name", "target_phone_url",
    "btc_delta_to_phone", "btc_can_buy_phone", "btc_progress_to_phone_pct",
    "btc_roi_pct", "btc_taxable_gain", "btc_tax_amount", "btc_profit_loss_net",
    "btc_roi_pct_net", "btc_net_price_per_btc", "btc_to_sell_for_phone",
    "btc_break_even_phone_price", "btc_progress_to_phone_net_pct",
    "btc_can_buy_phone_net", "btc_delta_to_phone_net", "btc_days_to_phone_estimate"
}

# Filter: remove template sensors with these unique_ids but keep input_number/input_text/rest sensors
to_keep = []
removed = []
for e in data["data"]["entities"]:
    if e.get("unique_id") in old_uids and e["entity_id"].startswith("sensor."):
        removed.append(e["entity_id"])
    else:
        to_keep.append(e)

data["data"]["entities"] = to_keep

with open(registry_path, "w") as f:
    json.dump(data, f, indent=2)

print(f"✅ Rimosse {len(removed)} entity vecchie:")
for r in removed:
    print(f"  - {r}")
