# Test script for Landing Zone Validation Flow
# This script tests the complete validation workflow

Write-Host "🧪 Testing Landing Zone Validation Flow" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$baseUrl = "http://localhost:8000/api"
$email = "admin@example.com"
$password = "admin123"

# Step 1: Login
Write-Host "1️⃣  Logging in as $email..." -ForegroundColor Yellow
$loginBody = @{
    email = $email
    password = $password
} | ConvertTo-Json

$loginResponse = Invoke-RestMethod -Uri "$baseUrl/auth/login" -Method Post -Body $loginBody -ContentType "application/json"
$token = $loginResponse.access_token
Write-Host "   ✅ Login successful! Token: $($token.Substring(0, 20))..." -ForegroundColor Green
Write-Host ""

# Step 2: Get Projects
Write-Host "2️⃣  Fetching projects..." -ForegroundColor Yellow
$headers = @{
    "Authorization" = "Bearer $token"
}

$projects = Invoke-RestMethod -Uri "$baseUrl/projects" -Method Get -Headers $headers
Write-Host "   ✅ Found $($projects.items.Count) project(s)" -ForegroundColor Green

# Use the "Production Migration - Phase 1" project (ID: 1)
$project = $projects.items | Where-Object { $_.name -eq "Production Migration - Phase 1" } | Select-Object -First 1
if (-not $project) {
    # Fallback to first project
    $project = $projects.items[0]
}
Write-Host "   📁 Using project: $($project.name) (ID: $($project.id))" -ForegroundColor Cyan
Write-Host ""

# Step 3: Get Landing Zones for the project
Write-Host "3️⃣  Fetching landing zones..." -ForegroundColor Yellow
$landingZones = Invoke-RestMethod -Uri "$baseUrl/projects/$($project.id)/landing-zones" -Method Get -Headers $headers
Write-Host "   ✅ Found $($landingZones.Count) landing zone(s)" -ForegroundColor Green

if ($landingZones.Count -gt 0) {
    $lz = $landingZones[0]
    Write-Host "   🏗️  First landing zone: $($lz.migrateProjects.Count) migrate project(s)" -ForegroundColor Cyan
    
    if ($lz.migrateProjects.Count -gt 0) {
        $migrateProjectIndex = 0
        $migrateProject = $lz.migrateProjects[$migrateProjectIndex]
        Write-Host "   📦 Migrate Project: $($migrateProject.migrateProjectName)" -ForegroundColor Cyan
        Write-Host ""
        
        # Step 4: Trigger Validation
        Write-Host "4️⃣  Triggering validation for migrate project..." -ForegroundColor Yellow
        try {
            $validateUrl = "$baseUrl/projects/$($project.id)/landing-zones/migrate-projects/$migrateProjectIndex/validate"
            Write-Host "   🔗 URL: $validateUrl" -ForegroundColor Gray
            
            $validationResponse = Invoke-RestMethod -Uri $validateUrl -Method Post -Headers $headers
            Write-Host "   ✅ Validation triggered successfully!" -ForegroundColor Green
            Write-Host "   📊 Validation ID: $($validationResponse.validation_id)" -ForegroundColor Cyan
            Write-Host "   ⏱️  Status: $($validationResponse.status)" -ForegroundColor Cyan
            Write-Host "   📝 Message: $($validationResponse.message)" -ForegroundColor Cyan
            Write-Host ""
            
            # Step 5: Get Validation Results
            Write-Host "5️⃣  Waiting 2 seconds for validation to process..." -ForegroundColor Yellow
            Start-Sleep -Seconds 2
            
            Write-Host "   📥 Fetching validation results..." -ForegroundColor Yellow
            $resultUrl = "$baseUrl/projects/$($project.id)/landing-zones/migrate-projects/$migrateProjectIndex/validation-result"
            $validationResult = Invoke-RestMethod -Uri $resultUrl -Method Get -Headers $headers
            
            Write-Host "   ✅ Validation completed!" -ForegroundColor Green
            Write-Host "   📊 Overall Status: $($validationResult.status)" -ForegroundColor $(if ($validationResult.status -eq "PASSED") { "Green" } elseif ($validationResult.status -eq "FAILED") { "Red" } else { "Yellow" })
            Write-Host "   ✅ Passed: $($validationResult.passed_count)" -ForegroundColor Green
            Write-Host "   ❌ Failed: $($validationResult.failed_count)" -ForegroundColor Red
            Write-Host "   ⚠️  Warnings: $($validationResult.warning_count)" -ForegroundColor Yellow
            Write-Host "   📅 Validated At: $($validationResult.validated_at)" -ForegroundColor Cyan
            Write-Host ""
            
            # Step 6: Show Individual Validation Results
            Write-Host "6️⃣  Individual validation results:" -ForegroundColor Yellow
            foreach ($result in $validationResult.results) {
                $statusIcon = switch ($result.status) {
                    "PASSED" { "✅" }
                    "FAILED" { "❌" }
                    "WARNING" { "⚠️" }
                    default { "❓" }
                }
                Write-Host "   $statusIcon $($result.stage): $($result.message)" -ForegroundColor $(
                    switch ($result.status) {
                        "PASSED" { "Green" }
                        "FAILED" { "Red" }
                        "WARNING" { "Yellow" }
                        default { "Gray" }
                    }
                )
            }
            Write-Host ""
            
            # Step 7: Get All Validations for the Project
            Write-Host "7️⃣  Fetching all validations for project..." -ForegroundColor Yellow
            $allValidations = Invoke-RestMethod -Uri "$baseUrl/projects/$($project.id)/validations" -Method Get -Headers $headers
            Write-Host "   ✅ Found $($allValidations.Count) validation(s) in history" -ForegroundColor Green
            Write-Host ""
            
        } catch {
            Write-Host "   ❌ Error during validation: $($_.Exception.Message)" -ForegroundColor Red
            Write-Host "   📄 Response: $($_.Exception.Response)" -ForegroundColor Red
        }
    } else {
        Write-Host "   ⚠️  No migrate projects found in landing zone" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ⚠️  No landing zones found in project" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ Test Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Next Steps:" -ForegroundColor Cyan
Write-Host "   1. Open http://localhost:5173 in your browser" -ForegroundColor White
Write-Host "   2. Login with: admin@example.com / admin123" -ForegroundColor White
Write-Host "   3. Navigate to a project" -ForegroundColor White
Write-Host "   4. Click the validate button (✓) on a migrate project" -ForegroundColor White
Write-Host "   5. Switch to the 'Validations' tab to see results" -ForegroundColor White
Write-Host ""
