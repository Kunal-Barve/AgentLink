#!/bin/bash
# ============================================================
# Weekly Backup Script: n8n + Supabase on Hostinger VPS
# Location on server: /root/backup-n8n-supabase.sh
# Cron: runs every Sunday at 2:00 AM UTC
# ============================================================

set -e

BACKUP_DIR="/root/backups"
DATE=$(date +%Y-%m-%d_%H-%M-%S)
N8N_BACKUP_DIR="$BACKUP_DIR/n8n"
SUPABASE_BACKUP_DIR="$BACKUP_DIR/supabase"
LOG_FILE="$BACKUP_DIR/backup.log"
KEEP_DAYS=30  # Keep backups for 30 days (4 weekly backups)

# ── Logging helper ──────────────────────────────────────────
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# ── Setup directories ────────────────────────────────────────
mkdir -p "$N8N_BACKUP_DIR" "$SUPABASE_BACKUP_DIR"

log "======================================================"
log "Starting backup: $DATE"
log "======================================================"

# ── 1. BACKUP N8N ────────────────────────────────────────────
log "📦 Backing up n8n data volume..."

N8N_FILE="$N8N_BACKUP_DIR/n8n_backup_$DATE.tar.gz"

docker run --rm \
    -v n8n_data:/data \
    -v "$N8N_BACKUP_DIR":/backup \
    alpine \
    tar czf "/backup/n8n_backup_$DATE.tar.gz" -C /data .

if [ -f "$N8N_FILE" ]; then
    SIZE=$(du -sh "$N8N_FILE" | cut -f1)
    log "✅ n8n backup complete: n8n_backup_$DATE.tar.gz ($SIZE)"
else
    log "❌ n8n backup FAILED"
    exit 1
fi

# ── 2. BACKUP SUPABASE POSTGRES ──────────────────────────────
log "📦 Backing up Supabase PostgreSQL database..."

SUPABASE_DB_FILE="$SUPABASE_BACKUP_DIR/supabase_db_$DATE.sql.gz"

# Get the postgres container name
PG_CONTAINER=$(docker ps --format '{{.Names}}' | grep 'supabase-db' | head -1)

if [ -z "$PG_CONTAINER" ]; then
    log "❌ Supabase DB container not found"
    exit 1
fi

docker exec "$PG_CONTAINER" \
    pg_dumpall -U postgres \
    | gzip > "$SUPABASE_DB_FILE"

if [ -f "$SUPABASE_DB_FILE" ]; then
    SIZE=$(du -sh "$SUPABASE_DB_FILE" | cut -f1)
    log "✅ Supabase DB backup complete: supabase_db_$DATE.sql.gz ($SIZE)"
else
    log "❌ Supabase DB backup FAILED"
    exit 1
fi

# ── 3. BACKUP SUPABASE STORAGE VOLUME ───────────────────────
log "📦 Backing up Supabase storage volume..."

SUPABASE_STORAGE_FILE="$SUPABASE_BACKUP_DIR/supabase_storage_$DATE.tar.gz"

# Backup the supabase volumes directory
tar czf "$SUPABASE_STORAGE_FILE" -C /root/supabase-app/volumes . 2>/dev/null || true

if [ -f "$SUPABASE_STORAGE_FILE" ]; then
    SIZE=$(du -sh "$SUPABASE_STORAGE_FILE" | cut -f1)
    log "✅ Supabase storage backup complete: supabase_storage_$DATE.tar.gz ($SIZE)"
else
    log "⚠️  Supabase storage backup skipped (no volumes dir)"
fi

# ── 4. BACKUP DOCKER COMPOSE CONFIGS ────────────────────────
log "📦 Backing up Docker Compose configs..."

CONFIG_FILE="$BACKUP_DIR/configs_$DATE.tar.gz"

tar czf "$CONFIG_FILE" \
    /root/docker-compose.yml \
    /root/supabase-app/docker-compose.yml \
    2>/dev/null || true

log "✅ Config backup complete: configs_$DATE.tar.gz"

# ── 5. CLEANUP OLD BACKUPS ───────────────────────────────────
log "🧹 Cleaning up backups older than $KEEP_DAYS days..."

find "$N8N_BACKUP_DIR" -name "*.tar.gz" -mtime +$KEEP_DAYS -delete
find "$SUPABASE_BACKUP_DIR" -name "*.sql.gz" -mtime +$KEEP_DAYS -delete
find "$SUPABASE_BACKUP_DIR" -name "*.tar.gz" -mtime +$KEEP_DAYS -delete
find "$BACKUP_DIR" -name "configs_*.tar.gz" -mtime +$KEEP_DAYS -delete

log "✅ Cleanup complete"

# ── 6. SUMMARY ───────────────────────────────────────────────
log "======================================================"
log "✅ Backup completed successfully: $DATE"
log "📁 Backup location: $BACKUP_DIR"
log "💾 Disk usage:"
du -sh "$BACKUP_DIR" 2>/dev/null | tee -a "$LOG_FILE"
log "======================================================"
