# Interventi Disco /dev/sdb (111.8 GB) - 2026-08-25/26

## Obiettivo
Liberare spazio dal disco principale (/dev/sda1, 230G al 99% → 80%) spostando backup, log, media telecamere, DB su nuovo disco.

---

## 1. Formattazione e Mount
```bash
sudo mkfs.ext4 -L ha_storage /dev/sdb
sudo mkdir -p /mnt/ha_storage
sudo mount /dev/sdb /mnt/ha_storage
sudo chown -R 1000:1000 /mnt/ha_storage
mkdir -p /mnt/ha_storage/{backups,logs,agentdvr/media,mariadb,influxdb}
```

## 2. Spostamento Dati (con container fermi)
```bash
docker compose stop homeassistant mariadb influxdb agentdvr

sudo mv /home/carlo/docker/homeassistant/config/backups /mnt/ha_storage/
sudo mv /home/carlo/docker/homeassistant/config/logs /mnt/ha_storage/
sudo mv /home/carlo/docker/agentdvr/media /mnt/ha_storage/agentdvr/
sudo mv /home/carlo/docker/mariadb/db /mnt/ha_storage/mariadb/
sudo mv /home/carlo/docker/influxdb/data /mnt/ha_storage/influxdb/
```

## 3. Symlink per Compatibilità (no nested dirs)
```bash
# Fix nesting creato dal mv
sudo mv /mnt/ha_storage/logs/logs/* /mnt/ha_storage/logs/
sudo rmdir /mnt/ha_storage/logs/logs
sudo mv /mnt/ha_storage/backups/backups/* /mnt/ha_storage/backups/
sudo rmdir /mnt/ha_storage/backups/backups

# Symlink
sudo ln -sfn /mnt/ha_storage/backups /home/carlo/docker/homeassistant/config/backups
sudo ln -sfn /mnt/ha_storage/logs /home/carlo/docker/homeassistant/config/logs
```

## 4. Aggiornamento docker-compose.yml
```yaml
mariadb:
  volumes:
    - /mnt/ha_storage/mariadb/db:/var/lib/mysql

influxdb:
  volumes:
    - /media/carlo/ha_storage/influxdb/data:/var/lib/influxdb2  # PATH CORRETTO

agentdvr:
  volumes:
    - /mnt/ha_storage/agentdvr/media:/media

samba:
  volumes:
    - /mnt/ha_storage:/storage
```

## 5. Fix Permessi Directory Log Mancanti
```bash
sudo mkdir -p /mnt/ha_storage/logs/usb_tether
sudo chmod 777 /mnt/ha_storage/logs/usb_tether
```

## 6. Fix InfluxDB Auth (Token 401 Unauthorized)
Il container InfluxDB usava dati su `/media/carlo/ha_storage/influxdb/data` (non `/mnt/ha_storage`).

**Problema**: token in `secrets.yaml` non valido per il DB esistente.

**Soluzione**:
```bash
# Crea nuovo token all-access
docker exec influxdb influx auth create --user admin --org ViaGrande50 --all-access --description "HA token"
# Output: FxqV-ZO2nTKkxifYVuKBrFC5JArG4e8qi0y-c8L_eAOYsTmYmy7ar4iiMmnkVmN2m39JeIGeRycT3aSKVYcT5g==

# Aggiorna secrets.yaml
influxdb_token: FxqV-ZO2nTKkxifYVuKBrFC5JArG4e8qi0y-c8L_eAOYsTmYmy7ar4iiMmnkVmN2m39JeIGeRycT3aSKVYcT5g==

docker restart homeassistant
```

---

## Risultato
| Filesystem | Prima | Dopo |
|------------|-------|------|
| / (sda1)   | 215G/230G (99%) | 174G/230G (80%) ✓ |
| /mnt/ha_storage (sdb) | — | 38G/110G (37%) |

## Container Riavviati
- `homeassistant` ✓
- `mariadb` ✓
- `influxdb` ✓ (su path corretto `/media/carlo/ha_storage/...`)
- `agentdvr` ✓ (in pull)

## ⚠️ Prerequisito Obbligatorio: Backup Prima di Ripetere
**Prima di ripetere questa procedura, effettuare backup completo di:**
- `/home/carlo/docker/homeassistant/config/backups/` (tutti i .tar)
- `/home/carlo/docker/homeassistant/config/logs/` (tutti i log)
- `/home/carlo/docker/mariadb/db/` (database MariaDB)
- `/home/carlo/docker/influxdb/data/` **O** `/media/carlo/ha_storage/influxdb/data/` (verificare con `docker inspect influxdb`)
- `/home/carlo/docker/agentdvr/media/` (registrazioni telecamere)
- `/home/carlo/docker/homeassistant/config/secrets.yaml` (token InfluxDB)
- `docker-compose.yml` (versione corrente)

```bash
# Esempio backup rapido
tar -czf /backup/pre-migration-$(date +%F).tar.gz \
  /home/carlo/docker/homeassistant/config/backups \
  /home/carlo/docker/homeassistant/config/logs \
  /home/carlo/docker/mariadb/db \
  /home/carlo/docker/influxdb/data \
  /home/carlo/docker/agentdvr/media \
  /home/carlo/docker/homeassistant/config/secrets.yaml \
  /home/carlo/docker/docker-compose.yml
```

## Note per Futuro
- InfluxDB data **NON** era in `/mnt/ha_storage/influxdb` ma in `/media/carlo/ha_storage/influxdb` — verificare sempre `docker inspect influxdb` per il mount reale
- I token InfluxDB v2 **non scadono** ma vanno rigenerati se il setup iniziale li sovrascrive
- Symlink dentro `/config` funzionano per tutti i container che montano `./homeassistant/config:/config`
- Evitare nested dirs: `mv src/* dst/` poi `rmdir src`