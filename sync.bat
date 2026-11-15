@echo off
REM One-click sync: commit every change in the project and push it to GitHub.
REM GitHub then retrains (if data changed) and updates Counselling-Unit-Support-Assistant.md automatically.
chcp 65001 >nul
cd /d "%~dp0"
set /p MSG="Describe the change (Enter = automatic message): "
if "%MSG%"=="" set MSG=Update %date% %time:~0,5%
python tools\build_project_md.py
git add -A
git commit -m "%MSG%"
git pull --rebase origin main
git push origin main
git pull --rebase origin main
echo.
echo Done. GitHub will refresh the project MD file within about a minute.
pause
