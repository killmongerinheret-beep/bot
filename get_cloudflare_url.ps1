# Get Cloudflare Tunnel URL for Vercel
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "CLOUDFLARE TUNNEL URL FOR VERCEL" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if cloudflared is running
$cloudflared = Get-Process -Name "cloudflared" -ErrorAction SilentlyContinue

if ($cloudflared) {
    Write-Host "✅ Cloudflared is running (PID: $($cloudflared.Id))" -ForegroundColor Green
    Write-Host ""
    Write-Host "⚠️  The tunnel URL was shown when you started cloudflared." -ForegroundColor Yellow
    Write-Host "    It looks like: https://abc-def-123.trycloudflare.com" -ForegroundColor Gray
    Write-Host ""
    Write-Host "📋 To find it:" -ForegroundColor Cyan
    Write-Host "   1. Look at the terminal where you ran cloudflared" -ForegroundColor Gray
    Write-Host "   2. Find the line with 'Your quick Tunnel has been created'" -ForegroundColor Gray
    Write-Host "   3. Copy the https://xxx.trycloudflare.com URL" -ForegroundColor Gray
    Write-Host ""
    Write-Host "🔄 Or restart cloudflared to see the URL again:" -ForegroundColor Cyan
    Write-Host "   1. Stop current tunnel (Ctrl+C in that terminal)" -ForegroundColor Gray
    Write-Host "   2. Run: cloudflared tunnel --url http://localhost:8000" -ForegroundColor Gray
    Write-Host "   3. Copy the new URL" -ForegroundColor Gray
    Write-Host ""
} else {
    Write-Host "❌ Cloudflared is NOT running" -ForegroundColor Red
    Write-Host ""
    Write-Host "🚀 Start it now:" -ForegroundColor Cyan
    Write-Host "   cloudflared tunnel --url http://localhost:8000" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "   You'll see output like:" -ForegroundColor Gray
    Write-Host "   +------------------------------------------------------------------+" -ForegroundColor DarkGray
    Write-Host "   | Your quick Tunnel has been created! Visit it at:                 |" -ForegroundColor DarkGray
    Write-Host "   | https://abc-def-123.trycloudflare.com                            |" -ForegroundColor Green
    Write-Host "   +------------------------------------------------------------------+" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "   Copy that URL! ☝️" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "VERCEL CONFIGURATION" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Once you have your Cloudflare URL:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1️⃣  Go to Vercel Dashboard" -ForegroundColor Cyan
Write-Host "   https://vercel.com/dashboard" -ForegroundColor Gray
Write-Host ""
Write-Host "2️⃣  Select your project" -ForegroundColor Cyan
Write-Host "   (probably 'bot-pl2x' or similar)" -ForegroundColor Gray
Write-Host ""
Write-Host "3️⃣  Go to Settings → Environment Variables" -ForegroundColor Cyan
Write-Host ""
Write-Host "4️⃣  Add or update this variable:" -ForegroundColor Cyan
Write-Host "   Name:  NEXT_PUBLIC_API_URL" -ForegroundColor Yellow
Write-Host "   Value: https://your-tunnel-url.trycloudflare.com/api/v1" -ForegroundColor Yellow
Write-Host "          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^" -ForegroundColor Red
Write-Host "          Replace with YOUR actual Cloudflare URL + /api/v1" -ForegroundColor Red
Write-Host ""
Write-Host "   Example:" -ForegroundColor Gray
Write-Host "   NEXT_PUBLIC_API_URL=https://abc-def-123.trycloudflare.com/api/v1" -ForegroundColor Green
Write-Host ""
Write-Host "5️⃣  Click Save" -ForegroundColor Cyan
Write-Host ""
Write-Host "6️⃣  Go to Deployments tab" -ForegroundColor Cyan
Write-Host ""
Write-Host "7️⃣  Click ... menu on latest deployment → Redeploy" -ForegroundColor Cyan
Write-Host ""
Write-Host "8️⃣  Wait ~2 minutes for deployment" -ForegroundColor Cyan
Write-Host ""
Write-Host "9️⃣  Visit your Vercel app and refresh!" -ForegroundColor Cyan
Write-Host "   https://bot-pl2x.vercel.app/" -ForegroundColor Gray
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "QUICK TEST" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Want to test your tunnel URL now? (Y/N)" -ForegroundColor Yellow
$test = Read-Host

if ($test -eq "Y" -or $test -eq "y") {
    Write-Host ""
    Write-Host "Enter your Cloudflare tunnel URL:" -ForegroundColor Cyan
    Write-Host "(e.g., https://abc-def-123.trycloudflare.com)" -ForegroundColor Gray
    $url = Read-Host
    
    if ($url) {
        $url = $url.TrimEnd('/')
        Write-Host ""
        Write-Host "Testing: $url/api/v1/tasks/" -ForegroundColor Yellow
        Write-Host ""
        
        try {
            $response = Invoke-WebRequest -Uri "$url/api/v1/tasks/" -UseBasicParsing -TimeoutSec 10
            $tasks = $response.Content | ConvertFrom-Json
            
            Write-Host "✅ SUCCESS! Tunnel is working!" -ForegroundColor Green
            Write-Host ""
            Write-Host "Found $($tasks.Count) tasks:" -ForegroundColor Cyan
            
            foreach ($task in $tasks) {
                $icon = if ($task.last_status -eq "available") { "✅" } else { "❌" }
                Write-Host "   $icon Task #$($task.id) - $($task.dates[0]) - $($task.last_status)" -ForegroundColor Gray
            }
            
            Write-Host ""
            Write-Host "🎉 Your tunnel URL is correct!" -ForegroundColor Green
            Write-Host ""
            Write-Host "Use this in Vercel:" -ForegroundColor Yellow
            Write-Host "NEXT_PUBLIC_API_URL=$url/api/v1" -ForegroundColor Green
            Write-Host ""
            
        } catch {
            Write-Host "❌ Failed to connect" -ForegroundColor Red
            Write-Host ""
            Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
            Write-Host ""
            Write-Host "Make sure:" -ForegroundColor Yellow
            Write-Host "  - URL starts with https://" -ForegroundColor Gray
            Write-Host "  - Cloudflared is running" -ForegroundColor Gray
            Write-Host "  - Backend is running (docker-compose ps backend)" -ForegroundColor Gray
            Write-Host ""
        }
    }
}

Write-Host ""
Write-Host "Done! 🎉" -ForegroundColor Green
Write-Host ""
