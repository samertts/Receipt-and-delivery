# Backup and Recovery Guide

## Overview

The system provides comprehensive backup and recovery capabilities for both the desktop application and web backend.

## Desktop Application Backups

### Location

Backups are stored in:
- Windows: `%LOCALAPPDATA%/LabReceiptSystem/database/backups/`
- Linux: `~/Documents/LabReceiptSystem/database/backups/`

### Creating Backups

#### Manual Backup

1. Navigate to Backup page
2. Click "Create Backup"
3. Backup file is created with timestamp

#### Automated Backup

Enable in Settings:
1. Go to Settings page
2. Set `backup.auto_enabled` to `true`
3. Configure `backup.path` for custom location
4. Set `backup.retention_max` for maximum backups

### Backup Format

Backups are SQLite database files with naming format:
```
backup_YYYYMMDD_HHMMSS.db
```

### Verifying Backups

1. Navigate to Backup page
2. Click "Verify" on a backup
3. System checks:
   - File integrity (SQLite PRAGMA integrity_check)
   - WAL mode status
   - Table existence
   - Index existence

### Restoring Backups

1. Navigate to Backup page
2. Click "Restore" on desired backup
3. Confirm restoration
4. Application restarts with restored data

**Warning:** Restoration replaces the current database entirely.

## Web Backend Backups

### PostgreSQL Backup

```bash
# Create backup
pg_dump -U lab_user -d lab_txn > backup_$(date +%Y%m%d).sql

# Restore backup
psql -U lab_user -d lab_txn < backup_YYYYMMDD.sql
```

### Docker Backup

```bash
# Backup volume
docker run --rm -v pgdata:/data -v $(pwd):/backup alpine \
  tar czf /backup/pgdata_backup_$(date +%Y%m%d).tar.gz -C /data .

# Restore volume
docker run --rm -v pgdata:/data -v $(pwd):/backup alpine \
  tar xzf /backup/pgdata_backup_YYYYMMDD.tar.gz -C /data
```

## Recovery Procedures

### Database Corruption

1. Run startup diagnostics (automatic)
2. If corruption detected:
   a. Navigate to Backup page
   b. Find most recent valid backup
   c. Click "Restore"
   d. Verify data integrity

### Accidental Data Loss

1. Stop the application immediately
2. Locate backup before the loss
3. Restore from backup
4. Verify data
5. Re-enter any lost transactions

### System Failure

1. Reinstall application if needed
2. Copy backup file to backup directory
3. Restore from backup
4. Verify all data

## Backup Retention Policy

### Default Settings

| Setting | Value |
|---------|-------|
| Auto-backup | Disabled |
| Retention max | 30 backups |
| Backup path | Default storage |

### Recommended Settings

| Environment | Retention | Frequency |
|-------------|-----------|-----------|
| Development | 7 days | Daily |
| Staging | 14 days | Daily |
| Production | 30 days | Daily |

## Monitoring Backup Health

### Dashboard Indicators

- Green: All backups valid
- Yellow: Some backups invalid
- Red: No backups or all invalid

### Manual Verification

```python
from lab_system.app.services.recovery_service import verify_backup, list_backups

# List all backups
backups = list_backups()

# Verify each
for b in backups:
    result = verify_backup(b["path"])
    print(f"{b['path']}: {'Valid' if result['valid'] else 'Invalid'}")
```

## Best Practices

1. **Regular Backups:** Enable automated backups
2. **Verify Backups:** Regularly verify backup integrity
3. **Offsite Storage:** Copy backups to external storage
4. **Test Restoration:** Periodically test backup restoration
5. **Monitor Retention:** Ensure old backups are cleaned up
6. **Document Procedures:** Keep recovery procedures documented

## Troubleshooting

### Backup Creation Fails

1. Check disk space
2. Verify write permissions
3. Check database is not locked

### Restore Fails

1. Verify backup file integrity
2. Check disk space
3. Ensure no other process is using the database
4. Check file permissions

### Backup Verification Fails

1. Check SQLite version compatibility
2. Verify backup file is not corrupted
3. Check for incomplete backups
