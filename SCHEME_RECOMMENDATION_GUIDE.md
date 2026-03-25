# 🎯 AI-Powered Scheme Recommendation Engine

## Overview
The Scheme Recommendation Engine is an advanced AI feature that automatically matches citizens with government schemes they're eligible for based on their profile data. It uses intelligent scoring algorithms to calculate eligibility and provides personalized recommendations.

---

## 🚀 Key Features

### 1. **Intelligent Eligibility Scoring**
- **Multi-factor Analysis**: Evaluates age, income, gender, and occupation
- **Weighted Scoring**: Each criterion contributes to a 0-100% match score
  - Age eligibility: 30 points
  - Income eligibility: 30 points
  - Gender match: 20 points
  - Occupation match: 20 points
- **Smart Filtering**: Only recommends schemes with ≥50% match score

### 2. **Personalized Citizen Dashboard**
- View all recommended schemes sorted by match score
- Color-coded badges (Green: 80%+, Blue: 70-79%, Yellow: 50-69%)
- Detailed eligibility reasons with checkmarks (✓) and crosses (✗)
- Track viewed and applied schemes
- One-click application to external portals

### 3. **Admin Analytics Dashboard**
- Overall recommendation statistics
- Average match scores across all recommendations
- View and application conversion rates
- Top performing schemes by recommendation count
- Score distribution charts
- Conversion funnel visualization
- Recent recommendations tracking

### 4. **Automatic Tracking**
- Tracks when citizens view scheme details
- Tracks when citizens apply to schemes
- Timestamps for all interactions
- Prevents duplicate recommendations per user-scheme pair

---

## 📊 How the AI Scoring Works

### Eligibility Calculation Algorithm

```python
Total Score = Age Score + Income Score + Gender Score + Occupation Score

Age Score (30 points):
- ✓ If user.age is between scheme.min_age and scheme.max_age → +30 points
- ✗ Otherwise → 0 points

Income Score (30 points):
- ✓ If user.annual_income ≤ scheme.max_income → +30 points
- ✗ Otherwise → 0 points

Gender Score (20 points):
- ✓ If scheme is open to all genders OR matches user gender → +20 points
- ✗ Otherwise → 0 points

Occupation Score (20 points):
- ✓ If scheme is open to all occupations → +20 points
- ✓ If user occupation matches scheme target occupations → +20 points
- ✗ Otherwise → 0 points
```

### Match Score Interpretation
- **90-100%**: Perfect match - Highly recommended
- **80-89%**: Excellent match - Strongly recommended
- **70-79%**: Good match - Recommended
- **60-69%**: Fair match - Consider applying
- **50-59%**: Partial match - Review eligibility carefully
- **<50%**: Not recommended (filtered out)

---

## 🎨 User Interface

### Citizen Dashboard (`/recommendations/my-recommendations/`)
**Stats Cards:**
- Total Matches: Number of recommended schemes
- High Match: Schemes with 80%+ match score
- Viewed: Schemes the citizen has viewed
- Applied: Schemes the citizen has applied to

**Scheme Cards:**
- Scheme name and match percentage badge
- Description and benefits summary
- Detailed eligibility reasons
- "View Details" and "Apply Now" buttons
- Status indicators (viewed/applied)

### Admin Analytics (`/recommendations/analytics/`)
**Stats Cards:**
- Total recommendations generated
- Users with recommendations
- Average match score
- View rate percentage

**Charts:**
- Match Score Distribution (Bar chart)
- Conversion Funnel (Horizontal bar chart)

**Tables:**
- Top Recommended Schemes with conversion rates
- Recent Recommendations with status tracking

---

## 🔧 Technical Implementation

### Models
**SchemeRecommendation**
- `user`: ForeignKey to User
- `scheme`: ForeignKey to Scheme
- `match_score`: Float (0-100)
- `match_reasons`: TextField (detailed explanation)
- `is_viewed`: Boolean
- `is_applied`: Boolean
- `created_at`, `viewed_at`, `applied_at`: Timestamps

### Engine Functions
**SchemeRecommendationEngine.calculate_eligibility(user, scheme)**
- Returns: (score, reasons_text)
- Evaluates all eligibility criteria
- Generates human-readable explanations

**SchemeRecommendationEngine.generate_recommendations(user, force_refresh=False)**
- Generates recommendations for all active schemes
- Only creates recommendations with score ≥ 50%
- Prevents duplicates unless force_refresh=True

**SchemeRecommendationEngine.get_top_recommendations(user, limit=5)**
- Returns top N recommendations sorted by score
- Auto-generates if none exist

