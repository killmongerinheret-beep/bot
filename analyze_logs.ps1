# Analyze Vatican Bot Logs
# Captures recent logs and shows key patterns

Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     Vatican Bot - Log Analysis                            ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

Write-Host "Capturing last 200 lines of logs..." -ForegroundColor Yellow
$logs = docker-compose logs --tail=200 worker_vatican 2>&1 | Out-String

Write-Host "✅ Logs captured" -ForegroundColor Green
Write-Host ""

# Analysis
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "VISITOR COUNT ANALYSIS" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Check for fromtag patterns
$fromtag1 = ([regex]::Matches($logs, "fromtag/1/")).Count
$fromtag2 = ([regex]::Matches($logs, "fromtag/2/")).Count
$fromtag3 = ([regex]::Matches($logs, "fromtag/3/")).Count

Write-Host "Deep Link Patterns:" -ForegroundColor Yellow
if ($fromtag1 -gt 0) {
    Write-Host "  ✅ /fromtag/1/ found $fromtag1 times (1 visitor)" -ForegroundColor Green
} else {
    Write-Host "  ❌ /fromtag/1/ not found (0 times)" -ForegroundColor Red
}

if ($fromtag2 -gt 0) {
    Write-Host "  ⚠️  /fromtag/2/ found $fromtag2 times (2 visitors)" -ForegroundColor Yellow
}

if ($fromtag3 -gt 0) {
    Write-Host "  ℹ️  /fromtag/3/ found $fromtag3 times (3 visitors)" -ForegroundColor Blue
}

Write-Host ""

# Check for API patterns
$visitorNum1 = ([regex]::Matches($logs, "visitorNum=1")).Count
$visitorNum2 = ([regex]::Matches($logs, "visitorNum=2")).Count
$visitorNum3 = ([regex]::Matches($logs, "visitorNum=3")).Count

Write-Host "API Call Patterns:" -ForegroundColor Yellow
if ($visitorNum1 -gt 0) {
    Write-Host "  ✅ visitorNum=1 found $visitorNum1 times" -ForegroundColor Green
} else {
    Write-Host "  ❌ visitorNum=1 not found (0 times)" -ForegroundColor Red
}

if ($visitorNum2 -gt 0) {
    Write-Host "  ⚠️  visitorNum=2 found $visitorNum2 times" -ForegroundColor Yellow
}

if ($visitorNum3 -gt 0) {
    Write-Host "  ℹ️  visitorNum=3 found $visitorNum3 times" -ForegroundColor Blue
}

Write-Host ""

# Check for Smart Group patterns
$smartGroups = ([regex]::Matches($logs, "Smart Group:.*?(\d+)v")).Count

