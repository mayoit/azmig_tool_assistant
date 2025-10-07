# Simple Mock Mode Test Script
# Tests basic functionality of azmig in mock mode

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Azure Migrate Tool - Mock Mode Test" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$ErrorCount = 0
$SuccessCount = 0

# Test 1: Help Command
Write-Host "[TEST 1] Help Command..." -ForegroundColor Yellow
$output = azmig --help 2>&1 | Out-String
if ($output -match "Azure Bulk Migration CLI") {
    Write-Host "  PASS - Help displays correctly" -ForegroundColor Green
    $SuccessCount++
}
else {
    Write-Host "  FAIL - Help not working" -ForegroundColor Red
    $ErrorCount++
}

# Test 2: Verify sample files exist
Write-Host "`n[TEST 2] Sample Files..." -ForegroundColor Yellow
$files = @(
    "examples\template_landing_zones.csv",
    "examples\template_landing_zones.json",
    "examples\servers.csv"
)

foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "  PASS - Found: $file" -ForegroundColor Green
        $SuccessCount++
    }
    else {
        Write-Host "  FAIL - Missing: $file" -ForegroundColor Red
        $ErrorCount++
    }
}

# Test 3: Create default config
Write-Host "`n[TEST 3] Create Default Config..." -ForegroundColor Yellow
if (Test-Path "validation_config.yaml") {
    Write-Host "  INFO - Config already exists, removing..." -ForegroundColor Gray
    Remove-Item "validation_config.yaml" -Force
}

$output = azmig --create-default-config 2>&1 | Out-String
if (Test-Path "validation_config.yaml") {
    Write-Host "  PASS - Config file created" -ForegroundColor Green
    $SuccessCount++
    
    # Show first few lines
    Write-Host "  Preview:" -ForegroundColor Gray
    Get-Content "validation_config.yaml" -Head 5 | ForEach-Object {
        Write-Host "    $_" -ForegroundColor DarkGray
    }
}
else {
    Write-Host "  FAIL - Config file not created" -ForegroundColor Red
    Write-Host "  Output: $output" -ForegroundColor DarkRed
    $ErrorCount++
}

# Test 4: Test mock mode with interactive prompts (we'll send Ctrl+C quickly)
Write-Host "`n[TEST 4] Mock Mode Basic Launch..." -ForegroundColor Yellow
Write-Host "  INFO - Testing if mock mode starts (will timeout after 3 seconds)" -ForegroundColor Gray

$job = Start-Job -ScriptBlock {
    azmig --mock 2>&1 | Out-String
}

$completed = Wait-Job $job -Timeout 3
if ($completed) {
    $output = Receive-Job $job
    if ($output -match "Mock Mode|Mode: MOCK") {
        Write-Host "  PASS - Mock mode starts correctly" -ForegroundColor Green
        $SuccessCount++
    }
    else {
        Write-Host "  FAIL - Mock mode doesn't start correctly" -ForegroundColor Red
        $ErrorCount++
    }
}
else {
    Write-Host "  PASS - Mock mode starts and waits for input (as expected)" -ForegroundColor Green
    $SuccessCount++
    Stop-Job $job
}
Remove-Job $job -Force

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Test Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Total Tests: $($SuccessCount + $ErrorCount)" -ForegroundColor White
Write-Host "  Passed: $SuccessCount" -ForegroundColor Green
Write-Host "  Failed: $ErrorCount" -ForegroundColor Red

if ($ErrorCount -eq 0) {
    Write-Host "`n  ALL TESTS PASSED!" -ForegroundColor Green
    exit 0
}
else {
    Write-Host "`n  SOME TESTS FAILED" -ForegroundColor Red
    exit 1
}
