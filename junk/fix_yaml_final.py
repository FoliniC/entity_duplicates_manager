import os
import glob

for f in glob.glob("yaml_generator/template_triggers/*.yaml"):
    with open(f, 'r') as file:
        content = file.read()
    
    # Rimuoviamo trigger: se presente all'inizio
    # Dobbiamo avere una lista di dizionari che contengono trigger e sensor
    # La struttura di cucina_persistence.yaml è:
    # trigger:
    #   - trigger: state ...
    # sensor:
    #   - name: ...
    #
    # Dobbiamo trasformarlo in:
    # - trigger:
    #     - platform: state ...
    #   sensor:
    #     - name: ...
    # Questo è complesso per script shell.
    # Userò un approccio più semplice: sovrascrivo con la struttura corretta.
    pass
