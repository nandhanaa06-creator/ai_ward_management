# Worker Performance Analytics - Complete Guide

## Overview
Comprehensive analytics system to track and analyze field worker performance with detailed metrics, charts, and PDF export.

## Features

### 📊 Metrics Tracked:
1. **Number of Complaints Completed** - Total resolved tasks
2. **Average Resolution Time** - Days taken to resolve complaints
3. **Citizen Feedback Rating** - Average rating from citizens (1-5 stars)
4. **Tasks Completed Per Month** - Monthly performance trends
5. **Completion Rate** - Percentage of assigned tasks completed
6. **Category Breakdown** - Distribution of work by complaint category
7. **Rating Distribution** - Breakdown of 1-5 star ratings

### 📈 Visualizations:
- Bar charts for worker comparison
- Line charts for monthly trends
- Doughnut charts for category breakdown
- Progress bars for rating distribution
- Performance leaderboard

### 📄 Export Options:
- PDF performance reports
- Individual worker reports
- Comprehensive metrics summary

## Installation

### No Additional Packages Required
All dependencies already installed:
- Django
- Chart.js (CDN)
- ReportLab (already installed)

### Add to Settings

Update `ward/settings.py`:
```python
INSTALLED_APPS = [
    ...
    'analytics',  # Add this
]
```

## URLs

### Main Dashboard:
```
/analytics/workers/
```

### Worker Detail:
```
/analytics/workers/<worker_id>/
```

### Export PDF:
```
/analytics/workers/<worker_id>/export-pdf/
```

### API Endpoints:
```
/analytics/api/worker-comparison/
/analytics/api/worker-ratings/
/analytics/api/worker/<worker_id>/monthly/
/analytics/api/worker/<worker_id>/categories/
```

## Usage

### 1. Access Analytics Dashboard

**URL:** `/analytics/workers/`

**Who Can Access:** Panchayath Admin, Superuser

**Features:**
- Overview statistics (total workers, completed tasks, active tasks, avg rating)
- Top 10 workers by completion (bar chart)
- Top 10 workers by rating (bar chart)
- Top 5 performers leaderboard
- All workers table with completion rates

### 2. View Worker Details

**URL:** `/analytics/workers/<worker_id>/`

**Features:**
- Performance metrics cards
- Monthly performance line chart (last 6 months)
- Rating distribution with progress bars
- Category breakdown doughnut chart
- Top categories table
- Recent tasks list
- Export to PDF button

### 3. Export Performance Report

**URL:** `/analytics/workers/<worker_id>/export-pdf/`

**Features:**
- Professional PDF report
- Worker name and date
- Performance summary table
- All key metrics included
- Downloadable file

## Metrics Explained

### 1. Total Assigned
- All complaints ever assigned to worker
- Includes pending, in progress, and completed

### 2. Completed
- Number of complaints marked as "resolved"
- Shows worker productivity

### 3. Completion Rate
- Formula: `(Completed / Total Assigned) × 100`
- Indicates efficiency
- Higher is better

### 4. Average Resolution Time
- Formula: `Sum of (resolved_date - created_date) / Number of resolved`
- Measured in days
- Lower is better
- Shows how quickly worker resolves issues

### 5. Citizen Rating
- Average of all feedback ratings (1-5 stars)
- Only includes complaints with feedback
- Shows citizen satisfaction
- Higher is better

### 6. Rating Distribution
- Breakdown of 5-star, 4-star, 3-star, 2-star, 1-star ratings
- Shows consistency of performance
- Helps identify areas for improvement

### 7. Monthly Performance
- Tasks completed each month for last 6 months
- Shows trends and patterns
- Helps identify seasonal variations

### 8. Category Breakdown
- Distribution of work by complaint type
- Shows worker specialization
- Helps with task assignment

## Charts

### 1. Worker Comparison Chart (Bar)
- **Type:** Horizontal bar chart
- **Data:** Top 10 workers by completion count
- **Color:** Green (success)
- **Use:** Compare worker productivity

### 2. Worker Rating Chart (Bar)
- **Type:** Horizontal bar chart
- **Data:** Top 10 workers by average rating
- **Color:** Blue (info)
- **Use:** Compare worker quality

### 3. Monthly Performance Chart (Line)
- **Type:** Line chart with area fill
- **Data:** Last 6 months completion count
- **Color:** Green (success)
- **Use:** Track trends over time

### 4. Category Breakdown Chart (Doughnut)
- **Type:** Doughnut chart
- **Data:** Top 6 categories by count
- **Colors:** Multi-color palette
- **Use:** Understand work distribution

## Navigation

### From Sidebar:
1. Click "Worker Analytics" in Administration section
2. View dashboard with all workers
3. Click "View Details" on any worker
4. View detailed analytics
5. Click "Export PDF" to download report

### From Manage Workers:
- Add link to worker analytics from manage workers page
- Quick access to performance data

## Access Control

### Required Role:
- Panchayath Admin
- Superuser

