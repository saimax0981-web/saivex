Write-Host "SAIVEX v1.0 Modularization Step 1" -ForegroundColor Yellow

$root = "D:\saivex"
Set-Location $root

if (!(Test-Path "app.py")) {
    Write-Host "app.py not found in D:\saivex" -ForegroundColor Red
    exit
}

if (!(Test-Path "legacy_app.py")) {
    Copy-Item "app.py" "legacy_app.py"
    Write-Host "Backed up current app.py as legacy_app.py" -ForegroundColor Green
} else {
    Write-Host "legacy_app.py already exists. Not overwriting." -ForegroundColor Cyan
}

Write-Host "Now copy the new app.py, config.py, extensions.py, models.py, routes/, utils/ into D:\saivex" -ForegroundColor Cyan
Write-Host "After copying, run: py app.py" -ForegroundColor Yellow
