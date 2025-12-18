# Joke Emporium Development Setup Script
# One-command setup for Windows developers
# Usage: .\setup.ps1

param(
    [switch]$SkipPreCommit,
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Joke Emporium Development Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function to check if command exists
function Test-Command {
    param($Command)
    $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
}

# Function to get version
function Get-CommandVersion {
    param($Command, $VersionFlag = "--version")
    try {
        $version = & $Command $VersionFlag 2>&1 | Select-Object -First 1
        return $version
    } catch {
        return "unknown"
    }
}

# Step 1: Check Python
Write-Host "[1/7] Checking Python..." -ForegroundColor Yellow
if (Test-Command python) {
    $pythonVersion = python --version 2>&1
    Write-Host "  Found: $pythonVersion" -ForegroundColor Green

    # Check if version is 3.10+
    $versionMatch = $pythonVersion -match "Python (\d+)\.(\d+)"
    if ($versionMatch) {
        $major = [int]$matches[1]
        $minor = [int]$matches[2]
        if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 10)) {
            Write-Host "  ERROR: Python 3.10+ required, found $pythonVersion" -ForegroundColor Red
            exit 1
        }
    }
} else {
    Write-Host "  ERROR: Python not found!" -ForegroundColor Red
    Write-Host "  Please install Python 3.10+ from https://python.org" -ForegroundColor Red
    exit 1
}

# Step 2: Check/Install uv
Write-Host "[2/7] Checking uv package manager..." -ForegroundColor Yellow
if (Test-Command uv) {
    $uvVersion = Get-CommandVersion uv
    Write-Host "  Found: $uvVersion" -ForegroundColor Green
} else {
    Write-Host "  Installing uv..." -ForegroundColor Yellow
    python -m pip install --upgrade uv
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Installed uv successfully" -ForegroundColor Green
    } else {
        Write-Host "  ERROR: Failed to install uv" -ForegroundColor Red
        exit 1
    }
}

# Step 3: Install dependencies
Write-Host "[3/7] Installing project dependencies..." -ForegroundColor Yellow
uv sync --extra dev --dev
if ($LASTEXITCODE -eq 0) {
    Write-Host "  Dependencies installed successfully" -ForegroundColor Green
} else {
    Write-Host "  ERROR: Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Step 4: Check Git LFS
Write-Host "[4/7] Checking Git LFS..." -ForegroundColor Yellow
if (Test-Command "git-lfs") {
    $lfsVersion = git lfs version
    Write-Host "  Found: $lfsVersion" -ForegroundColor Green

    # Initialize Git LFS
    git lfs install 2>&1 | Out-Null
    Write-Host "  Git LFS initialized" -ForegroundColor Green
} else {
    Write-Host "  WARNING: Git LFS not found" -ForegroundColor Yellow
    Write-Host "  Install from: https://git-lfs.github.com/" -ForegroundColor Yellow
    Write-Host "  (Not critical for basic development)" -ForegroundColor Yellow
}

# Step 5: Install pre-commit hooks
if (-not $SkipPreCommit) {
    Write-Host "[5/7] Installing pre-commit hooks..." -ForegroundColor Yellow
    if (Test-Path ".pre-commit-config.yaml") {
        # Install pre-commit package
        uv pip install pre-commit 2>&1 | Out-Null

        # Install hooks
        uv run pre-commit install 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  Pre-commit hooks installed" -ForegroundColor Green
        } else {
            Write-Host "  WARNING: Failed to install pre-commit hooks" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  Skipping (no .pre-commit-config.yaml found)" -ForegroundColor Yellow
    }
} else {
    Write-Host "[5/7] Skipping pre-commit hooks (--SkipPreCommit flag)" -ForegroundColor Yellow
}

# Step 6: Create data directory
Write-Host "[6/7] Setting up data directories..." -ForegroundColor Yellow
if (-not (Test-Path "data")) {
    New-Item -ItemType Directory -Path "data" | Out-Null
    Write-Host "  Created data/ directory" -ForegroundColor Green
} else {
    Write-Host "  data/ directory exists" -ForegroundColor Green
}

# Step 7: Run tests
if (-not $SkipTests) {
    Write-Host "[7/7] Running test suite..." -ForegroundColor Yellow
    uv run pytest tests/ -v --tb=short
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  All tests passed!" -ForegroundColor Green
    } else {
        Write-Host "  WARNING: Some tests failed" -ForegroundColor Yellow
        Write-Host "  This may be expected if databases are not set up" -ForegroundColor Yellow
    }
} else {
    Write-Host "[7/7] Skipping tests (--SkipTests flag)" -ForegroundColor Yellow
}

# Success!
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Run tests:        task test" -ForegroundColor White
Write-Host "  2. Format code:      task format" -ForegroundColor White
Write-Host "  3. Import sample:    task import:taivop -- --max-records 100" -ForegroundColor White
Write-Host "  4. View commands:    task --list" -ForegroundColor White
Write-Host ""
Write-Host "Documentation:" -ForegroundColor Cyan
Write-Host "  - Project overview:  CLAUDE.md" -ForegroundColor White
Write-Host "  - Quick start:       README.md" -ForegroundColor White
Write-Host "  - DX analysis:       DX_ANALYSIS.md" -ForegroundColor White
Write-Host ""
Write-Host "Happy coding!" -ForegroundColor Green