### API Endpoints
- `/recommendations/my-recommendations/` - Citizen dashboard
- `/recommendations/refresh/` - Force regenerate recommendations
- `/recommendations/mark-viewed/<id>/` - Track view action
- `/recommendations/mark-applied/<id>/` - Track application
- `/recommendations/analytics/` - Admin analytics dashboard
- `/recommendations/api/score-distribution/` - Chart data
- `/recommendations/api/conversion-funnel/` - Chart data

---

## 📋 Usage Instructions

### For Citizens

1. **Access Recommendations**
   - Navigate to "Recommended Schemes" in the sidebar
   - System automatically generates recommendations on first visit

2. **View Scheme Details**
   - Click "View Details" to see full scheme information
   - System tracks this as a view
   - Opens application portal if available

3. **Apply to Schemes**
   - Click "Apply Now" to open external application portal
   - System tracks this as an application
   - Status updates automatically

4. **Refresh Recommendations**
   - Click "Refresh" button to regenerate recommendations
   - Useful after updating profile information
   - Clears old recommendations and creates new ones

### For Administrators

1. **Monitor Performance**
   - Access "Scheme Analytics" in the sidebar
   - View overall recommendation statistics
   - Analyze conversion rates

2. **Identify Top Schemes**
   - Check "Top Recommended Schemes" table
   - See which schemes are most relevant to citizens
   - Monitor application conversion rates

3. **Track Engagement**
   - View recent recommendations
   - Monitor view and application rates
   - Identify schemes with low engagement

---

## 🔄 Integration with Existing System

### Required User Profile Fields
The recommendation engine requires these fields in the User model:
- `age` (IntegerField)
- `annual_income` (DecimalField)
- `gender` (CharField with choices: M/F)
- `occupation` (CharField)

### Scheme Model Requirements
The Scheme model must have:
- `min_age`, `max_age` (IntegerField)
- `max_income` (DecimalField)
- `gender_target` (CharField: M/F/A)
- `target_occupation` (CharField, comma-separated)
- `is_active` (BooleanField)
- `application_link` (URLField, optional)

---

## 📈 Analytics Metrics

### Key Performance Indicators (KPIs)
1. **Recommendation Coverage**: % of users with recommendations
2. **Average Match Score**: Quality of recommendations
3. **View Rate**: (Viewed / Total) × 100
4. **Application Rate**: (Applied / Total) × 100
5. **Conversion Rate**: (Applied / Viewed) × 100

### Success Criteria
- Average match score > 70%
- View rate > 40%
- Application rate > 15%
- Conversion rate > 30%

---

## 🎯 Benefits

### For Citizens
- **Discover Eligible Schemes**: No need to manually search
- **Save Time**: Instant eligibility checking
- **Transparency**: Clear reasons for each recommendation
- **Easy Application**: Direct links to application portals

### For Administrators
- **Increase Enrollment**: More citizens discover relevant schemes
- **Data-Driven Decisions**: Analytics show which schemes are popular
- **Improved Targeting**: Understand citizen demographics
- **Performance Tracking**: Monitor scheme effectiveness

### For Government
- **Better Outreach**: Schemes reach intended beneficiaries
- **Higher Utilization**: More citizens apply to schemes
- **Reduced Overhead**: Automated eligibility screening
- **Measurable Impact**: Track recommendation effectiveness

---

## 🔮 Future Enhancements

1. **Machine Learning Improvements**
   - Learn from application patterns
   - Adjust scoring weights based on success rates
   - Predict likelihood of application completion

2. **Advanced Filtering**
   - Location-based scheme recommendations
   - Family size considerations
   - Disability or special needs criteria

3. **Notifications**
   - Alert citizens about new matching schemes
   - Remind about application deadlines
   - Follow-up on viewed but not applied schemes

4. **Collaborative Filtering**
   - "Citizens like you also applied to..."
   - Success stories from similar profiles

5. **Multi-language Support**
   - Recommendations in local languages
   - Translated scheme descriptions

---

## 🐛 Troubleshooting

### No Recommendations Showing
- **Cause**: User profile incomplete
- **Solution**: Ensure age, income, gender, and occupation are filled

### Low Match Scores
- **Cause**: User doesn't meet scheme criteria
- **Solution**: Update profile or create more inclusive schemes

### Recommendations Not Updating
- **Cause**: Cached recommendations
- **Solution**: Click "Refresh" button to regenerate

### Charts Not Loading
- **Cause**: No recommendation data
- **Solution**: Generate recommendations for at least one user first

---

## 📞 Support

For technical issues or feature requests, contact the system administrator or refer to the main project documentation.

---

**Version**: 1.0  
**Last Updated**: 2024  
**Developed for**: AI-Based Smart Ward Management System
