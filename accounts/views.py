from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Avg, Q
from django.utils import timezone

# Import Models
from .models import User, Ward, CitizenProfile
from complaints.models import Complaint
from governance.models import Meeting

# Import Forms
from .forms import CitizenRegistrationForm, WardForm, CitizenProfileForm


# ── Helpers ─────────────────────────────────────────────────────────────────

def _ward_member_context(user):
    """
    Build the full data context for the Ward Member Decision Support Dashboard.
    Uses Django Count, Avg, and annotate-based aggregations.
    """
    ward = user.ward

    # ── Base querysets ─────────────────────────────────────────────
    ward_complaints = Complaint.objects.filter(ward=ward)
    total_complaints = ward_complaints.count()

    resolved_complaints   = ward_complaints.filter(status='resolved')
    pending_complaints    = ward_complaints.filter(status='pending')
    in_progress_complaints = ward_complaints.filter(status='in_progress')

    # ── 1. Resolution Efficiency (%) ───────────────────────────────
    resolved_count = resolved_complaints.count()
    resolution_rate = (
        round((resolved_count / total_complaints) * 100)
        if total_complaints > 0 else 0
    )

    # ── 2. Satisfaction Index (avg citizen_rating on resolved) ─────
    satisfaction_data = resolved_complaints.aggregate(avg=Avg('citizen_rating'))
    satisfaction_index = round(satisfaction_data['avg'] or 0, 1)
    # Convert to a 0–100 scale for a progress bar (rating is 1–5)
    satisfaction_pct = round((satisfaction_index / 5) * 100) if satisfaction_index else 0

    # ── 3. Hotspot Detection — top 3 categories with pending issues ─
    hotspots = (
        pending_complaints
        .exclude(category__isnull=True)
        .exclude(category='')
        .values('category')
        .annotate(count=Count('id'))
        .order_by('-count')[:3]
    )
    # Max count for bar scaling
    hotspot_max = hotspots[0]['count'] if hotspots else 1

    # ── 4. Upcoming Meetings (next 3 from today) ───────────────────
    upcoming_meetings = (
        Meeting.objects
        .filter(ward=ward, meeting_date__gte=timezone.now())
        .order_by('meeting_date')[:3]
    )

    # ── 5. Priority Alerts — AI-escalated High-priority open issues ─
    priority_alerts = (
        ward_complaints
        .filter(priority='high')
        .exclude(status='resolved')
        .exclude(status='rejected')
        .order_by('-created_at')[:5]
    )

    # ── 6. Additional stat tiles ───────────────────────────────────
    total_citizens = User.objects.filter(ward=ward, role='citizen').count()
    duplicate_count = ward_complaints.filter(is_duplicate=True).count()

    # Status breakdown for mini table
    in_progress_count = in_progress_complaints.count()
    assigned_count    = ward_complaints.filter(status='assigned').count()
    rejected_count    = ward_complaints.filter(status='rejected').count()

    # ── 7. Potential Duplicates (AI Flagged) ──────────────────────
    flagged_duplicates = ward_complaints.filter(is_duplicate=True, parent_complaint__isnull=True).order_by('-created_at')

    return {
        'ward':               ward,
        'ward_name':          str(ward) if ward else 'No Ward Assigned',

        # Complaint stats
        'total':              total_complaints,
        'resolved':           resolved_count,
        'pending':            pending_complaints.count(),
        'new_issues':         pending_complaints.count(),
        'in_progress':        in_progress_count,
        'assigned':           assigned_count,
        'rejected':           rejected_count,
        'duplicate_count':    duplicate_count,

        # KPIs
        'resolution_rate':    resolution_rate,
        'satisfaction_index': satisfaction_index,
        'satisfaction_pct':   satisfaction_pct,
        'total_citizens':     total_citizens,

        # Smart data
        'hotspots':           hotspots,
        'hotspot_max':        hotspot_max,
        'upcoming_meetings':  upcoming_meetings,
        'priority_alerts':    priority_alerts,
        'priority_alert_count': priority_alerts.count(),
        'flagged_duplicates': flagged_duplicates,
        'flagged_duplicate_count': flagged_duplicates.count(),

        # ── 8. Ward Health & Predictive Stress ───────────────────────
        # Stress Score = (Unresolved / Workers) + (Avg Days to Resolve)
        'unresolved_count': (pending_complaints.count() + in_progress_count + assigned_count),
        'worker_count': User.objects.filter(ward=ward, role='field_worker').count() or 1,
    }
    # ── 9. Calculation Logic ───────────────────────────────────────
    unresolved = context['unresolved_count']
    workers = context['worker_count']
    
    # Average Days to Resolve (Python-side for duration flexibility)
    resolve_durations = []
    for c in resolved_complaints:
        dur = (c.updated_at - c.created_at).total_seconds() / 86400.0
        resolve_durations.append(dur)
    
    avg_days = sum(resolve_durations) / len(resolve_durations) if resolve_durations else 1.5
    context['avg_resolve_days'] = round(avg_days, 1)
    
    # Stress Score Calculation
    stress_score = (unresolved / workers) + avg_days
    context['stress_score'] = round(stress_score, 1)
    
    # Predicted Resolution Time (Hours for Current Week)
    context['predicted_res_time'] = round((unresolved * avg_days * 24) / workers)

    # ── 10. Heatmap Data (Predictive) ──────────────────────────────
    context['heatmap_data'] = [
        {
            'lat': round(float(c['latitude']), 4), 
            'lng': round(float(c['longitude']), 4), 
            'count': 1,
        } for c in ward_complaints.filter(status__in=['pending', 'assigned', 'in_progress']).values('latitude', 'longitude') if c['latitude'] and c['longitude']
    ]

    # Colours for UI indicators
    context['resolution_color'] = 'success' if resolution_rate >= 70 else 'warning' if resolution_rate >= 40 else 'danger'
    context['satisfaction_color'] = 'success' if satisfaction_index >= 4 else 'warning' if satisfaction_index >= 2.5 else 'danger'
    context['stress_color'] = 'danger' if stress_score > 8 else 'warning' if stress_score > 5 else 'success'

    return context


