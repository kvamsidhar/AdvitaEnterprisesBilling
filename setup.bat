@echo off
setlocal
cd /d "%~dp0"
echo ==========================================
echo Advita Enterprises Quotation Generator
echo Installing Python packages...
echo ==========================================
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 -m pip install --upgrade pip
  py -3 -m pip install -r requirements.txt
) else (
  python -m pip install --upgrade pip
  python -m pip install -r requirements.txt
)
if errorlevel 1 (
  echo.
  echo Installation failed. Please install Python 3.10 or newer from python.org
  echo and make sure "Add Python to PATH" is checked.
  pause
  exit /b 1
)
echo.
echo Setup completed. You can now run launch.bat
pause
