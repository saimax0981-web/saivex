Write-Host "SAIVEX Production Steps 2-5 Apply Script" -ForegroundColor Yellow

$root = "D:\saivex"
Set-Location $root

if (!(Test-Path "legacy_app.py")) {
    if (Test-Path "app.py") {
        Copy-Item "app.py" "legacy_app.py"
        Write-Host "Created legacy_app.py backup from current app.py" -ForegroundColor Green
    } else {
        Write-Host "app.py missing." -ForegroundColor Red
        exit
    }
} else {
    Write-Host "legacy_app.py already exists. Keeping it." -ForegroundColor Cyan
}

Write-Host ""
Write-Host "Now copy all files from the extracted production pack into D:\saivex." -ForegroundColor Cyan
Write-Host "Then run:" -ForegroundColor Yellow
Write-Host "py -m pip install -r requirements.txt"
Write-Host "py app.py"
