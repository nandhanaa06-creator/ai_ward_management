@echo off
echo Installing required packages for Export Reports feature...
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install packages
pip install reportlab==4.0.9
pip install pandas==2.2.0

echo.
echo Installation complete!
echo Now run: python manage.py runserver
pause
