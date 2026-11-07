#!/bin/bash
# Ensure /config/backup symlink points to /backup (mounted from /ha-data/backups)
if [ ! -L /config/backup ]; then
    ln -s /backup /config/backup
fi