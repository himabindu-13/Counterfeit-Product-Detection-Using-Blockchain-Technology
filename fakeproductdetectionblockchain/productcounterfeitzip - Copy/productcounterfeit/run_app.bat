@echo off
REM Simple script to run the Flask app
REM This will activate the virtual environment and start the server

echo ========================================
echo  Product Verification System
echo ========================================
echo.

REM Change to the app directory
cd /d "%~dp0"

REM Activate virtual environment
echo Activating virtual environment...
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
) else (
    echo ERROR: Virtual environment not found!
    echo Please run: python -m venv .venv
    echo Then install packages: pip install flask qrcode opencv-python numpy web3 eth-account pyOpenSSL pyzbar
    pause
    exit /b 1
)

echo.
echo Starting Flask server...
echo.
echo Server will start on: http://localhost:5000
echo.
echo TIP: For mobile camera access, you need HTTPS:
echo   1. Use ngrok: download from https://ngrok.com
echo   2. Run: ngrok http 5000
echo   3. Use the ngrok HTTPS URL on your phone
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start Flask app
python app3.py

pause

