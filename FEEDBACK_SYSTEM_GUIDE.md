# Complaint Feedback System - Migration Guide

## Database Migration Required

A new model `ComplaintFeedback` has been added to store citizen ratings and feedback.

### Run Migration Commands:

```bash
# Activate virtual environment
E:\AI-Based Smart Ward Management System\venv\Scripts\activate

# Create migration
python manage.py makemigrations

# Apply migration
python manage.py migrate
```

## New Features Added:

### 1. ComplaintFeedback Model
- **Fields:**
  - complaint (OneToOneField) - Links to resolved complaint
  - citizen (ForeignKey) - User who submitted feedback
  - rating (1-5 stars)
  - feedback_text (TextField)
  - created_at, updated_at (timestamps)

### 2. Views Created:
- **submit_feedback** - Citizen submits rating and feedback
- **feedback_list** - Admin views all feedback reports

### 3. Templates Created:
- **feedback_form.html** - Interactive star rating form
- **feedback_list.html** - Admin feedback dashboard with stats and filters

### 4. URLs Added:
- `/complaints/<id>/feedback/` - Feedback form (GET)
- `/complaints/<id>/submit-feedback/` - Submit feedback (POST)
- `/complaints/feedback-list/` - Admin feedback list

## Features:

### For Citizens:
- Submit 1-5 star rating after complaint resolution
- Write detailed feedback
- Interactive star rating UI
- Auto re-open complaint if rating ≤ 2 stars

### For Admins:
- View all feedback with stats
- Filter by rating (1-5 stars)
- Filter by ward
- View average rating
- Track good vs poor ratings
- Modal popup for detailed feedback view

## Usage:

### Citizen Flow:
1. Complaint gets resolved
2. Citizen clicks "Submit Feedback" button
3. Rates 1-5 stars and writes feedback
4. If rating ≤ 2, complaint auto re-opens with HIGH priority

### Admin Flow:
1. Navigate to Feedback List
2. View stats: Total, Average, Good/Poor ratings
3. Filter by rating or ward
4. Click "View" to see full feedback details
5. Click "View Complaint" to see original complaint

## Security:
- Only complaint owner can submit feedback
- Only resolved complaints can receive feedback
- One feedback per complaint (OneToOne relationship)
- Admin/Ward Member access required for feedback list

## Next Steps:
1. Run migrations
2. Test feedback submission on resolved complaints
3. Add "Submit Feedback" button to complaint detail page
4. Add "Feedback Reports" link to admin navigation