# ── Views ────────────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    user = request.user

    # ── Superuser ─────────────────────────────────────────────────
    if user.is_superuser:
        return redirect('admin_dashboard')

    # ── Citizen ────────────────────────────────────────────────────
    if user.role == 'citizen':
        my_complaints = Complaint.objects.filter(user=user)
        profile, _ = CitizenProfile.objects.get_or_create(user=user)
        all_meetings = Meeting.objects.filter(ward=user.ward).order_by('-meeting_date')
        upcoming_meetings = all_meetings.filter(meeting_date__gte=timezone.now()).order_by('meeting_date')[:2]
        past_meetings = all_meetings.filter(meeting_date__lt=timezone.now())[:2]

        context = {
            'profile': profile,
            'total': my_complaints.count(),
            # Action Pending = Pending + In Progress + Urgent Review (for comprehensive view)
            'pending': my_complaints.filter(status__in=['pending', 'in_progress', 'urgent_review']).count(),
            'resolved': my_complaints.filter(status='resolved').count(),
            'recent_complaints': my_complaints.order_by('-created_at')[:5],
            'upcoming_meetings': upcoming_meetings,
            'past_meetings': past_meetings,
            'user_ward': user.ward,
        }
        return render(request, 'accounts/citizen_dashboard.html', context)

    # ── Ward Member — full Decision Support Dashboard ───────────────
    if user.role in ('ward_member', 'panchayath_admin'):
        
        # Admin Override: if it's an admin, we provide a link to the God Mode dashboard 
        # inside the Ward Member context if they want to view ward-specific data, 
        # but the primary redirection for admin should go to admin_dashboard.
        if user.role == 'panchayath_admin' and 'ward_view' not in request.GET:
             return redirect('admin_dashboard')

        context = _ward_member_context(user)
        return render(request, 'accounts/ward_dashboard_advanced.html', context)


    # ── Field Worker ───────────────────────────────────────────────
    if user.role == 'field_worker':
        # Tasks assigned specifically to this worker
        my_tasks = Complaint.objects.filter(
            assigned_worker=user
        ).exclude(status='resolved').exclude(status='rejected').order_by('-priority', '-created_at')
        
        resolved_tasks = Complaint.objects.filter(
            assigned_worker=user, status='resolved'
        ).count()

        context = {
            'total_assigned': my_tasks.count(),
            'resolved_count': resolved_tasks,
            'active_tasks': my_tasks,
            'user_ward': user.ward,
        }
        return render(request, 'accounts/worker_dashboard.html', context)

    # Fallback
    return render(request, 'accounts/citizen_dashboard.html', {})


