# Test script for complete validation workflow
# Phase 2 - End-to-End Testing

$ErrorActionPreference = "Stop"
$baseUrl = "http://localhost:8000/api"

Write-Host "`n=== Azure Migration Tool - Complete Validation Workflow Test ===" -ForegroundColor Cyan
Write-Host "Testing: Servers upload → Landing zone config → Validation trigger → Results query`n" -ForegroundColor Gray

# Helper function for API calls
function Invoke-API {
    param(
        [string]$Method,
        [string]$Endpoint,
        [object]$Body = $null,
        [string]$Token = $null,
        [string]$ContentType = "application/json"
    )
    
    $headers = @{}
    if ($Token) {
        $headers["Authorization"] = "Bearer $Token"
    }
    if ($ContentType) {
        $headers["Content-Type"] = $ContentType
    }
    
    $params = @{
        Uri = "$baseUrl$Endpoint"
        Method = $Method
        Headers = $headers
    }
    
    if ($Body -and $ContentType -eq "application/json") {
        $params["Body"] = ($Body | ConvertTo-Json -Depth 10)
    } elseif ($Body) {
        $params["Body"] = $Body
    }
    
    try {
        $response = Invoke-RestMethod @params
        return $response
    } catch {
        Write-Host "API Error: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.ErrorDetails.Message) {
            Write-Host "Details: $($_.ErrorDetails.Message)" -ForegroundColor Red
        }
        throw
    }
}

# Test counters
$testsPassed = 0
$testsFailed = 0

function Test-Step {
    param([string]$Name, [scriptblock]$Code)
    Write-Host "`n>>> $Name" -ForegroundColor Yellow
    try {
        & $Code
        $script:testsPassed++
        Write-Host "✓ PASSED" -ForegroundColor Green
    } catch {
        $script:testsFailed++
        Write-Host "✗ FAILED: $_" -ForegroundColor Red
    }
}

# Variables
$token = $null
$project = $null
$excelFile = $null

# Step 1: Login
Test-Step "Step 1: Login as admin" {
    $loginData = @{
        email = "admin@example.com"
        password = "admin123"
    }
    
    $response = Invoke-API -Method POST -Endpoint "/auth/login" -Body $loginData
    $script:token = $response.access_token
    
    if (-not $token) {
        throw "No access token received"
    }
    
    Write-Host "  Token: $($token.Substring(0, 20))..." -ForegroundColor Gray
}

# Step 2: Create project
Test-Step "Step 2: Create test project" {
    $projectData = @{
        name = "E2E Test Project $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
        description = "End-to-end validation test project"
        azure_subscription_id = "12345678-1234-1234-1234-123456789abc"
        migrate_project_name = "test-migrate-project"
        recovery_vault_name = "test-recovery-vault"
    }
    
    $script:project = Invoke-API -Method POST -Endpoint "/projects" -Body $projectData -Token $token
    
    if (-not $project.id) {
        throw "No project ID received"
    }
    
    Write-Host "  Project ID: $($project.id)" -ForegroundColor Gray
    Write-Host "  Project Name: $($project.name)" -ForegroundColor Gray
}

# Step 3: Configure landing zone
Test-Step "Step 3: Configure landing zone" {
    $lzData = @{
        migrate_project_name = "test-migrate-project"
        migrate_project_rg = "test-migrate-rg"
        recovery_vault_name = "test-recovery-vault"
        recovery_vault_rg = "test-vault-rg"
        appliance_name = "test-appliance"
        cache_storage_account = "testcachestorage"
        cache_storage_rg = "test-cache-rg"
    }
    
    $lzResponse = Invoke-API -Method POST -Endpoint "/projects/$($project.id)/landing-zone" -Body $lzData -Token $token
    
    if (-not $lzResponse.id) {
        throw "Landing zone not created"
    }
    
    Write-Host "  Landing Zone ID: $($lzResponse.id)" -ForegroundColor Gray
}

