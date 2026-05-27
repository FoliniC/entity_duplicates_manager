import os

file_path = "/config/custom_components/localtuya/core/cloud_api.py"

with open(file_path, 'r') as f:
    content = f.read()

get_old = """                    async with session.get(
                        full_url, headers=dict(default_par, **headers)
                    ) as resp:
                        return await resp.json()"""
get_new = """                    async with session.get(
                        full_url, headers=dict(default_par, **headers)
                    ) as resp:
                        self._logger.debug("CLOUD API RESP - Status: %s - Body: %s", resp.status, await resp.text())
                        return await resp.json()"""

post_old = """                    async with session.post(
                        full_url,
                        headers=dict(default_par, **headers),
                        data=json.dumps(body),
                    ) as resp:
                        return await resp.json()"""
post_new = """                    async with session.post(
                        full_url,
                        headers=dict(default_par, **headers),
                        data=json.dumps(body),
                    ) as resp:
                        self._logger.debug("CLOUD API RESP - Status: %s - Body: %s", resp.status, await resp.text())
                        return await resp.json()"""

put_old = """                    async with session.put(
                        full_url,
                        headers=dict(default_par, **headers),
                        data=json.dumps(body),
                    ) as resp:
                        return await resp.json()"""
put_new = """                    async with session.put(
                        full_url,
                        headers=dict(default_par, **headers),
                        data=json.dumps(body),
                    ) as resp:
                        self._logger.debug("CLOUD API RESP - Status: %s - Body: %s", resp.status, await resp.text())
                        return await resp.json()"""

new_content = content.replace(get_old, get_new).replace(post_old, post_new).replace(put_old, put_new)

if new_content != content:
    with open(file_path, 'w') as f:
        f.write(new_content)
    print("SUCCESS")
else:
    print("ERROR: Match failed")