@login_required
@user_passes_test(lambda u: u.role == 'panchayath_admin' or u.is_superuser)
def manage_workers(request):
    """
    Worker management hub for Panchayath Admins.
    Allows listing all workers and recruiting new ones.
    """
    from django.db.models import Count, Q
    from .models import User, Ward
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        ward_id = request.POST.get('ward')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, f"Error: Username '{username}' is already taken.")
        else:
            ward = Ward.objects.get(id=ward_id) if ward_id else None
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role='field_worker',
                ward=ward
            )
            messages.success(request, f"Successfully recruited {user.get_full_name() or user.username} as an Authorized Field Worker.")
            return redirect('manage_workers')

    # Fetch all workers with active task counts
    workers = User.objects.filter(role='field_worker').annotate(
        active_tasks=Count('assigned_tasks', filter=Q(assigned_tasks__status__in=['assigned', 'in_progress', 'urgent_review']))
    ).order_by('-date_joined')
    
    wards = Ward.objects.all()
    
    return render(request, 'accounts/manage_workers.html', {
        'workers': workers,
        'wards': wards
    })

from datetime import timedelta, date
import random
from django.db.models import Count, Q, Avg
from django.utils import timezone

from django.contrib.auth.decorators import user_passes_test

def is_admin(user):
    return user.is_authenticated and (user.role == 'panchayath_admin' or user.is_superuser)

# ---------------------------------------------------------------------------
# IOT & SMART INFRASTRUCTURE UTILITIES
# ---------------------------------------------------------------------------

def get_iot_telemetry(admin_user):
    """
    Simulates real-time IoT sensor data and triggers automatic complaints.
    """
    # Simulate values 20% - 90%
    water_level = random.randint(20, 95) # Slightly higher upper bound to favor demo triggers
    waste_level = random.randint(20, 95)
    
    telemetry = {
        'water': {'level': water_level, 'status': 'Stable', 'color': 'cyan'},
        'waste': {'level': waste_level, 'status': 'Stable', 'color': 'cyan'}
    }
    
    # Threshold check (> 85%)
    # We assign to a default ward or the first ward for simulation purposes
    target_ward = Ward.objects.first()
    
    if water_level > 85:
        telemetry['water']['status'] = 'CRITICAL'
        telemetry['water']['color'] = 'danger'
        # Check if an auto-complaint already exists for this in the last hour to prevent spam
        recent_exists = Complaint.objects.filter(
            title__contains="IOT_AUTO_SIGNAL: Water Tank Overflow",
            created_at__gte=timezone.now() - timedelta(hours=1)
        ).exists()
        
        if not recent_exists:
            Complaint.objects.create(
                user=admin_user,
                ward=target_ward,
                title="[IOT_AUTO_SIGNAL] Water Tank Overflow Danger",
                description=f"Automated Alert: Central Water Tank Level at {water_level}%. Immediate intervention required to prevent overflow.",
                category="Public Works",
                priority="high",
                status="pending"
            )

    if waste_level > 85:
        telemetry['waste']['status'] = 'CRITICAL'
        telemetry['waste']['color'] = 'danger'
        recent_exists = Complaint.objects.filter(
            title__contains="IOT_AUTO_SIGNAL: Waste Bin Full",
            created_at__gte=timezone.now() - timedelta(hours=1)
        ).exists()
        
        if not recent_exists:
            Complaint.objects.create(
                user=admin_user,
                ward=target_ward,
                title="[IOT_AUTO_SIGNAL] Waste Bin Capacity Breach",
                description=f"Automated Alert: Smart Waste Bin at Zone A-1 is at {waste_level}% capacity. Routing sanitation crew required.",
                category="Sanitation",
                priority="high",
                status="pending"
            )
            
    return telemetry

