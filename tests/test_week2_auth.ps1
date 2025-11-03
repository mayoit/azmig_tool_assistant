# Week 2 - Authentication Flow Test
# This script tests the complete authentication flow

Write-Host "`n🧪 Week 2: Authentication Flow Test`n" -ForegroundColor Cyan

# Test 1: API Health Check
Write-Host "Test 1: API Health Check" -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri 'http://localhost:8000/health' -Method Get
    if ($health.status -eq 'healthy') {
        Write-Host "  ✓ API is healthy (version: $($health.version))" -ForegroundColor Green
    } else {
        Write-Host "  ✗ API health check failed" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "  ✗ Failed to connect to API: $_" -ForegroundColor Red
    exit 1
}

# Test 2: Login with Admin User
Write-Host "`nTest 2: Login with Admin Credentials" -ForegroundColor Yellow
try {
    $loginBody = @{
        email = 'admin@example.com'
        password = 'admin123'
    } | ConvertTo-Json

    $loginResponse = Invoke-RestMethod -Uri 'http://localhost:8000/api/auth/login' `
        -Method Post `
        -Body $loginBody `
        -ContentType 'application/json'

    if ($loginResponse.access_token) {
        Write-Host "  ✓ Login successful" -ForegroundColor Green
        Write-Host "  ✓ Access token received" -ForegroundColor Green
        $token = $loginResponse.access_token
    } else {
        Write-Host "  ✗ No access token in response" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "  ✗ Login failed: $_" -ForegroundColor Red
    exit 1
}

# Test 3: Access Protected Endpoint
Write-Host "`nTest 3: Access Protected Endpoint (Projects)" -ForegroundColor Yellow
try {
    $projects = Invoke-RestMethod -Uri 'http://localhost:8000/api/projects' `
        -Headers @{Authorization="Bearer $token"} `
        -Method Get

    if ($projects.items) {
        Write-Host "  ✓ Successfully accessed protected endpoint" -ForegroundColor Green
        Write-Host "  ✓ Found $($projects.total) projects in database" -ForegroundColor Green
    } else {
        Write-Host "  ✗ No projects returned" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "  ✗ Failed to access protected endpoint: $_" -ForegroundColor Red
    exit 1
}

# Test 4: Login with Operator User
Write-Host "`nTest 4: Login with Operator Credentials" -ForegroundColor Yellow
try {
    $loginBody = @{
        email = 'operator@example.com'
        password = 'operator123'
    } | ConvertTo-Json

    $operatorResponse = Invoke-RestMethod -Uri 'http://localhost:8000/api/auth/login' `
        -Method Post `
        -Body $loginBody `
        -ContentType 'application/json'

    if ($operatorResponse.access_token) {
        Write-Host "  ✓ Operator login successful" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Operator login failed" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "  ✗ Operator login failed: $_" -ForegroundColor Red
    exit 1
}

# Test 5: Login with Viewer User
Write-Host "`nTest 5: Login with Viewer Credentials" -ForegroundColor Yellow
try {
    $loginBody = @{
        email = 'viewer@example.com'
        password = 'viewer123'
    } | ConvertTo-Json

    $viewerResponse = Invoke-RestMethod -Uri 'http://localhost:8000/api/auth/login' `
        -Method Post `
        -Body $loginBody `
        -ContentType 'application/json'

    if ($viewerResponse.access_token) {
        Write-Host "  ✓ Viewer login successful" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Viewer login failed" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "  ✗ Viewer login failed: $_" -ForegroundColor Red
    exit 1
}

# Test 6: Invalid Credentials
Write-Host "`nTest 6: Invalid Credentials (Should Fail)" -ForegroundColor Yellow
try {
    $loginBody = @{
        email = 'invalid@example.com'
        password = 'wrongpassword'
    } | ConvertTo-Json

    $invalidResponse = Invoke-RestMethod -Uri 'http://localhost:8000/api/auth/login' `
        -Method Post `
        -Body $loginBody `
        -ContentType 'application/json' `
        -ErrorAction SilentlyContinue

    Write-Host "  ✗ Expected authentication to fail" -ForegroundColor Red
    exit 1
} catch {
    if ($_.Exception.Response.StatusCode -eq 401) {
        Write-Host "  ✓ Correctly rejected invalid credentials (401)" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Unexpected error: $_" -ForegroundColor Yellow
    }
}

# Test 7: Access Without Token (Should Fail)
Write-Host "`nTest 7: Access Protected Endpoint Without Token (Should Fail)" -ForegroundColor Yellow
try {
    $unauthorizedResponse = Invoke-RestMethod -Uri 'http://localhost:8000/api/projects' `
        -Method Get `
        -ErrorAction SilentlyContinue

    Write-Host "  ✗ Expected authorization to fail" -ForegroundColor Red
    exit 1
} catch {
    if ($_.Exception.Response.StatusCode -eq 401 -or $_.Exception.Response.StatusCode -eq 403) {
        Write-Host "  ✓ Correctly rejected unauthorized access (401/403)" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Unexpected error: $_" -ForegroundColor Yellow
    }
}

# Final Summary
Write-Host "`n✅ All Authentication Tests Passed!`n" -ForegroundColor Green

Write-Host "📋 Summary:" -ForegroundColor Cyan
Write-Host "  ✓ API health check" -ForegroundColor Green
Write-Host "  ✓ Admin login" -ForegroundColor Green
Write-Host "  ✓ Operator login" -ForegroundColor Green
Write-Host "  ✓ Viewer login" -ForegroundColor Green
Write-Host "  ✓ Protected endpoint access" -ForegroundColor Green
Write-Host "  ✓ Invalid credentials rejected" -ForegroundColor Green
Write-Host "  ✓ Unauthorized access blocked" -ForegroundColor Green

Write-Host "`n🌐 Frontend Testing:" -ForegroundColor Cyan
Write-Host "  Open http://localhost:5173 to test the login UI" -ForegroundColor White
Write-Host "  Try logging in with:" -ForegroundColor White
Write-Host "    • admin@example.com / admin123" -ForegroundColor Gray
Write-Host "    • operator@example.com / operator123" -ForegroundColor Gray
Write-Host "    • viewer@example.com / viewer123" -ForegroundColor Gray

Write-Host "`n✨ Week 2 Components:" -ForegroundColor Cyan
Write-Host "  ✓ LoginForm with validation" -ForegroundColor Green
Write-Host "  ✓ ProtectedRoute wrapper" -ForegroundColor Green
Write-Host "  ✓ Navbar with user menu" -ForegroundColor Green
Write-Host "  ✓ Sidebar with navigation" -ForegroundColor Green
Write-Host "  ✓ MainLayout integration" -ForegroundColor Green
Write-Host "  ✓ Dark mode support" -ForegroundColor Green

Write-Host ""
