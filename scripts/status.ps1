# PowerShell status script for Copy/Paste project
# Shows backend health, frontend URL, and Docker container status

Write-Host ""
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "🎯 SYSTEM STATUS" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Backend health check
Write-Host "✅ Backend: http://localhost:8000" -ForegroundColor Green
try {
    $healthResponse = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get -TimeoutSec 2 -ErrorAction Stop
    Write-Host "   Health: $($healthResponse.status)" -ForegroundColor Green
} catch {
    Write-Host "   Health: ❌ Unreachable" -ForegroundColor Red
}

# Backend ready check
try {
    $readyResponse = Invoke-RestMethod -Uri "http://localhost:8000/ready" -Method Get -TimeoutSec 2 -ErrorAction Stop
    Write-Host "   Ready: $($readyResponse.status)" -ForegroundColor Green
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    if ($statusCode -eq 503) {
        Write-Host "   Ready: ⚠️  DB not ready (503)" -ForegroundColor Yellow
    } else {
        Write-Host "   Ready: ❌ Error ($statusCode)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "✅ Frontend: http://localhost:5174" -ForegroundColor Green
Write-Host "   (Öppna i webbläsare för att se UI:n)" -ForegroundColor Gray
Write-Host ""

# Docker container status
Write-Host "📋 Docker Containers:" -ForegroundColor Cyan
$containers = docker ps --filter "name=copy-paste" --format "table {{.Names}}\t{{.Status}}" 2>$null
if ($containers) {
    Write-Host $containers
} else {
    Write-Host "   No containers running" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🔗 Öppna frontend: http://localhost:5174" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

