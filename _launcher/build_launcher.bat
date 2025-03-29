@echo off
del .\dist\launcher.exe
del .\dist\WelcomeLauncher.exe
..\..\venv\Scripts\pyinstaller.exe --onefile --icon=Welcome.ico launcher.py
ren .\dist\launcher.exe WelcomeLauncher.exe
pause
