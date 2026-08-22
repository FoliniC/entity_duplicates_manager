#!/usr/bin/env python3
"""Register BTC Investment Tracker dashboard in HA storage."""
import json
import os

dashboards_path = "/config/.storage/lovelace_dashboards"
with open(dashboards_path, 'r') as f:
    data = json.load(f)

new_dashboard = {
    "id": "btc_investment_tracker",
    "show_in_sidebar": True,
    "title": "₿ BTC Investment Tracker",
    "require_admin": False,
    "mode": "yaml",
    "url_path": "btc-tracker",
    "icon": "mdi:bitcoin",
    "filename": "btc_investment_tracker.yaml"
}

exists = any(d.get('id') == 'btc_investment_tracker' for d in data['data']['items'])
if not exists:
    data['data']['items'].append(new_dashboard)
    with open(dashboards_path, 'w') as f:
        json.dump(data, f, indent=2)
    print("✅ Dashboard registered in lovelace_dashboards")
else:
    print("ℹ️ Dashboard already present")
