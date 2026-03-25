@echo off
echo ========================================
echo Fixing Notification Model Conflicts
echo ========================================
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

echo Step 1: Creating migrations for governance...
python manage.py makemigrations governance

echo.
echo Step 2: Creating migrations for notifications...
python manage.py makemigrations notifications

echo.
echo Step 3: Applying all migrations...
python manage.py migrate

echo.
echo ========================================
echo Migration Complete!
echo ========================================
echo.
echo Fixed:
echo - governance.Notification now uses 'governance_notifications'
echo - notifications.Notification now uses 'user_notifications'
echo - Static files directory created
echo.
echo You can now run: python manage.py runserver
echo.
pause
