import json

def read_cronostar_profiles(path):
    """Regular python function to read JSON file, bypasses pyscript restrictions."""
    with open(path, 'r') as f:
        return json.load(f)
