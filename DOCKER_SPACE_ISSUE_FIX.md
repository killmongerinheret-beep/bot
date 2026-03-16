# Docker Space Not Showing on Windows - Fix Guide

## 🤔 Why This Happens

Docker on Windows uses a **virtual disk file** (usually `ext4.vhdx`) to store all Docker data. When you delete Docker objects, the space is freed **inside** the virtual disk, but the `.vhdx` file itself doesn't shrink automatically.

**Think of it like this:**
- You have a 50GB zip file
- You delete 30GB of files inside the zip
- The zip file is still 50GB on disk until you "compress" it

---

## 🔍 Check Docker's Virtual Disk Location

### Docker Desktop Location
The virtual disk is usually located at:
```
C:\Users\[YourUsername]\AppData\Local\Docker\wsl\data\ext4.vhdx
```

Or for WSL2:
```
C:\Users\[YourUsername]\AppData\Local\Docker\wsl\distro\ext4.vhdx
```

---

## 🛠️ Solutions to Reclaim Disk Space

### Solution 1: Compact WSL2 Virtual Disk (Recommended)

1. **Stop Docker Desktop completely**
   - Right-click Docker Desktop in system tray
   - Click "Quit Docker Desktop"
   - Wait for it to fully stop

2. **Open PowerShell as Administrator**

3. **Shutdown WSL**
   ```powershell
   wsl --shutdown
   ```

4. **Find your Docker virtual disk**
   ```powershell
   # Check common locations
   Get-ChildItem -Path "$env:USERPROFILE\AppData\Local\Docker\wsl" -Recurse -Name "*.vhdx"
   ```

5. **Compact the virtual disk**
   ```powershell
   # Replace with your actual path
   diskpart
   ```
   
   In diskpart:
   ```
   select vdisk file="C:\Users\[YourUsername]\AppData\Local\Docker\wsl\data\ext4.vhdx"
   compact vdisk
   exit
   ```

6. **Restart Docker Desktop**

### Solution 2: Using Docker Desktop Settings

1. **Open Docker Desktop**
2. **Go to Settings** (gear icon)
3. **Resources → Advanced**
4. **Click "Clean / Purge data"**
5. **Restart Docker Desktop**

### Solution 3: WSL Command (Alternative)

```powershell
# Shutdown WSL
wsl --shutdown

# Compact the disk (replace path)
wsl --manage docker-desktop-data --set-sparse true
```

### Solution 4: Reset Docker Desktop (Nuclear Option)

⚠️ **WARNING: This will delete all Docker data**

1. **Docker Desktop → Settings → Reset**
2. **Choose "Reset to factory defaults"**
3. **This will free all space but you'll need to rebuild everything**

---

## 🧪 Quick Test Commands

### Before Compacting
```powershell
# Check current disk usage
Get-ChildItem "$env:USERPROFILE\AppData\Local\Docker\wsl\data\ext4.vhdx" | Select-Object Name, @{Name="Size(GB)";Expression={[math]::Round($_.Length/1GB,2)}}
```

### After Compacting
```powershell
# Check if size reduced
Get-ChildItem "$env:USERPROFILE\AppData\Local\Docker\wsl\data\ext4.vhdx" | Select-Object Name, @{Name="Size(GB)";Expression={[math]::Round($_.Length/1GB,2)}}
```

---

## 📋 Step-by-Step Fix (Recommended)

### Step 1: Stop Docker
```powershell
# Stop Docker Desktop completely
# (Use GUI or wait for processes to stop)
```

### Step 2: Shutdown WSL
```powershell
wsl --shutdown
```

### Step 3: Find Virtual Disk
```powershell
# Find the .vhdx file
Get-ChildItem -Path "$env:USERPROFILE\AppData\Local\Docker" -Recurse -Name "*.vhdx"
```

### Step 4: Compact Disk
```powershell
# Open diskpart
diskpart

# In diskpart (replace with your actual path):
select vdisk file="C:\Users\YourUsername\AppData\Local\Docker\wsl\data\ext4.vhdx"
compact vdisk
exit
```

### Step 5: Restart Docker
```powershell
# Start Docker Desktop again
```

### Step 6: Verify
```powershell
# Check Docker is working
docker ps

# Check space usage
docker system df
```

---

## 🔧 Alternative: PowerShell Script

Create this script to automate the process:

```powershell
# docker_compact.ps1
Write-Host "🛑 Stopping Docker Desktop..."
Stop-Process -Name "Docker Desktop" -Force -ErrorAction SilentlyContinue

Write-Host "⏳ Waiting for Docker to stop..."
Start-Sleep -Seconds 10

Write-Host "🔌 Shutting down WSL..."
wsl --shutdown

Write-Host "🔍 Finding Docker virtual disk..."
$vhdxPath = Get-ChildItem -Path "$env:USERPROFILE\AppData\Local\Docker" -Recurse -Name "*.vhdx" | Select-Object -First 1
$fullPath = "$env:USERPROFILE\AppData\Local\Docker\wsl\data\$vhdxPath"

if (Test-Path $fullPath) {
    Write-Host "📁 Found: $fullPath"
    
    $sizeBefore = (Get-Item $fullPath).Length / 1GB
    Write-Host "📊 Size before: $([math]::Round($sizeBefore, 2)) GB"
    
    Write-Host "🗜️ Compacting virtual disk..."
    $diskpartScript = @"
select vdisk file="$fullPath"
compact vdisk
exit
"@
    
    $diskpartScript | diskpart
    
    $sizeAfter = (Get-Item $fullPath).Length / 1GB
    Write-Host "📊 Size after: $([math]::Round($sizeAfter, 2)) GB"
    Write-Host "💾 Space freed: $([math]::Round($sizeBefore - $sizeAfter, 2)) GB"
} else {
    Write-Host "❌ Virtual disk not found!"
}

Write-Host "🚀 Starting Docker Desktop..."
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"

Write-Host "✅ Done! Check your disk space now."
```

---

## 🎯 Expected Results

After compacting, you should see:
- **Windows disk space freed** (31GB+ available)
- **Docker still working** normally
- **Virtual disk file smaller** on Windows
- **All containers still running**

---

## ⚠️ Troubleshooting

### If Compact Fails
```powershell
# Try alternative method
wsl --manage docker-desktop-data --set-sparse true
```

### If Docker Won't Start
```powershell
# Reset WSL
wsl --unregister docker-desktop-data
wsl --unregister docker-desktop
# Then restart Docker Desktop
```

### If Still No Space
- Check Windows Disk Cleanup
- Empty Recycle Bin
- Check for Windows Update files
- Run `cleanmgr` (Disk Cleanup)

---

## 🏆 Quick Fix Summary

1. **Stop Docker Desktop**
2. **Run:** `wsl --shutdown`
3. **Run:** `diskpart` → `select vdisk file="path"` → `compact vdisk`
4. **Start Docker Desktop**
5. **Check disk space** - should now show 31GB+ freed!

This should immediately show the freed space in Windows! 🎉