# ---------------------------------------------------------------------------
# PREDICTIVE GOVERNANCE UTILITIES
# ---------------------------------------------------------------------------

def get_predictive_analytics(wards, total_days=90, forecast_days=30):
    """
    Calculates Ward Stress Scores and generates a 30-day forecast.
    """
    # 1. Ward Stress Scoring
    risk_wards = []
    for ward in wards:
        # Get active workers in this ward
        active_workers = User.objects.filter(role='field_worker', ward=ward).count()
        
        # Stress Score = Pending / (Active Workers + 1)
        score = ward.pending_count / (active_workers + 0.5) # using 0.5 to avoid heavy bias if 0 workers
        
        risk_level = "Normal"
        risk_color = "success"
        if score > 8:
            risk_level = "High Risk"
            risk_color = "danger"
        elif score > 4:
            risk_level = "Elevated"
            risk_color = "warning"
            
        risk_wards.append({
            'ward': ward,
            'score': round(score, 1),
            'risk_level': risk_level,
            'risk_color': risk_color,
            'active_workers': active_workers
        })

    # 2. Daily Average Forecast
    # Calculate average complaints per day over last 90 days
    since_date = timezone.now() - timedelta(days=total_days)
    historical_complaints = Complaint.objects.filter(created_at__gte=since_date)
    
    total_count = historical_complaints.count()
    daily_avg = total_count / total_days if total_days > 0 else 0
    
    # Generate labels (next 30 days) and projected cumulative growth
    labels = []
    forecast_data = []
    
    current_total = Complaint.objects.count()
    for i in range(1, forecast_days + 1):
        future_date = date.today() + timedelta(days=i)
        labels.append(future_date.strftime('%d %b'))
        # Projected linear growth based on historical daily average
        projected_val = current_total + (daily_avg * i)
        forecast_data.append(round(projected_val))

    return {
        'risk_wards': risk_wards,
        'forecast_labels': labels,
        'forecast_data': forecast_data,
        'daily_avg': round(daily_avg, 2)
    }

@user_passes_test(is_admin, login_url='/accounts/login/')
def citizens_list(request):
    """
    Display all registered citizens with their details.
    """
    from django.db.models import Count
    
    # Get all citizens with complaint count
    citizens = User.objects.filter(role='citizen').annotate(
        complaint_count=Count('complaints')
    ).order_by('-date_joined')
    
    # Stats
    total_citizens = citizens.count()
    assigned_citizens = citizens.filter(ward__isnull=False).count()
    unassigned_citizens = citizens.filter(ward__isnull=True).count()
    
    context = {
        'citizens': citizens,
        'total_citizens': total_citizens,
        'assigned_citizens': assigned_citizens,
        'unassigned_citizens': unassigned_citizens,
    }
    
    return render(request, 'accounts/citizens_list.html', context)


