@echo off
echo ========================================
echo Running Migrations for ComplaintFeedback
echo ========================================
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

echo Step 1: Creating migrations...
python manage.py makemigrations complaints

echo.
echo Step 2: Applying migrations...
python manage.py migrate

echo.
echo ========================================
echo Migration Complete!
echo ========================================
echo.
echo Now you can:
echo 1. Run server: python manage.py runserver
echo 2. Access reports: http://localhost:8000/reports/
echo 3. Access feedback: http://localhost:8000/complaints/feedback-list/
echo.
pause
