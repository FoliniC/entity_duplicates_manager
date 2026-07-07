# Host Backup

Questa directory contiene snapshot generati dello stato Docker host che vive
fuori dal repository Home Assistant.

`ha_gh_backup_final.sh` copia `/home/carlo/docker/docker-compose.yml` in
`host_backup/docker-compose.yml` prima del commit GitHub, rimuovendo token e
password note.

Per ripristini completi servono comunque i segreti originali, per esempio il
token Cloudflare Tunnel recuperabile da Cloudflare Zero Trust.
