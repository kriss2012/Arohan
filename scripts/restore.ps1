param (
    [Parameter(Mandatory=$true)]
    [string]$BackupFilename
)

Write-Host "Restoring from local backup: $BackupFilename..." -ForegroundColor Cyan

python -c "import sys; from backend.app.services.backup_service import BackupService; res = BackupService.verify_and_restore_backup('$BackupFilename'); print('Restore Complete. Files restored:', res['restored_files_count'])"

Write-Host "Database and file storage successfully restored." -ForegroundColor Green