Write-Host "Smart Grouping:" -ForegroundColor Yellow
if ($smartGroups -gt 0) {
    Write-Host "  ✅ Smart Group patterns found $smartGroups times" -ForegroundColor Green
    
    # Extract specific patterns
    $smartGroup1v = ([regex]::Matches($logs, "Smart Group:.*?/1v")).Count
    $smartGroup2v = ([regex]::Matches($logs, "Smart Group:.*?/2v")).Count
    
    if ($smartGroup1v -gt 0) {
        Write-Host "     • Grouping by 1 visitor: $smartGroup1v times" -ForegroundColor Green
    }
    if ($smartGroup2v -gt 0) {
        Write-Host "     • Grouping by 2 visitors: $smartGroup2v times" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ⚠️  No Smart Group patterns found" -ForegroundColor Yellow
    Write-Host "     (May be using legacy grouping)" -ForegroundColor Gray
}

Write-Host ""

# Check for availability
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "AVAILABILITY DETECTION" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

$foundSlots = ([regex]::Matches($logs, "Found \d+ slots")).Count
$availableSlots = ([regex]::Matches($logs, "FOUND.*SLOTS")).Count
$soldOut = ([regex]::Matches($logs, "SOLD OUT|sold_out")).Count

Write-Host "Availability Patterns:" -ForegroundColor Yellow
if ($foundSlots -gt 0 -or $availableSlots -gt 0) {
    Write-Host "  🎉 AVAILABILITY FOUND!" -ForegroundColor Green
    Write-Host "     • 'Found X slots': $foundSlots times" -ForegroundColor Green
    Write-Host "     • 'FOUND SLOTS': $availableSlots times" -ForegroundColor Green
} else {
    Write-Host "  ❌ No availability found in logs" -ForegroundColor Red
}

if ($soldOut -gt 0) {
    Write-Host "  ℹ️  'Sold out' mentioned: $soldOut times" -ForegroundColor Gray
}

Write-Host ""

# Check for errors
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "ERROR DETECTION" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

$errors = ([regex]::Matches($logs, "ERROR|Error|❌")).Count
$warnings = ([regex]::Matches($logs, "WARNING|Warning|⚠️")).Count

if ($errors -gt 0) {
    Write-Host "  ⚠️  Errors found: $errors" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Recent errors:" -ForegroundColor Red
    $logs -split "`n" | Select-String -Pattern "ERROR|Error|❌" | Select-Object -First 5 | ForEach-Object {
        Write-Host "    $_" -ForegroundColor Red
    }
} else {
    Write-Host "  ✅ No errors found" -ForegroundColor Green
}

if ($warnings -gt 0) {
    Write-Host "  ℹ️  Warnings found: $warnings" -ForegroundColor Yellow
}

Write-Host ""

# Check for specific tasks
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "TASK SPECIFIC CHECKS" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

$task19 = ([regex]::Matches($logs, "Task.*19|task.*19")).Count
$march16 = ([regex]::Matches($logs, "16/03/2026|2026-03-16")).Count

Write-Host "Task #19 (March 16, 1 visitor):" -ForegroundColor Yellow
if ($task19 -gt 0) {
    Write-Host "  ✅ Task #19 mentioned $task19 times" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  Task #19 not found in recent logs" -ForegroundColor Yellow
}

if ($march16 -gt 0) {
    Write-Host "  ✅ March 16 date mentioned $march16 times" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  March 16 date not found in recent logs" -ForegroundColor Yellow
}

Write-Host ""

# Summary
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "SUMMARY & DIAGNOSIS" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

$fixWorking = $fromtag1 -gt 0 -or $smartGroup1v -gt 0
$findingSlots = $foundSlots -gt 0 -or $availableSlots -gt 0
$hasErrors = $errors -gt 0

if ($fixWorking) {
    Write-Host "✅ VISITOR COUNT FIX IS WORKING!" -ForegroundColor Green
    Write-Host "   Bot is using correct visitor counts" -ForegroundColor White
} else {
    Write-Host "⚠️  VISITOR COUNT FIX NOT DETECTED" -ForegroundColor Yellow
    Write-Host "   Bot may still be using old code" -ForegroundColor White
    Write-Host "   Try: docker-compose restart worker_vatican" -ForegroundColor Cyan
}

Write-Host ""

if ($findingSlots) {
    Write-Host "🎉 BOT IS FINDING AVAILABILITY!" -ForegroundColor Green
    Write-Host "   If dashboard shows sold out, issue is:" -ForegroundColor White
    Write-Host "   1. Dashboard not refreshing" -ForegroundColor Gray
    Write-Host "   2. Backend API not accessible from Vercel" -ForegroundColor Gray
    Write-Host "   3. Cloudflare tunnel not working" -ForegroundColor Gray
} else {
    Write-Host "❌ NO AVAILABILITY FOUND" -ForegroundColor Red
    Write-Host "   This could mean:" -ForegroundColor White
    Write-Host "   1. Tickets genuinely sold out" -ForegroundColor Gray
    Write-Host "   2. Bot checking with wrong parameters" -ForegroundColor Gray
    Write-Host "   3. Bot not running checks yet" -ForegroundColor Gray
}

Write-Host ""

if ($hasErrors) {
    Write-Host "⚠️  ERRORS DETECTED IN LOGS" -ForegroundColor Red
    Write-Host "   Review errors above and check full logs" -ForegroundColor White
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "NEXT STEPS" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

if ($fixWorking -and $findingSlots) {
    Write-Host "✅ Bot is working correctly!" -ForegroundColor Green
    Write-Host ""
    Write-Host "1. Test backend API:" -ForegroundColor White
    Write-Host "   http://localhost:8000/api/tasks/" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "2. Check Cloudflare tunnel:" -ForegroundColor White
    Write-Host "   https://your-tunnel-url.trycloudflare.com/api/tasks/" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "3. Refresh Vercel dashboard:" -ForegroundColor White
    Write-Host "   https://bot-pl2x.vercel.app/" -ForegroundColor Cyan
    
} elseif ($fixWorking -and -not $findingSlots) {
    Write-Host "⚠️  Fix is working but no availability found" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "1. Wait a few more minutes for checks to complete" -ForegroundColor White
    Write-Host "2. Check if tickets are genuinely sold out" -ForegroundColor White
    Write-Host "3. View live logs: docker-compose logs -f worker_vatican" -ForegroundColor Cyan
    
} else {
    Write-Host "⚠️  Fix not detected in logs" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "1. Restart worker:" -ForegroundColor White
    Write-Host "   docker-compose restart worker_vatican" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "2. Wait 30 seconds and run this script again" -ForegroundColor White
    Write-Host "   .\analyze_logs.ps1" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "To see live logs: docker-compose logs -f worker_vatican" -ForegroundColor Gray
Write-Host "To save logs: docker-compose logs worker_vatican > logs.txt" -ForegroundColor Gray
Write-Host ""
