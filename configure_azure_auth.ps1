# Configure Azure Authentication for a Project
# This script helps set up Azure credentials for validation

Write-Host "🔐 Azure Authentication Configuration" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$baseUrl = "http://localhost:8000/api"
$email = "admin@example.com"
$password = "admin123"

# Step 1: Login
Write-Host "1️⃣  Logging in..." -ForegroundColor Yellow
$loginBody = @{
    email = $email
    password = $password
} | ConvertTo-Json

$loginResponse = Invoke-RestMethod -Uri "$baseUrl/auth/login" -Method Post -Body $loginBody -ContentType "application/json"
$token = $loginResponse.access_token
Write-Host "   ✅ Login successful!" -ForegroundColor Green
Write-Host ""

# Step 2: Get Azure Token (using Azure CLI)
Write-Host "2️⃣  Getting Azure token from Azure CLI..." -ForegroundColor Yellow
Write-Host "   💡 Make sure you're logged in with: az login" -ForegroundColor Gray
Write-Host ""

try {
    # Get token from Azure CLI
    $azToken = az account get-access-token --resource https://management.azure.com --query accessToken -o tsv
    $azAccount = az account show | ConvertFrom-Json
    
    Write-Host "   ✅ Azure token retrieved!" -ForegroundColor Green
    Write-Host "   📧 Account: $($azAccount.user.name)" -ForegroundColor Cyan
    Write-Host "   🔑 Tenant: $($azAccount.tenantId)" -ForegroundColor Cyan
    Write-Host "   📦 Subscription: $($azAccount.name) ($($azAccount.id))" -ForegroundColor Cyan
    Write-Host ""
    
    # Calculate token expiration (Azure tokens typically last 1 hour)
    $expiresOn = [int][double]::Parse((Get-Date).AddHours(1).ToString("yyyyMMddHHmmss"))
    
    # Step 3: List projects
    Write-Host "3️⃣  Fetching projects..." -ForegroundColor Yellow
    $headers = @{
        "Authorization" = "Bearer $token"
    }
    
    $projects = Invoke-RestMethod -Uri "$baseUrl/projects" -Method Get -Headers $headers
    Write-Host "   ✅ Found $($projects.items.Count) project(s)" -ForegroundColor Green
    Write-Host ""
    
    # Show available projects
    Write-Host "   Available Projects:" -ForegroundColor Cyan
    for ($i = 0; $i -lt $projects.items.Count; $i++) {
        $proj = $projects.items[$i]
        Write-Host "   [$i] ID: $($proj.id) - $($proj.name)" -ForegroundColor White
    }
    Write-Host ""
    
    # Step 4: Select project
    $projectIndex = Read-Host "   Enter project number (0-$($projects.items.Count - 1))"
    $selectedProject = $projects.items[$projectIndex]
    Write-Host "   📁 Selected: $($selectedProject.name) (ID: $($selectedProject.id))" -ForegroundColor Cyan
    Write-Host ""
    
    # Step 5: Configure Azure auth for the project
    Write-Host "4️⃣  Configuring Azure authentication..." -ForegroundColor Yellow
    
    # Update project with Azure credentials
    $updateBody = @{
        azure_subscription_id = $azAccount.id
        azure_tenant_id = $azAccount.tenantId
        auth_method = "user_token"
        auth_credentials = @{
            access_token = $azToken
            expires_on = $expiresOn
        }
    } | ConvertTo-Json
    
    $updateResponse = Invoke-RestMethod -Uri "$baseUrl/projects/$($selectedProject.id)" -Method Put -Body $updateBody -Headers $headers -ContentType "application/json"
    
    Write-Host "   ✅ Azure authentication configured!" -ForegroundColor Green
    Write-Host "   🔑 Method: User Token (from Azure CLI)" -ForegroundColor Cyan
    Write-Host "   📦 Subscription: $($azAccount.id)" -ForegroundColor Cyan
    Write-Host "   🔑 Tenant: $($azAccount.tenantId)" -ForegroundColor Cyan
    Write-Host "   ⏰ Token valid for ~1 hour" -ForegroundColor Yellow
    Write-Host ""
    
    # Step 6: Test authentication
    Write-Host "5️⃣  Testing Azure authentication..." -ForegroundColor Yellow
    try {
        $testUrl = "$baseUrl/projects/$($selectedProject.id)/auth/test"
        $testResult = Invoke-RestMethod -Uri $testUrl -Method Post -Headers $headers
        
        Write-Host "   ✅ Authentication test successful!" -ForegroundColor Green
        Write-Host "   ✓ Can access Azure Resource Manager" -ForegroundColor Green
        Write-Host ""
    } catch {
        Write-Host "   ⚠️  Authentication test failed: $($_.Exception.Message)" -ForegroundColor Yellow
        Write-Host "   💡 This might be OK if the endpoint doesn't exist yet" -ForegroundColor Gray
        Write-Host ""
    }
    
    Write-Host "=====================================" -ForegroundColor Cyan
    Write-Host "✅ Configuration Complete!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📝 Next Steps:" -ForegroundColor Cyan
    Write-Host "   1. Go to http://localhost:5173" -ForegroundColor White
    Write-Host "   2. Login and navigate to project: $($selectedProject.name)" -ForegroundColor White
    Write-Host "   3. Click validate button on any migrate project" -ForegroundColor White
    Write-Host "   4. Validation should now work with Azure!" -ForegroundColor White
    Write-Host ""
    Write-Host "⚠️  Important: Token expires in ~1 hour" -ForegroundColor Yellow
    Write-Host "   Re-run this script to refresh if needed" -ForegroundColor Gray
    Write-Host ""
    
} catch {
    Write-Host ""
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 Troubleshooting:" -ForegroundColor Yellow
    Write-Host "   1. Make sure Azure CLI is installed: https://aka.ms/azcli" -ForegroundColor Gray
    Write-Host "   2. Login to Azure CLI: az login" -ForegroundColor Gray
    Write-Host "   3. Set your subscription: az account set --subscription <subscription-id>" -ForegroundColor Gray
    Write-Host "   4. Run this script again" -ForegroundColor Gray
    Write-Host ""
}
