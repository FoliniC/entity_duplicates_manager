import os

file_path = '/config/custom_components/localtuya/coordinator.py'
with open(file_path, 'r') as f:
    content = f.read()

# We want to wrap the status query to be optional
old_code = """                self.debug("Retrieving initial state")
                status = await self._interface.status(cid=self._node_id)
                if status is None:
                    self.warning("Failed to retrieve initial status, continuing in passive mode")
                    status = {}

                self.status_updated(status)"""

new_code = """                self.debug("Retrieving initial state")
                if int(self._device_config.scan_interval) == 0:
                    self.debug("Skipping initial status query for passive device")
                    status = {}
                else:
                    try:
                        status = await self._interface.status(cid=self._node_id)
                    except Exception as e:
                        self.warning(f"Initial status query failed ({e}), continuing in passive mode")
                        status = {}
                
                if status is None:
                    status = {}

                self.status_updated(status)"""

if old_code in content:
    new_content = content.replace(old_code, new_code)
    with open(file_path, 'w') as f:
        f.write(new_content)
    print("Patch V3 applied successfully")
else:
    print("Could not find V2 code block to patch")
