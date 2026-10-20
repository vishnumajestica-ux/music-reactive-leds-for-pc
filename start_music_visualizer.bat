@echo off
timeout /t 30 /nobreak >nul
cd /d "%USERPROFILE%\OneDrive\Desktop"
start "" "C:\Users\SPMU_\AppData\Local\Python\pythoncore-3.15-64\python.exe" "%USERPROFILE%\OneDrive\Desktop\music_visualizer.py"
