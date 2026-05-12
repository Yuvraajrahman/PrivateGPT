@echo off
setlocal
cd /d "%~dp0"
echo.
npm run start:chatbot
if errorlevel 1 (
  echo.
  echo Failed — see messages above. Press any key to close.
  pause >nul
)
endlocal
