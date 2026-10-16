@echo off
title E4K Bot Dashboard
echo.
echo  =============================================
echo   E4K Bot - Starting Dashboard Server...
echo  =============================================
echo.
echo  Dashboard will open at: http://localhost:5000
echo  Keep this window OPEN while using the bot.
echo  Press CTRL+C to stop the server.
echo.

cd /d "C:\Users\Aditya Mohite\.gemini\antigravity\scratch\empire_bot"

:: Wait 2 seconds then open browser
start /b cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:5000"

:: Start Flask server (this keeps window open)
python server.py

pause
