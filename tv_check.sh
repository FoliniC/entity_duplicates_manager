#!/system/bin/sh
echo "=== Permission groups ==="
pm list permissions -g 2>/dev/null | grep -A2 -iE "Nearby|Location" | head -15
echo "=== TV appops ==="
cmd appops get com.teamviewer.host.market 2>&1 | head -10
echo "=== ID search ==="
ls /data/data/com.teamviewer.host.market/shared_prefs/ 2>/dev/null | head
grep -iE "id=" /data/data/com.teamviewer.host.market/shared_prefs/* 2>/dev/null | head -3
echo "=== Network/LAN permission ==="
pm list permissions -g -r 2>/dev/null | grep -i "NEARBY_WIFI_DEVICES" | head -3
echo "=== Battery optimization ==="
cmd deviceidle force-idle 2>&1 | head -2 || echo "idle-ok"