@user_passes_test(is_admin, login_url='/accounts/login/')
def admin_dashboard(request):
    """
    God Mode Interface for Panchayath Admin.
    Provides global oversight, smart notifications, and cross-ward management.
    """

    # 1. Global Complaint Hub 
    complaints = Complaint.objects.all().order_by('-created_at')
    
    # ── Filters ──
    status_filter = request.GET.get('status')
    priority_filter = request.GET.get('priority')
    
    if status_filter:
        complaints = complaints.filter(status=status_filter)
    if priority_filter:
        complaints = complaints.filter(priority=priority_filter)

    # 2. Smart Notifications
    forty_eight_hours_ago = timezone.now() - timedelta(hours=48)
    
    urgent_reviews = Complaint.objects.filter(
        status='pending',
        created_at__lte=forty_eight_hours_ago
    ).order_by('created_at')

    low_ratings = Complaint.objects.filter(
        citizen_rating__lte=2
    ).order_by('-updated_at')

    # 3. Overview Stats
    total_complaints = Complaint.objects.count()
    resolved_complaints = Complaint.objects.filter(status='resolved').count()
    pending_complaints = Complaint.objects.filter(status='pending').count()
    
    resolved_rate = (
        round((resolved_complaints / total_complaints) * 100)
        if total_complaints > 0 else 0
    )
    
    # 4. Ward & User Management base stats
    wards = Ward.objects.annotate(
        complaint_count=Count('complaints'),
        pending_count=Count('complaints', filter=Q(complaints__status='pending'))
    ).order_by('ward_number')
    
    hotspot_ward = wards.order_by('-pending_count').first()
    
    # Total citizens count
    total_citizens = User.objects.filter(role='citizen').count()
    
    # 5. Field Worker Lifecycle Telemetry
    workers = User.objects.filter(role='field_worker').annotate(
        task_count_annotation=Count('assigned_tasks', filter=Q(assigned_tasks__status__in=['assigned', 'in_progress'])),
        resolved_tasks=Count('assigned_tasks', filter=Q(assigned_tasks__status='resolved'))
    )


    # 6. Predictive Governance Data
    predictive_data = get_predictive_analytics(wards)
    
    # 7. IoT Telemetry simulation
    iot_data = get_iot_telemetry(request.user)

    context = {
        'complaints': complaints,
        'urgent_reviews': urgent_reviews,
        'urgent_count': urgent_reviews.count(),
        'low_ratings': low_ratings,
        'low_rating_count': low_ratings.count(),
        
        'total_complaints': total_complaints,
        'resolved_complaints': resolved_complaints,
        'pending_complaints': pending_complaints,
        'resolved_rate': resolved_rate,
        'hotspot_ward': hotspot_ward,
        'wards': wards,
        'workers': workers,
        'total_citizens': total_citizens,
        
        'predictive': predictive_data,
        'iot': iot_data,
        
        # Current active filters to repopulate UI
        'current_status': status_filter,
        'current_priority': priority_filter,
    }
    
    return render(request, 'accounts/admin_dashboard.html', context)



def signup(request):
    if request.method == 'POST':
        form = CitizenRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = CitizenRegistrationForm()
    return render(request, 'accounts/signup.html', {'form': form})

from django.contrib import messages

@login_required
def manage_wards(request):
    """
    Secure administrative interface to manage the Ward structure.
    Restricted to panchayath_admin or superuser.
    """
    if not (request.user.role == 'panchayath_admin' or request.user.is_superuser):
        messages.error(request, 'Access denied. Administrator privileges required.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = WardForm(request.POST)
        if form.is_valid():
            ward = form.save()
            messages.success(request, f'✅ Ward {ward.ward_number} - "{ward.ward_name}" has been successfully added!')
            return redirect('manage_wards')
        else:
            messages.error(request, 'Failed to add ward. Please ensure the ward number is unique.')
    else:
        form = WardForm()

    # 1. Fetch all wards and annotate with the count of citizens residing in them
    wards = Ward.objects.annotate(
        citizen_count=Count('user', filter=Q(user__role='citizen'))
    ).order_by('ward_number')

    # 2. Smart Logic: Count total unassigned citizens globally
    unassigned_count = User.objects.filter(role='citizen', ward__isnull=True).count()

    context = {
        'form': form,
        'wards': wards,
        'unassigned_count': unassigned_count,
    }
    return render(request, 'accounts/manage_wards.html', context)



@login_required
def update_profile(request):
    profile, _ = CitizenProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = CitizenProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = CitizenProfileForm(instance=profile)
    return render(request, 'accounts/update_profile.html', {'form': form})


@login_required
def ward_performance_report(request):
    """
    Mock report view — generates a plain-text summary of the ward's
    performance metrics. In production this could render a PDF.
    """
    if request.user.role not in ('ward_member', 'panchayath_admin'):
        return redirect('dashboard')

    context = _ward_member_context(request.user)
    return render(request, 'accounts/ward_report.html', context)