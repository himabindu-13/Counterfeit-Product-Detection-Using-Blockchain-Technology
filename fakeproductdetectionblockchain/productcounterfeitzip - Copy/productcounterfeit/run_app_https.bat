@echo off
REM Script to run Flask app with HTTPS for mobile camera access
REM Note: You'll need to accept the self-signed certificate on your phone

echo ========================================
echo  Product Verification System (HTTPS)
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

REM Get local IP address
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set LOCAL_IP=%%a
    goto :found_ip
)
:found_ip
set LOCAL_IP=%LOCAL_IP:~1%
echo.
echo Your local IP address: %LOCAL_IP%
echo.

REM Set environment variables for HTTPS
set FLASK_USE_HTTPS=1
set PUBLIC_BASE_URL=https://%LOCAL_IP%:5000

echo Starting Flask server with HTTPS...
echo.
echo HTTPS Server: https://%LOCAL_IP%:5000
echo.
echo IMPORTANT:
echo   - On your phone, go to: https://%LOCAL_IP%:5000
echo   - Accept the security warning (self-signed certificate is safe for testing)
echo   - After accepting, camera will work!
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start Flask app
python app3.py

pause

