import subprocess
import json

payload = {
    "entity_id": "media_player.cucina",
    "media_content_id": "radio m2o",
    "media_content_type": "music"
}

result = subprocess.run(
    ['curl', '-s', '-X', 'POST', '-H', 'Content-Type: application/json', 
     '-d', json.dumps(payload), 
     'http://supervisor/core/api/services/media_player/play_media'],
    capture_output=True, text=True, timeout=10
)
print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("Return code:", result.returncode)