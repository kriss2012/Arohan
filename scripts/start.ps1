# ISDP Local Campus Start Script
Write-Host "Starting ISDP Local Services..." -ForegroundColor Cyan

# Start Backend API Server
Start-Process -FilePath "python" -ArgumentList "-m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000" -WindowStyle Hidden
Write-Host "Backend API Server started at http://127.0.0.1:8000" -ForegroundColor Green

# Start Frontend App
Push-Location frontend
Start-Process -FilePath "cmd.exe" -ArgumentList "/c npm run dev -- --host 127.0.0.1 --port 5173" -WindowStyle Hidden
Pop-Location
Write-Host "Frontend Application started at http://127.0.0.1:5173" -ForegroundColor Green
Write-Host "`nAll services active. Open your browser or Tauri desktop shell to begin." -ForegroundColor Yellow