# Step 4: Create sample Excel file with servers
Test-Step "Step 4: Create sample Excel file with servers" {
    # Use Python to create Excel file (ensures pandas compatibility)
    $script:excelFile = "$env:TEMP\test_servers_$(Get-Date -Format 'yyyyMMdd_HHmmss').xlsx"
    $script:excelFile = python tests\create_test_excel.py $excelFile
    
    if (-not (Test-Path $excelFile)) {
        throw "Failed to create Excel file"
    }
    
    Write-Host "  Excel file created: $excelFile" -ForegroundColor Gray
    Write-Host "  Servers: 3" -ForegroundColor Gray
}

# Step 5: Upload Excel file
Test-Step "Step 5: Upload server configurations" {
    # Upload using Invoke-WebRequest with -InFile parameter
    $headers = @{
        "Authorization" = "Bearer $token"
    }
    
    try {
        $response = Invoke-WebRequest -Uri "$baseUrl/projects/$($project.id)/servers/upload?update_existing=true" `
            -Method POST `
            -Headers $headers `
            -Form @{ file = [System.IO.FileInfo]::new($excelFile) } `
            -SkipHttpErrorCheck
        
        if ($response.StatusCode -eq 200) {
            $uploadResponse = $response.Content | ConvertFrom-Json
        } else {
            $errorDetail = ($response.Content | ConvertFrom-Json).detail
            throw "Upload failed: $errorDetail"
        }
    } catch {
        throw "Excel upload failed: $($_.Exception.Message)"
    }
    
    Write-Host "  Servers created: $($uploadResponse.servers_created)" -ForegroundColor Gray
    Write-Host "  Servers updated: $($uploadResponse.servers_updated)" -ForegroundColor Gray
    
    if ($uploadResponse.errors.Count -gt 0) {
        Write-Host "  Errors: $($uploadResponse.errors.Count)" -ForegroundColor Yellow
    }
    
    # Verify servers were created
    $serversList = Invoke-API -Method GET -Endpoint "/projects/$($project.id)/servers" -Token $token
    Write-Host "  Total servers in project: $($serversList.total)" -ForegroundColor Gray
}

# Step 6: Trigger validation
Test-Step "Step 6: Trigger validation job" {
    $validationResponse = Invoke-API -Method POST -Endpoint "/projects/$($project.id)/validate" -Token $token
    
    if (-not $validationResponse.job_id) {
        throw "No job ID received"
    }
    
    $jobId = $validationResponse.job_id
    Write-Host "  Job ID: $jobId" -ForegroundColor Gray
    Write-Host "  Status: $($validationResponse.status)" -ForegroundColor Gray
    Write-Host "  Message: $($validationResponse.message)" -ForegroundColor Gray
    
    # Set for next step
    $script:jobId = $jobId
}

# Step 7: Poll job status
Test-Step "Step 7: Poll validation job status" {
    $maxWaitSeconds = 300  # 5 minutes
    $pollIntervalSeconds = 5
    $elapsed = 0
    
    Write-Host "  Waiting for job to complete (max ${maxWaitSeconds}s)..." -ForegroundColor Gray
    
    while ($elapsed -lt $maxWaitSeconds) {
        $jobStatus = Invoke-API -Method GET -Endpoint "/validations/$jobId" -Token $token
        
        Write-Host "  [$elapsed s] Status: $($jobStatus.status)" -ForegroundColor Gray
        
        if ($jobStatus.status -eq "completed") {
            Write-Host "  ✓ Job completed successfully" -ForegroundColor Green
            if ($jobStatus.completed_at) {
                Write-Host "  Completed at: $($jobStatus.completed_at)" -ForegroundColor Gray
            }
            break
        } elseif ($jobStatus.status -eq "failed") {
            Write-Host "  ✗ Job failed" -ForegroundColor Red
            if ($jobStatus.error_message) {
                Write-Host "  Error: $($jobStatus.error_message)" -ForegroundColor Red
            }
            throw "Validation job failed"
        }
        
        Start-Sleep -Seconds $pollIntervalSeconds
        $elapsed += $pollIntervalSeconds
    }
    
    if ($elapsed -ge $maxWaitSeconds) {
        throw "Job did not complete within ${maxWaitSeconds} seconds"
    }
}

