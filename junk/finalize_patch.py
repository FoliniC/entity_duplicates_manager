import os

file_path = "/config/custom_components/localtuya/coordinator.py"

with open(file_path, 'r') as f:
    content = f.read()

# Cerchiamo il punto in cui viene gestita la connessione riuscita per forzare un aggiornamento DP
# subito dopo che pytuya ha stabilito il canale.

old_logic = """                self.status_updated(status)
            except (UnicodeDecodeError, DecodeError) as e:"""

new_logic = """                self.status_updated(status)
                
                # v1.0.24 Fix: Se il dispositivo è online ma HA lo vede unavailable, 
                # forziamo un aggiornamento dei DP (Command 18) per svegliare l'interfaccia.
                if self.connected and not status:
                    self.debug("Forcing DP refresh (Command 18) to wake up device")
                    try:
                        await self._interface.update_dps()
                    except:
                        pass
            except (UnicodeDecodeError, DecodeError) as e:"""

if old_logic in content:
    with open(file_path, 'w') as f:
        f.write(content.replace(old_logic, new_logic))
    print("SUCCESS: LocalTuya Coordinator updated with Command 18 wake-up logic.")
else:
    print("ERROR: Could not find injection point. The file might have been modified differently.")
