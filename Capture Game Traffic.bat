@echo off
title E4K Traffic Capture Tool
color 0A
echo.
echo  =====================================================
echo   E4K Traffic Capture Tool - Auto Setup
echo  =====================================================
echo.

:: Step 1 - Set Windows system proxy (LDPlayer uses this automatically)
echo [1/3] Setting Windows system proxy to route LDPlayer traffic...
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings" /v ProxyEnable /t REG_DWORD /d 1 /f >nul
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings" /v ProxyServer /t REG_SZ /d "127.0.0.1:8888" /f >nul
echo       Done! Windows proxy set to 127.0.0.1:8888

echo.
echo [2/3] IMPORTANT - Set proxy inside LDPlayer Android:
echo       Inside LDPlayer, go to:
echo       Android Settings - WiFi - Long press WiredSSID
echo       - Modify Network - Advanced - Proxy: Manual
echo       - Host: 192.168.0.105
echo       - Port: 8888
echo.
echo [3/3] Starting traffic capture proxy...
echo.
echo  -----------------------------------------------
echo  NOW DO THIS IN ORDER:
echo  1. Set LDPlayer proxy as shown above
echo  2. Open Empire: Four Kingdoms in LDPlayer
echo  3. Log in to your game account
echo  4. Open World Map
echo  5. Attack 1 Robber Baron castle
echo  6. Press CTRL+C here when done
echo  -----------------------------------------------
echo.
pause

cd /d "C:\Users\Aditya Mohite\.gemini\antigravity\scratch\empire_bot"
python tools/capture_traffic.py

:: Step - Disable Windows proxy when done
echo.
echo Disabling Windows proxy...
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings" /v ProxyEnable /t REG_DWORD /d 0 /f >nul
echo Done! Proxy removed.
echo.
echo Check the captured_traffic folder for results!
pause
