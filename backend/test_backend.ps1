# Backend API Test Script (PowerShell)

Write-Host "Testing Backend API" -ForegroundColor Cyan
Write-Host "===================" -ForegroundColor Cyan

# Health check
Write-Host "`n1. Health Check:" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:5000/health" -Method Get
    $response | ConvertTo-Json
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
}

# Register user
Write-Host "`n2. Register Assessor:" -ForegroundColor Yellow
try {
    $body = @{
        email = "assessor@example.com"
        password = "password123"
        name = "Test Assessor"
        role = "ASSESSOR"
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri "http://localhost:5000/api/auth/register" `
        -Method Post `
        -Body $body `
        -ContentType "application/json"
    $response | ConvertTo-Json
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
}

# Get claims statistics
Write-Host "`n3. Get Statistics:" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:5000/api/claims/stats/summary" -Method Get
    $response | ConvertTo-Json
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
}

Write-Host "`n✅ Backend API tests complete!" -ForegroundColor Green
