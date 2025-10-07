# Test Landing Zone Validation Flow
# This tests the complete LZ validation without launching the migration wizard

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Testing Landing Zone Validation" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Create input for the tool
$testInput = @"
1
csv
y
n
y
"@

Write-Host "Inputs to be provided:" -ForegroundColor Yellow
Write-Host "  1 - Select Landing Zone Validation" -ForegroundColor Gray
Write-Host "  csv - Choose CSV format" -ForegroundColor Gray
Write-Host "  y - Use template file" -ForegroundColor Gray
Write-Host "  n - No JSON export" -ForegroundColor Gray
Write-Host "  y - Proceed with operation" -ForegroundColor Gray

Write-Host "`nRunning azmig...`n" -ForegroundColor Yellow
Write-Host "========================================`n" -ForegroundColor Cyan

# Run the tool with input
$testInput | azmig

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Test completed!" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan
