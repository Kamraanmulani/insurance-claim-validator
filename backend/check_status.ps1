# Quick Backend Check
Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "   Backend API Status Check" -ForegroundColor Cyan  
Write-Host "============================================`n" -ForegroundColor Cyan

try {
    $api = Invoke-RestMethod http://localhost:5000/
    $health = Invoke-RestMethod http://localhost:5000/health
    
    Write-Host "✓ API: $($api.message)" -ForegroundColor Green
    Write-Host "✓ Version: $($api.version)" -ForegroundColor Green
    Write-Host "✓ Health: $($health.status)" -ForegroundColor Green
    Write-Host "✓ MongoDB: $($health.mongodb)" -ForegroundColor Green
    Write-Host "`n🎉 Backend is running perfectly!" -ForegroundColor Green
    
} catch {
    Write-Host "✗ Backend not responding" -ForegroundColor Red
    Write-Host "  Make sure to run: npm start" -ForegroundColor Yellow
    exit 1
}
