@echo off
setlocal
cd /d "%~dp0"

git add -A
if errorlevel 1 goto failed

git diff --cached --quiet
if errorlevel 1 goto commit
goto push

:commit
set "commit_message="
set /p "commit_message=Commit message (default: Update project): "
if not defined commit_message set "commit_message=Update project"

git commit -m "%commit_message%"
if errorlevel 1 goto failed

:push
git push
if errorlevel 1 goto failed

echo.
echo Push completed successfully.
pause
exit /b 0

:failed
echo.
echo Push failed. Check the error above.
pause
exit /b 1
