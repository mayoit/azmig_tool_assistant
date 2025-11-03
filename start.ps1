# Azure Migration Tool - Docker Compose Quick Start
# PowerShell script to start the application

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Azure Migration Tool - Docker Setup" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
Write-Host "Checking Docker..." -ForegroundColor Yellow
try {
    docker info > $null 2>&1
    Write-Host "✓ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env file from template..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "✓ .env file created. Please edit it with your settings." -ForegroundColor Green
    Write-Host ""
    Write-Host "IMPORTANT: Update these values in .env:" -ForegroundColor Yellow
    Write-Host "  - DB_PASSWORD" -ForegroundColor White
    Write-Host "  - REDIS_PASSWORD" -ForegroundColor White
    Write-Host "  - SECRET_KEY" -ForegroundColor White
    Write-Host ""
    $continue = Read-Host "Press Enter to continue or Ctrl+C to exit"
}

# Start Docker Compose
Write-Host ""
Write-Host "Starting services..." -ForegroundColor Yellow
docker-compose up -d

# Wait for services to be healthy
Write-Host ""
Write-Host "Waiting for services to be healthy..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check service status
Write-Host ""
Write-Host "Service Status:" -ForegroundColor Cyan
docker-compose ps

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Services are starting!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Access the application at:" -ForegroundColor Yellow
Write-Host "  • API Documentation: " -NoNewline -ForegroundColor White
Write-Host "http://localhost:8000/api/docs" -ForegroundColor Cyan
Write-Host "  • API Health Check:  " -NoNewline -ForegroundColor White
Write-Host "http://localhost:8000/health" -ForegroundColor Cyan
Write-Host "  • Frontend (Vue.js): " -NoNewline -ForegroundColor White
Write-Host "http://localhost:5173" -ForegroundColor Cyan
Write-Host ""
Write-Host "View logs:" -ForegroundColor Yellow
Write-Host "  docker-compose logs -f" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Create database migration:" -ForegroundColor White
Write-Host "     docker-compose exec api alembic revision --autogenerate -m ""Initial schema""" -ForegroundColor Gray
Write-Host "  2. Apply migration:" -ForegroundColor White
Write-Host "     docker-compose exec api alembic upgrade head" -ForegroundColor Gray
Write-Host ""
