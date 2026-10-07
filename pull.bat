@echo off
setlocal
cd /d "%~dp0"

git pull
if errorlevel 1 goto failed

echo.
echo Pull completed successfully.
pause
exit /b 0

:failed
echo.
echo Pull failed. Check the error above.
pause
exit /b 1
