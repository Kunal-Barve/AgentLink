# Hostinger VPS: n8n & Supabase Backup and Update Guide

## Server Details

| Item | Value |
|------|-------|
| **Server IP** | `72.62.64.72` |
| **SSH Key** | `D:\Articflow\ssh-keys\agentlink-hostinger-n8n` |
| **SSH Command** | `ssh -i D:\Articflow\ssh-keys\agentlink-hostinger-n8n root@72.62.64.72` |
| **n8n compose file** | `/root/docker-compose.yml` |
| **Supabase compose file** | `/root/supabase-app/docker-compose.yml` |
| **n8n data volume** | `n8n_data` (Docker named volume) |
| **Backup script** | `/root/backup-n8n-supabase.sh` |
| **Backup location** | `/root/backups/` |
| **Backup log** | `/root/backups/backup.log` |

---

## What's Running on the Server

- **n8n** — container `root-n8n-1`, image `docker.n8n.io/n8nio/n8n`, port `127.0.0.1:5678`
- **Traefik** — reverse proxy with SSL (Let's Encrypt)
- **Supabase** — full self-hosted stack (`supabase-db`, `supabase-studio`, `supabase-auth`, `supabase-rest`, `supabase-storage`, etc.)

---

## Backup Script

The backup script is located at `/root/backup-n8n-supabase.sh` on the server and also stored locally at `docs/backup-n8n-supabase.sh`.

### What it backs up

| Item | Method | Output |
|------|--------|--------|
| n8n workflows & credentials | Docker volume tar | `n8n_backup_YYYY-MM-DD_HH-MM-SS.tar.gz` |
| Supabase PostgreSQL database | `pg_dumpall` | `supabase_db_YYYY-MM-DD_HH-MM-SS.sql.gz` |
| Supabase storage volumes | Directory tar | `supabase_storage_YYYY-MM-DD_HH-MM-SS.tar.gz` |
| Docker Compose configs | File tar | `configs_YYYY-MM-DD_HH-MM-SS.tar.gz` |

### Retention policy
- Backups older than **30 days** are automatically deleted
- This keeps approximately **4 weekly backups** at any time

### Automated schedule
The script runs automatically every **Sunday at 2:00 AM UTC** via cron:
```
0 2 * * 0 /root/backup-n8n-supabase.sh >> /root/backups/backup.log 2>&1
```

---

## How to Run a Manual Backup

```bash
# SSH into the server
ssh -i D:\Articflow\ssh-keys\agentlink-hostinger-n8n root@72.62.64.72

# Run the backup script
bash /root/backup-n8n-supabase.sh

# Check the log
cat /root/backups/backup.log

# Check backup files and sizes
du -sh /root/backups/
ls -lh /root/backups/n8n/
ls -lh /root/backups/supabase/
```

---

## How to Update n8n

> **Always run a backup before updating.**

### Step 1: SSH into the server
```bash
ssh -i D:\Articflow\ssh-keys\agentlink-hostinger-n8n root@72.62.64.72
```

### Step 2: Run a backup
```bash
bash /root/backup-n8n-supabase.sh
```

### Step 3: Pull the latest n8n image
```bash
cd /root
docker compose pull n8n
```

### Step 4: Restart only the n8n container (Supabase stays running)
```bash
docker compose stop n8n
docker compose rm -f n8n
docker compose up -d n8n
```

### Step 5: Verify n8n is running and check the version
```bash
docker ps | grep n8n
docker exec root-n8n-1 n8n --version
```

> **Note:** Do NOT run `docker compose down` as that will stop Supabase too. Always stop/start only the `n8n` service.

---

## How to Update Supabase

> Supabase updates are more complex. Only update if there is a specific reason (security patch, required feature).

### Step 1: SSH into the server and run a backup
```bash
ssh -i D:\Articflow\ssh-keys\agentlink-hostinger-n8n root@72.62.64.72
bash /root/backup-n8n-supabase.sh
```

### Step 2: Pull updated Supabase images
```bash
cd /root/supabase-app
docker compose pull
```

### Step 3: Restart Supabase services
```bash
docker compose down
docker compose up -d
```

### Step 4: Verify all services are healthy
```bash
docker ps --format 'table {{.Names}}\t{{.Status}}'
```

All Supabase containers should show `(healthy)`.

---

## How to Restore from Backup

### Restore n8n data volume
```bash
# Stop n8n first
cd /root && docker compose stop n8n

# Restore the volume from backup (replace filename with the backup you want)
docker run --rm \
    -v n8n_data:/data \
    -v /root/backups/n8n:/backup \
    alpine \
    tar xzf /backup/n8n_backup_YYYY-MM-DD_HH-MM-SS.tar.gz -C /data

# Start n8n again
docker compose up -d n8n
```

### Restore Supabase database
```bash
# Get the postgres container name
PG_CONTAINER=$(docker ps --format '{{.Names}}' | grep 'supabase-db')

# Restore from SQL dump (replace filename with the backup you want)
gunzip -c /root/backups/supabase/supabase_db_YYYY-MM-DD_HH-MM-SS.sql.gz \
    | docker exec -i $PG_CONTAINER psql -U postgres
```

---

## How to Update the Backup Script

If you need to modify the backup script (e.g., change retention period, add new services):

### Option 1: Edit directly on the server
```bash
ssh -i D:\Articflow\ssh-keys\agentlink-hostinger-n8n root@72.62.64.72
nano /root/backup-n8n-supabase.sh
```

### Option 2: Edit locally and re-upload
1. Edit `docs/backup-n8n-supabase.sh` in the local repo
2. Upload to server:
```bash
scp -i "D:\Articflow\ssh-keys\agentlink-hostinger-n8n" "docs\backup-n8n-supabase.sh" root@72.62.64.72:/root/backup-n8n-supabase.sh
```

### Key variables in the script
```bash
BACKUP_DIR="/root/backups"   # Where backups are stored
KEEP_DAYS=30                  # How many days to keep backups
```

---

## How to Change the Cron Schedule

```bash
# Edit cron jobs
crontab -e

# Current schedule (every Sunday at 2:00 AM UTC):
0 2 * * 0 /root/backup-n8n-supabase.sh >> /root/backups/backup.log 2>&1

# Example: Run every day at 3:00 AM UTC:
0 3 * * * /root/backup-n8n-supabase.sh >> /root/backups/backup.log 2>&1

# View current cron jobs
crontab -l
```

---

## Quick Reference Commands

```bash
# Check all running containers
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}'

# Check disk usage
df -h /

# Check backup sizes
du -sh /root/backups/

# View backup log
tail -50 /root/backups/backup.log

# Check n8n version
docker exec root-n8n-1 n8n --version

# Check n8n logs
docker logs root-n8n-1 --tail 50
```
