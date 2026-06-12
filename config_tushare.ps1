# Tushare HTTP Proxy Configuration (PowerShell)
# ==================================================

Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  Tushare HTTP Proxy Configuration Tool" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

# Check existing configuration
if ($env:TUSHARE_HTTP_URL) {
    Write-Host "Current configuration:" -ForegroundColor Yellow
    Write-Host "  TUSHARE_HTTP_URL = $env:TUSHARE_HTTP_URL"
    if ($env:TUSHARE_HTTP_TOKEN) {
        Write-Host "  TUSHARE_HTTP_TOKEN = ******"
    }
    Write-Host ""
}

Write-Host "Configuration Options:"
Write-Host "  1. Temporary (current session only)"
Write-Host "  2. Permanent (user level, recommended)"
Write-Host "  3. Test current configuration"
Write-Host "  4. Exit"
Write-Host ""

$choice = Read-Host "Select (1-4)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "Temporary Configuration" -ForegroundColor Green
        Write-Host "================================"
        $apiUrl = Read-Host "Enter API URL (e.g. http://api.example.com)"
        $apiToken = Read-Host "Enter TOKEN (optional, press Enter to skip)"

        $env:TUSHARE_HTTP_URL = $apiUrl
        if ($apiToken) {
            $env:TUSHARE_HTTP_TOKEN = $apiToken
        }

        Write-Host ""
        Write-Host "OK! Temporary configuration applied:" -ForegroundColor Green
        Write-Host "  TUSHARE_HTTP_URL = $env:TUSHARE_HTTP_URL"
        Write-Host ""
        Write-Host "Note: Only valid in current PowerShell window" -ForegroundColor Yellow
        Write-Host ""

        # Test
        Write-Host "Testing configuration..." -ForegroundColor Cyan
        python test_tushare_config.py
    }

    "2" {
        Write-Host ""
        Write-Host "Permanent Configuration" -ForegroundColor Green
        Write-Host "================================"
        $apiUrl = Read-Host "Enter API URL (e.g. http://api.example.com)"
        $apiToken = Read-Host "Enter TOKEN (optional, press Enter to skip)"

        # Set permanently
        [System.Environment]::SetEnvironmentVariable('TUSHARE_HTTP_URL', $apiUrl, 'User')
        if ($apiToken) {
            [System.Environment]::SetEnvironmentVariable('TUSHARE_HTTP_TOKEN', $apiToken, 'User')
        }

        # Also set for current session
        $env:TUSHARE_HTTP_URL = $apiUrl
        if ($apiToken) {
            $env:TUSHARE_HTTP_TOKEN = $apiToken
        }

        Write-Host ""
        Write-Host "OK! Permanent configuration saved:" -ForegroundColor Green
        Write-Host "  TUSHARE_HTTP_URL = $apiUrl"
        Write-Host ""
        Write-Host "Note: New PowerShell windows will auto-load this config" -ForegroundColor Yellow
        Write-Host ""

        # Test
        Write-Host "Testing configuration..." -ForegroundColor Cyan
        python test_tushare_config.py
    }

    "3" {
        Write-Host ""
        Write-Host "Testing Configuration" -ForegroundColor Cyan
        Write-Host "================================"

        if (-not $env:TUSHARE_HTTP_URL) {
            Write-Host "ERROR: TUSHARE_HTTP_URL not configured" -ForegroundColor Red
            Write-Host ""
            Write-Host "Please run option 1 or 2 first" -ForegroundColor Yellow
        } else {
            Write-Host "Environment variables:" -ForegroundColor Green
            Write-Host "  TUSHARE_HTTP_URL = $env:TUSHARE_HTTP_URL"
            if ($env:TUSHARE_HTTP_TOKEN) {
                Write-Host "  TUSHARE_HTTP_TOKEN = ******"
            }
            Write-Host ""

            Write-Host "Running test script..." -ForegroundColor Cyan
            python test_tushare_config.py
        }
    }

    "4" {
        Write-Host "Exiting..." -ForegroundColor Yellow
        exit
    }

    default {
        Write-Host "Invalid choice" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Press any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
