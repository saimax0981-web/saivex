Write-Host "SAIVEX v1.0 Production Cleanup" -ForegroundColor Yellow
Write-Host "This will remove temporary files only." -ForegroundColor Cyan

$root = "D:\saivex"

if (!(Test-Path $root)) {
    Write-Host "D:\saivex not found." -ForegroundColor Red
    exit
}

Set-Location $root

$itemsToRemove = @(
    "__pycache__",
    "voice.wav",
    "image_test.py",
    "memory_test.py",
    "speak_test.py",
    "test.py",
    "voice_test.py",
    "web_test.py",
    "phase6_requirements.txt",
    "phase9_requirements.txt",
    "stage3_requirements.txt",
    "requirements_phase14.txt",
    "requirements_phase14_1.txt",
    "requirements_phase14_2.txt",
    "requirements_phase15.txt",
    "requirements_production.txt",
    "requirements_v1.txt"
)

foreach ($item in $itemsToRemove) {
    if (Test-Path $item) {
        Remove-Item $item -Recurse -Force
        Write-Host "Removed $item" -ForegroundColor Green
    }
}

if (Test-Path "static\generated") {
    Remove-Item "static\generated\*" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "Cleaned static\generated" -ForegroundColor Green
} else {
    New-Item -ItemType Directory -Path "static\generated" | Out-Null
}

if (Test-Path "uploads") {
    Remove-Item "uploads\*" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "Cleaned uploads" -ForegroundColor Green
} else {
    New-Item -ItemType Directory -Path "uploads" | Out-Null
}

if (!(Test-Path "instance")) {
    New-Item -ItemType Directory -Path "instance" | Out-Null
}

Write-Host ""
Write-Host "Cleanup complete." -ForegroundColor Yellow
Write-Host "Next: run py app.py and test SAIVEX." -ForegroundColor Cyan
