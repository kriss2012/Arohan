# ISDP Local Backup Creation Script
Write-Host "Triggering local offline backup..." -ForegroundColor Cyan

python -c "from backend.app.services.backup_service import BackupService; report = BackupService.create_backup(); print('Backup Created Successfully:', report['filename'], 'Size:', report['size_bytes'], 'bytes')"

Write-Host "Local backup saved to ./local_storage/backups/" -ForegroundColor Green
