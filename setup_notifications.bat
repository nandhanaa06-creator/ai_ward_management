@echo off
echo ========================================
echo Real-Time Notifications Setup
echo ========================================
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

echo Step 1: Installing Django Channels...
pip install channels==4.0.0
pip install channels-redis==4.1.0
pip install daphne==4.0.0

echo.
echo Step 2: Creating migrations...
python manage.py makemigrations notifications

echo.
echo Step 3: Applying migrations...
python manage.py migrate

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo To start server with WebSocket support:
echo   python manage.py runserver
echo.
echo Or use Daphne (recommended for production):
echo   daphne -b 0.0.0.0 -p 8000 ward.asgi:application
echo.
echo Test notifications at: http://localhost:8000
echo.
pause
