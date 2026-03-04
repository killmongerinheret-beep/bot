# Windows PowerShell Script to Check Logs for Visitor Count
# This script filters logs to show visitor-related entries

Write-Host "Checking Vatican worker logs for visitor count patterns..." -ForegroundColor Cyan
Write-Host ""

# Get the last 100 lines of logs
$logs = docker-compose logs --tail=100 worker_vatican 2>&1

# Filter for visitor-related patterns
Write-Host "=== Deep Link Patterns (fromtag) ===" -ForegroundColor Yellow
$logs | Select-String -Pattern "fromtag" | ForEach-Object {
    $line = $_.Line
    if ($line -match "fromtag/(\d+)/") {
        $visitors = $matches[1]
        if ($visitors -eq "1") {
            Write-Host "✅ " -NoNewline -ForegroundColor Green
        } elseif ($visitors -eq "2") {
            Write-Host "⚠️  " -NoNewline -ForegroundColor Yellow
        } else {
            Write-Host "ℹ️  " -NoNewline -ForegroundColor Blue
        }
        Write-Host "$line"
    }
}

Write-Host "`n=== API Call Patterns (visitorNum) ===" -ForegroundColor Yellow
$logs | Select-String -Pattern "visitorNum" | ForEach-Object {
    $line = $_.Line
    if ($line -match "visitorNum=(\d+)") {
        $visitors = $matches[1]
        if ($visitors -eq "1") {
            Write-Host "✅ " -NoNewline -ForegroundColor Green
        } elseif ($visitors -eq "2") {
            Write-Host "⚠️  " -NoNewline -ForegroundColor Yellow
        } else {
            Write-Host "ℹ️  " -NoNewline -ForegroundColor Blue
        }
        Write-Host "$line"
    }
}

Write-Host "`n=== Smart Group Patterns ===" -ForegroundColor Yellow
$logs | Select-String -Pattern "Smart Group" | ForEach-Object {
    Write-Host "📊 $($_.Line)" -ForegroundColor Cyan
}

Write-Host "`n=== Task Check Patterns ===" -ForegroundColor Yellow
$logs | Select-String -Pattern "Checking.*visitor" | ForEach-Object {
    Write-Host "🔍 $($_.Line)" -ForegroundColor Magenta
}

Write-Host "`n=== Error Patterns ===" -ForegroundColor Yellow
$errorCount = 0
$logs | Select-String -Pattern "ERROR|Error|error|❌" | ForEach-Object {
    Write-Host "❌ $($_.Line)" -ForegroundColor Red
    $errorCount++
}

if ($errorCount -eq 0) {
    Write-Host "✅ No errors found" -ForegroundColor Green
}

Write-Host "`n=== Summary ===" -ForegroundColor Cyan
$fromtag1 = ($logs | Select-String -Pattern "fromtag/1/").Count
$fromtag2 = ($logs | Select-String -Pattern "fromtag/2/").Count
$visitorNum1 = ($logs | Select-String -Pattern "visitorNum=1").Count
$visitorNum2 = ($logs | Select-String -Pattern "visitorNum=2").Count

Write-Host "Deep links with 1 visitor: $fromtag1" -ForegroundColor $(if ($fromtag1 -gt 0) { "Green" } else { "Gray" })
Write-Host "Deep links with 2 visitors: $fromtag2" -ForegroundColor $(if ($fromtag2 -gt 0) { "Yellow" } else { "Gray" })
Write-Host "API calls with visitorNum=1: $visitorNum1" -ForegroundColor $(if ($visitorNum1 -gt 0) { "Green" } else { "Gray" })
Write-Host "API calls with visitorNum=2: $visitorNum2" -ForegroundColor $(if ($visitorNum2 -gt 0) { "Yellow" } else { "Gray" })
Write-Host "Errors found: $errorCount" -ForegroundColor $(if ($errorCount -eq 0) { "Green" } else { "Red" })

Write-Host "`nTo see live logs, run:" -ForegroundColor Yellow
Write-Host "docker-compose logs -f worker_vatican" -ForegroundColor Cyan
