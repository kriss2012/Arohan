# ISDP Setup and Database Initialization Script
Write-Host "Initializing local database schema and seed data..." -ForegroundColor Cyan

python -c "import asyncio; from backend.app.main import app, lifespan; asyncio.run(lifespan(app).__aenter__()); print('Local database initialized and seeded successfully!')"

Write-Host "Setup finished. Database is ready for offline operation." -ForegroundColor Green
