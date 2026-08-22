#!/usr/bin/env python3
"""Nuclear option: clear ALL btc template sensors from registry + states."""
import json
import os

registry_path = "/config/.storage/core.entity_registry"

with open(registry_path) as f:
    data = json.load(f)

# Remove ALL template sensors with BTC unique_ids
btc_uids = {
    "btc_investment_eur", "btc_amount", "btc_avg_buy_price",
    "btc_current_value", "btc_profit_loss", "btc_profit_loss_pct",
    "target_phone_price", "target_phone_name", "target_phone_url",
    "btc_delta_to_phone", "btc_can_buy_phone", "btc_progress_to_phone_pct",
    "btc_roi_pct", "btc_taxable_gain", "btc_tax_amount", "btc_profit_loss_net",
    "btc_roi_pct_net", "btc_net_price_per_btc", "btc_to_sell_for_phone",
    "btc_break_even_phone_price", "btc_progress_to_phone_net_pct",
    "btc_can_buy_phone_net", "btc_delta_to_phone_net", "btc_days_to_phone_estimate"
}

to_keep = []
removed = []
for e in data["data"]["entities"]:
    if e.get("unique_id") in btc_uids and "template" in str(e.get("platform", "")):
        removed.append(e["entity_id"])
        # Also mark for removal by tracking these
    else:
        to_keep.append(e)

# Remove ALL sensor.* entities that have these unique_ids (both template and rest)
final_keep = []
removed2 = []
for e in to_keep:
    uid = e.get("unique_id", "")
    eid = e.get("entity_id", "")
    if eid.startswith("sensor.") and uid in btc_uids:
        removed2.append(eid)
    else:
        final_keep.append(e)

data["data"]["entities"] = final_keep

with open(registry_path, "w") as f:
    json.dump(data, f, indent=2)

print(f"✅ Total removed: {len(removed) + len(removed2)}")
for r in removed + removed2:
    print(f"  - {r}")