# Step 8: Get validation results
Test-Step "Step 8: Retrieve validation results" {
    $results = Invoke-API -Method GET -Endpoint "/validations/$jobId/results" -Token $token
    
    Write-Host "`n  === Validation Summary ===" -ForegroundColor Cyan
    Write-Host "  Total validations: $($results.summary.total_validations)" -ForegroundColor Gray
    Write-Host "  Total passed: $($results.summary.total_passed)" -ForegroundColor Green
    Write-Host "  Total failed: $($results.summary.total_failed)" -ForegroundColor $(if ($results.summary.total_failed -gt 0) { "Red" } else { "Green" })
    
    Write-Host "`n  Landing Zone:" -ForegroundColor Cyan
    Write-Host "    Total: $($results.summary.landing_zone.total)" -ForegroundColor Gray
    Write-Host "    Passed: $($results.summary.landing_zone.passed)" -ForegroundColor Green
    Write-Host "    Failed: $($results.summary.landing_zone.failed)" -ForegroundColor $(if ($results.summary.landing_zone.failed -gt 0) { "Red" } else { "Green" })
    
    Write-Host "`n  Servers:" -ForegroundColor Cyan
    Write-Host "    Total: $($results.summary.servers.total)" -ForegroundColor Gray
    Write-Host "    Passed: $($results.summary.servers.passed)" -ForegroundColor Green
    Write-Host "    Failed: $($results.summary.servers.failed)" -ForegroundColor $(if ($results.summary.servers.failed -gt 0) { "Red" } else { "Green" })
    
    if ($results.landing_zone_results.Count -gt 0) {
        Write-Host "`n  Landing Zone Results:" -ForegroundColor Cyan
        foreach ($lzResult in $results.landing_zone_results) {
            $color = if ($lzResult.status -eq "passed") { "Green" } else { "Red" }
            Write-Host "    [$($lzResult.validation_type)] $($lzResult.message)" -ForegroundColor $color
        }
    }
    
    if ($results.server_results.Count -gt 0) {
        Write-Host "`n  Server Results (first 5):" -ForegroundColor Cyan
        $results.server_results | Select-Object -First 5 | ForEach-Object {
            $color = if ($_.status -eq "passed") { "Green" } else { "Red" }
            Write-Host "    [$($_.server_name)] $($_.validation_type): $($_.message)" -ForegroundColor $color
        }
        
        if ($results.server_results.Count -gt 5) {
            Write-Host "    ... and $($results.server_results.Count - 5) more" -ForegroundColor Gray
        }
    }
}

# Step 9: List all validation jobs for project
Test-Step "Step 9: List validation jobs for project" {
    $jobs = Invoke-API -Method GET -Endpoint "/projects/$($project.id)/validations?page=1&page_size=10" -Token $token
    
    Write-Host "  Total jobs: $($jobs.total)" -ForegroundColor Gray
    Write-Host "  Jobs on this page: $($jobs.items.Count)" -ForegroundColor Gray
    
    if ($jobs.items.Count -gt 0) {
        Write-Host "`n  Recent jobs:" -ForegroundColor Cyan
        foreach ($job in $jobs.items) {
            $statusColor = switch ($job.status) {
                "completed" { "Green" }
                "failed" { "Red" }
                "running" { "Yellow" }
                default { "Gray" }
            }
            Write-Host "    Job #$($job.id) - Status: $($job.status) - Created: $($job.created_at)" -ForegroundColor $statusColor
        }
    }
}

# Cleanup
Write-Host "`n=== Cleanup ===" -ForegroundColor Cyan

if ($excelFile -and (Test-Path $excelFile)) {
    Remove-Item $excelFile -Force
    Write-Host "✓ Deleted temp Excel file" -ForegroundColor Gray
}

# Summary
Write-Host "`n=== Test Summary ===" -ForegroundColor Cyan
Write-Host "Tests Passed: $testsPassed" -ForegroundColor Green
Write-Host "Tests Failed: $testsFailed" -ForegroundColor $(if ($testsFailed -gt 0) { "Red" } else { "Green" })
Write-Host "Total Tests: $($testsPassed + $testsFailed)" -ForegroundColor Gray

if ($testsFailed -eq 0) {
    Write-Host "`n✓ All tests passed! Phase 2 validation workflow is working." -ForegroundColor Green
    exit 0
} else {
    Write-Host "`n✗ Some tests failed. Please review errors above." -ForegroundColor Red
    exit 1
}
