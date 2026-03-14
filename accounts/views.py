from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
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

        # Colours for progress bar tier
        'resolution_color': (
            'success' if resolution_rate >= 70
            else 'warning' if resolution_rate >= 40
            else 'danger'
        ),
        'satisfaction_color': (
            'success' if satisfaction_index >= 4
            else 'warning' if satisfaction_index >= 2.5
            else 'danger'
        ),
    }


# ── Views ────────────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    user = request.user

    # ── Citizen ────────────────────────────────────────────────────
    if user.role == 'citizen':
        my_complaints    = Complaint.objects.filter(user=user)
        upcoming_meetings = Meeting.objects.filter(
            ward=user.ward, meeting_date__gte=timezone.now()
        ).order_by('meeting_date')[:3]

        context = {
            'total':            my_complaints.count(),
            'resolved':         my_complaints.filter(status='resolved').count(),
            'pending':          my_complaints.filter(status='pending').count(),
            'recent_complaints': my_complaints.order_by('-created_at')[:5],
            'upcoming_meetings': upcoming_meetings,
            'user_ward':        user.ward,
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
        assigned = Complaint.objects.filter(
            ward=user.ward, assigned_worker=user
        ).order_by('-created_at')
        return render(request, 'accounts/citizen_dashboard.html', {
            'total':   assigned.count(),
            'pending': assigned.filter(status='pending').count(),
            'resolved': assigned.filter(status='resolved').count(),
            'recent_complaints': assigned[:5],
            'upcoming_meetings': [],
            'user_ward': user.ward,
        })

    # Fallback
    return render(request, 'accounts/citizen_dashboard.html', {})

from datetime import timedelta

from django.contrib.auth.decorators import user_passes_test

def is_admin(user):
    return user.is_authenticated and (user.role == 'panchayath_admin' or user.is_superuser)

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