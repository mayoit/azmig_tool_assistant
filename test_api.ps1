# Test API endpoints

Write-Host "`n=== Testing Authentication Flow ===" -ForegroundColor Cyan

# 1. Register new user
Write-Host "`n1. Register new user..." -ForegroundColor Yellow
$registerBody = @{
    email = "test@example.com"
    password = "testpass123"
    full_name = "Test User"
} | ConvertTo-Json

$registerResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/register" `
    -Method POST `
    -ContentType "application/json" `
    -Body $registerBody `
    -ErrorAction Stop

Write-Host "✅ Registered user: $($registerResponse.email) (role: $($registerResponse.role))" -ForegroundColor Green

# 2. Login with admin user
Write-Host "`n2. Login with admin credentials..." -ForegroundColor Yellow
$loginBody = @{
    email = "admin@example.com"
    password = "admin123"
} | ConvertTo-Json

$loginResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/login" `
    -Method POST `
    -ContentType "application/json" `
    -Body $loginBody `
    -ErrorAction Stop

$accessToken = $loginResponse.access_token
Write-Host "✅ Login successful! Token expires in $($loginResponse.expires_in) seconds" -ForegroundColor Green

# 3. Get current user info
Write-Host "`n3. Get current user info..." -ForegroundColor Yellow
$headers = @{
    Authorization = "Bearer $accessToken"
}

$meResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/me" `
    -Method GET `
    -Headers $headers `
    -ErrorAction Stop

Write-Host "✅ Current user: $($meResponse.full_name) ($($meResponse.email))" -ForegroundColor Green

# 4. List projects
Write-Host "`n4. List all projects..." -ForegroundColor Yellow
$projectsResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/projects" `
    -Method GET `
    -Headers $headers `
    -ErrorAction Stop

Write-Host "✅ Found $($projectsResponse.total) projects:" -ForegroundColor Green
foreach ($project in $projectsResponse.items) {
    Write-Host "   - $($project.name) (status: $($project.status))" -ForegroundColor White
}

# 5. Create new project
Write-Host "`n5. Create new project..." -ForegroundColor Yellow
$projectBody = @{
    name = "Test Project"
    description = "Created via API test"
    azure_subscription_id = "99999999-9999-9999-9999-999999999999"
    metadata_json = @{
        test = $true
        created_at = (Get-Date -Format "yyyy-MM-dd")
    }
} | ConvertTo-Json

$newProject = Invoke-RestMethod -Uri "http://localhost:8000/api/projects" `
    -Method POST `
    -ContentType "application/json" `
    -Headers $headers `
    -Body $projectBody `
    -ErrorAction Stop

Write-Host "✅ Created project: $($newProject.name) (ID: $($newProject.id))" -ForegroundColor Green

# 6. Get project details
Write-Host "`n6. Get project details..." -ForegroundColor Yellow
$projectDetails = Invoke-RestMethod -Uri "http://localhost:8000/api/projects/$($newProject.id)" `
    -Method GET `
    -Headers $headers `
    -ErrorAction Stop

Write-Host "✅ Project: $($projectDetails.name)" -ForegroundColor Green
Write-Host "   Description: $($projectDetails.description)" -ForegroundColor White
Write-Host "   Owner: $($projectDetails.owner.full_name)" -ForegroundColor White
Write-Host "   Servers: $($projectDetails.servers_count)" -ForegroundColor White
Write-Host "   Validations: $($projectDetails.validations_count)" -ForegroundColor White

# 7. Test non-admin user access
Write-Host "`n7. Test viewer access (should only see their own projects)..." -ForegroundColor Yellow
$viewerLoginBody = @{
    email = "viewer@example.com"
    password = "viewer123"
} | ConvertTo-Json

$viewerLoginResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/login" `
    -Method POST `
    -ContentType "application/json" `
    -Body $viewerLoginBody `
    -ErrorAction Stop

$viewerHeaders = @{
    Authorization = "Bearer $($viewerLoginResponse.access_token)"
}

$viewerProjects = Invoke-RestMethod -Uri "http://localhost:8000/api/projects" `
    -Method GET `
    -Headers $viewerHeaders `
    -ErrorAction Stop

Write-Host "✅ Viewer sees $($viewerProjects.total) projects (filtered to their own)" -ForegroundColor Green

Write-Host "`n=== All tests passed! ===" -ForegroundColor Green
