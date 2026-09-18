# ISDP Platform Health Check Script
Write-Host "Running ISDP local health check..." -ForegroundColor Cyan

python -c "import urllib.request, json; data = json.loads(urllib.request.urlopen('http://127.0.0.1:8000/health').read().decode('utf-8')); print('API Status:', data['status'], '| Server Time UTC:', data['server_time_utc'])"

Write-Host "Health check completed successfully." -ForegroundColor Green
