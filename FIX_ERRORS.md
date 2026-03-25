# Fix Installation Errors

## Error 1: ModuleNotFoundError: No module named 'sklearn'

### Solution:
Open your terminal/command prompt and run:

```bash
# Activate your virtual environment first
venv\Scripts\activate

# Then install scikit-learn
pip install scikit-learn numpy
```

Or if you're already in the virtual environment:
```bash
pip install scikit-learn==1.5.2 numpy==1.26.4
```

## Error 2: Cannot resolve keyword 'complaint' into field

This error was already fixed in the citizens_list view. The code now uses 'complaints' instead of 'complaint'.

## Quick Fix Commands:

```bash
# 1. Activate virtual environment
cd "E:\AI-Based Smart Ward Management System"
venv\Scripts\activate

# 2. Install dependencies
pip install scikit-learn numpy

# 3. Train AI models
python manage.py train_ai_model
python manage.py train_priority_model

# 4. Run server
python manage.py runserver
```

## If pip doesn't work, try:
```bash
python -m pip install scikit-learn numpy
```

## Or install from requirements.txt:
```bash
pip install -r requirements.txt
```
