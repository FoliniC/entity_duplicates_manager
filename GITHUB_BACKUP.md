# GitHub Backup System - Home Assistant

This repository is automatically backed up to GitHub using a system based on a **Systemd Timer** and a custom Bash script.

## System Components

### 1. Backup Script
*   **Path**: `/usr/local/bin/ha_gh_backup`
*   **Description**: The script manages the entire backup lifecycle:
    *   Repository status check (modified files, pending commits).
    *   Automatic addition of new files (respecting `.gitignore`).
    *   Commit creation with timestamp.
    *   Push to GitHub using SSH authentication.
*   **Authentication**: Uses the root user's SSH key located at `/root/.ssh/id_rsa`.

### 2. Automation (Systemd)
The backup is scheduled through two systemd units:

*   **Timer**: `ha-gh-backup.timer`
    *   Controls the execution frequency (currently configured to run periodically).
    *   Status: `systemctl status ha-gh-backup.timer`
*   **Service**: `ha-gh-backup.service`
    *   Executes the script as the root user.
    *   Status: `systemctl status ha-gh-backup.service`

## Useful Commands

### Check Logs
To check the results of the latest backups:
```bash
sudo journalctl -u ha-gh-backup.service -n 50 --no-pager
```

### Run Manual Backup
You can force an immediate backup execution without waiting for the timer:
```bash
sudo systemctl start ha-gh-backup.service
```

### Verify GitHub Authentication
To test if the SSH key is still valid:
```bash
sudo ssh -T git@github.com
```

## Script Structure
The script is divided into phases:
- **PHASE 0**: Repository analysis (diff, log).
- **PHASE 1**: `git add .` (if there are unstaged changes).
- **PHASE 2**: `git commit` with message "Backup YYYY-MM-DD HH:MM".
- **PHASE 3**: `git push` with detailed network operation logs.

## Maintenance Notes
In case of error "128" during push, there might be a remote conflict. In this case, you might need to manually run `git pull` or, if you are sure of your local version, a `git push --force-with-lease origin main` from the `/home/carlo/docker/homeassistant/config` folder.
