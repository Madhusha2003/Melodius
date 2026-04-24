# Melodius Build Script (Windows - Nuitka)
# This script prepares the production build and compiles it into a standalone EXE.

Write-Host "--- Step 1: Exporting Production Frontend ---" -ForegroundColor Cyan
Set-Location frontend
reflex export --frontend-only --no-zip
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Reflex export failed!" -ForegroundColor Red
    exit $LASTEXITCODE
}
Set-Location ..

Write-Host "--- Step 2: Compiling with Nuitka ---" -ForegroundColor Cyan
# We use main_desktop.py as it is the unified runner (FastAPI + Reflex API in one process)
# --lto=yes: Enables Link Time Optimization for a smaller and faster binary
python -m nuitka `
    --standalone `
    --onefile `
    --windows-disable-console `
    --enable-plugin=tk-inter `
    --follow-imports `
    --lto=yes `
    --include-data-dir=backend=backend `
    --include-data-dir=frontend=frontend `
    --include-data-dir=frontend/.web/build/client=frontend/.web/build/client `
    --output-dir=dist `
    --output-filename=Melodius `
    main_desktop.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Nuitka compilation failed!" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "--- Build Complete! ---" -ForegroundColor Green
Write-Host "Your executable is located at: dist/Melodius.exe" -ForegroundColor Yellow
