# Export Reports Feature - Installation & Usage Guide

## Overview
Admin users can export comprehensive reports in Excel and PDF formats for complaints, scheme beneficiaries, and monthly summaries.

## Installation

### 1. Install Required Packages

```bash
# Activate virtual environment
E:\AI-Based Smart Ward Management System\venv\Scripts\activate

# Install packages
pip install pandas==2.2.0
pip install openpyxl==3.1.2
pip install reportlab==4.0.9
```

Or install from requirements.txt:
```bash
pip install -r requirements.txt
```

### 2. Verify Installation

```bash
python -c "import pandas; import openpyxl; import reportlab; print('All packages installed successfully!')"
```

## Features

### 1. Complaints Report (Excel)
**URL:** `/reports/export/complaints-excel/`

**Features:**
- Export all complaints to Excel (.xlsx)
- Filter by status, ward, priority
- Includes: ID, Title, Description, Category, Priority, Status, Ward, Citizen, Worker, Rating, Dates
- Auto-adjusted column widths
- Professional formatting

**Filters:**
- Status: All, Pending, Assigned, In Progress, Resolved, Rejected
- Ward: All wards or specific ward
- Priority: All, High, Medium, Low

**Example URLs:**
- All complaints: `/reports/export/complaints-excel/`
- Resolved only: `/reports/export/complaints-excel/?status=resolved`
- Ward 1 high priority: `/reports/export/complaints-excel/?ward=1&priority=high`

### 2. Scheme Beneficiaries (Excel)
**URL:** `/reports/export/schemes-excel/`

**Features:**
- Export all scheme applications
- Includes: Scheme Name, Category, Applicant Details, Status, Eligibility Score, Admin Notes
- All schemes and applications in one file
- Auto-formatted columns

**Data Included:**
- Scheme name and category
- Applicant name, username, email
- Ward assignment
- Application status
- Applied date
- Eligibility score
- Admin notes

### 3. Monthly Report (PDF)
**URL:** `/reports/export/monthly-pdf/`

**Features:**
- Professional PDF report with tables
- Executive summary with key metrics
- Category breakdown (top 5)
- Ward performance (top 5)
- Citizen feedback statistics
- Formatted with colors and styling

**Report Sections:**
1. **Executive Summary**
   - Total complaints
   - Resolved complaints
   - Pending complaints
   - High priority issues
   - Resolution rate
   - Average citizen rating
   - Total feedbacks

2. **Top 5 Complaint Categories**
   - Category name
   - Count
   - Percentage

3. **Top 5 Wards by Complaint Volume**
   - Ward number and name
   - Complaint count

**Month Selection:**
- Select from last 6 months
- Default: Current month
- Format: YYYY-MM

**Example URLs:**
- Current month: `/reports/export/monthly-pdf/`
- Specific month: `/reports/export/monthly-pdf/?month=2024-12`

## Access Control

**Required Role:** Panchayath Admin or Superuser

**Security:**
- `@login_required` decorator
- `@user_passes_test(is_admin)` decorator
- Only admins can access export features

## File Naming Convention

### Excel Files:
- Complaints: `complaints_report_YYYYMMDD_HHMMSS.xlsx`
- Schemes: `scheme_beneficiaries_YYYYMMDD_HHMMSS.xlsx`

### PDF Files:
- Monthly: `monthly_report_YYYY_MM.pdf`

## Navigation

**Access from:**
1. Admin sidebar → "Export Reports"
2. Direct URL: `/reports/`

## Technical Details

### Excel Export (pandas + openpyxl)
- Uses pandas DataFrame for data manipulation
- openpyxl engine for Excel file generation
- Auto-adjusts column widths (max 50 characters)
- In-memory file generation (BytesIO)
- Proper MIME type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`

### PDF Export (reportlab)
- A4 page size
- Custom styles with brand colors
- Professional table formatting
- Color-coded headers
- Alternating row backgrounds
- Proper spacing and margins

## Usage Examples

### 1. Export All Complaints
1. Navigate to `/reports/`
2. Click "Download Excel Report" under Complaints Report
3. File downloads automatically

### 2. Export Filtered Complaints
1. Navigate to `/reports/`
2. Select filters (Status, Ward, Priority)
3. Click "Download Excel Report"
4. Filtered data exports

### 3. Export Scheme Beneficiaries
1. Navigate to `/reports/`
2. Click "Download Excel Report" under Scheme Beneficiaries
3. All schemes and applications export

### 4. Generate Monthly PDF
1. Navigate to `/reports/`
2. Select month from dropdown
3. Click "Generate PDF Report"
4. PDF downloads with comprehensive statistics

## Troubleshooting

### Error: "No module named 'pandas'"
**Solution:** Install pandas: `pip install pandas==2.2.0`

### Error: "No module named 'openpyxl'"
**Solution:** Install openpyxl: `pip install openpyxl==3.1.2`

### Error: "No module named 'reportlab'"
**Solution:** Install reportlab: `pip install reportlab==4.0.9`

### Empty Excel File
**Cause:** No data matches filters
**Solution:** Remove filters or check database has data

### PDF Generation Error
**Cause:** Missing data or invalid month format
**Solution:** Ensure month format is YYYY-MM

## Performance Notes

- Excel exports handle large datasets efficiently
- PDF generation is optimized for monthly data
- In-memory file generation (no disk writes)
- Filters reduce export time and file size

## Future Enhancements

Potential additions:
- Date range filters for complaints
- Chart/graph exports
- Email report delivery
- Scheduled automatic reports
- CSV export option
- Custom report templates

## Files Created

1. `reports/views.py` - Export logic
2. `reports/urls.py` - URL routing
3. `reports/templates/reports/reports_dashboard.html` - UI
4. `requirements.txt` - Updated with new packages
5. `ward/urls.py` - Added reports URLs
6. `templates/base.html` - Added navigation link

## Testing

### Test Complaints Export:
```bash
# Visit in browser (as admin)
http://localhost:8000/reports/export/complaints-excel/
```

### Test Schemes Export:
```bash
http://localhost:8000/reports/export/schemes-excel/
```

### Test PDF Export:
```bash
http://localhost:8000/reports/export/monthly-pdf/?month=2024-12
```

## Support

For issues or questions:
1. Check package installation
2. Verify admin access
3. Check database has data
4. Review Django logs for errors
