@echo off
REM === Instagram reels auto-poster (PC) ===
cd /d "F:\extraas\claude projects\youtube uploads history"
echo [1/2] Naye reels GitHub se la rahe hain...
git pull
echo [2/2] Instagram par post kar rahe hain...
python src\run_local_instagram.py
echo Done. Window 10 sec me band hoga.
timeout /t 10 >nul