### Restricted:
- Ward Members (can be enabled if needed)
- Field Workers (cannot view their own analytics)
- Citizens (no access)

## Performance Considerations

### Optimized Queries:
- Uses Django annotations for efficiency
- Aggregates data at database level
- Minimal Python-side processing

### Caching Recommendations:
```python
# Add to views for production
from django.views.decorators.cache import cache_page

@cache_page(60 * 15)  # Cache for 15 minutes
def worker_analytics_dashboard(request):
    ...
```

### Database Indexes:
```python
# Add to Complaint model
class Meta:
    indexes = [
        models.Index(fields=['assigned_worker', 'status']),
        models.Index(fields=['assigned_worker', 'updated_at']),
    ]
```

## Customization

### Add More Metrics:

1. **Response Time:**
```python
# Time from assignment to first action
response_times = []
for task in all_tasks:
    if task.status_history.exists():
        first_action = task.status_history.first()
        delta = first_action.created_at - task.created_at
        response_times.append(delta.total_seconds() / 3600)  # hours
```

2. **Reopened Tasks:**
```python
# Tasks that were reopened after resolution
reopened = all_tasks.filter(
    status_history__new_status='pending',
    status_history__created_at__gt=F('updated_at')
).count()
```

3. **Citizen Satisfaction Trend:**
```python
# Monthly average ratings
monthly_ratings = []
for i in range(5, -1, -1):
    month_start = timezone.now() - timedelta(days=30*i)
    month_end = timezone.now() - timedelta(days=30*(i-1)) if i > 0 else timezone.now()
    
    avg = ComplaintFeedback.objects.filter(
        complaint__assigned_worker=worker,
        created_at__gte=month_start,
        created_at__lt=month_end
    ).aggregate(Avg('rating'))['rating__avg'] or 0
    
    monthly_ratings.append(avg)
```

### Add More Charts:

1. **Priority Distribution:**
```javascript
// Pie chart showing high/medium/low priority tasks
fetch('/analytics/api/worker/<id>/priorities/')
    .then(response => response.json())
    .then(data => {
        new Chart(ctx, {
            type: 'pie',
            data: {
                labels: ['High', 'Medium', 'Low'],
                datasets: [{
                    data: data.priorities,
                    backgroundColor: ['#dc3545', '#ffc107', '#198754']
                }]
            }
        });
    });
```

2. **Resolution Time Trend:**
```javascript
// Line chart showing average resolution time per month
fetch('/analytics/api/worker/<id>/resolution-trend/')
    .then(response => response.json())
    .then(data => {
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.months,
                datasets: [{
                    label: 'Avg Resolution Time (days)',
                    data: data.times,
                    borderColor: '#0dcaf0'
                }]
            }
        });
    });
```

## Troubleshooting

### No Data Showing:
**Cause:** No completed tasks
**Solution:** Assign and complete some tasks first

### Charts Not Loading:
**Cause:** API endpoints not accessible
**Solution:** Check URL configuration and permissions

### PDF Export Error:
**Cause:** ReportLab not installed
**Solution:** `pip install reportlab==4.0.9`

### Slow Performance:
**Cause:** Large dataset
**Solution:** Add database indexes and caching

## Best Practices

### 1. Regular Monitoring:
- Check analytics weekly
- Identify underperforming workers
- Recognize top performers

### 2. Fair Comparison:
- Consider task difficulty
- Account for ward differences
- Look at trends, not just numbers

### 3. Actionable Insights:
- Use data for training needs
- Adjust task assignments
- Reward high performers

### 4. Feedback Loop:
- Share analytics with workers
- Set performance goals
- Track improvement over time

## Future Enhancements

### Planned Features:
- [ ] Worker comparison side-by-side
- [ ] Custom date range selection
- [ ] Excel export option
- [ ] Email reports to admin
- [ ] Performance alerts
- [ ] Goal setting and tracking
- [ ] Team analytics
- [ ] Predictive analytics

### Integration Ideas:
- Link to worker profiles
- Add analytics to worker dashboard
- Show analytics in task assignment
- Include in performance reviews

## Files Created

1. `analytics/views.py` - All analytics views
2. `analytics/urls.py` - URL configuration
3. `analytics/templates/analytics/worker_dashboard.html` - Main dashboard
4. `analytics/templates/analytics/worker_detail.html` - Worker details
5. `templates/base.html` - Updated navigation
6. `ward/urls.py` - Added analytics URLs
7. `WORKER_ANALYTICS_GUIDE.md` - This documentation

## Summary

✅ **Complete Analytics System:**
- Dashboard with overview metrics
- Detailed worker analytics
- Multiple chart types
- PDF export functionality
- API endpoints for charts
- Responsive design
- Admin-only access

✅ **Key Metrics:**
- Completion count
- Resolution time
- Citizen ratings
- Monthly trends
- Category breakdown
- Rating distribution

✅ **Ready to Use:**
- No additional setup required
- All dependencies included
- Professional UI
- Mobile responsive
- Chart.js integration

Access at: `/analytics/workers/`
