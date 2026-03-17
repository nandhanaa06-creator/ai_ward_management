import math
from difflib import SequenceMatcher
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta

from .forms import ComplaintForm, TaskCompletionForm
from .models import Complaint, ComplaintStatusHistory


# ---------------------------------------------------------------------------
# AI ENGINE — CATEGORISATION
# ---------------------------------------------------------------------------

# Keyword map: category → list of trigger words
CATEGORY_KEYWORDS = {
    'Water':        ['pipe', 'leak', 'flood', 'drain', 'water', 'sewage', 'tap', 'tank', 'overflow'],
    'Electricity':  ['wire', 'power', 'dark', 'light', 'pole', 'current', 'transformer', 'electric', 'outage'],
    'Roads':        ['pothole', 'road', 'tar', 'street', 'bridge', 'pavement', 'crack', 'broken road'],
    'Sanitation':   ['garbage', 'waste', 'trash', 'dirty', 'smell', 'dump', 'litter', 'clean'],
    'Trees':        ['tree', 'branch', 'fallen', 'root', 'leaves', 'park'],
    'Construction': ['building', 'construction', 'wall', 'encroach', 'concrete', 'debris'],
}

# Keywords that trigger an automatic priority escalation to 'high'
EMERGENCY_KEYWORDS = [
    'danger', 'dangerous', 'immediately', 'urgent', 'accident',
    'emergency', 'fire', 'injury', 'hurt', 'hospital', 'death',
    'electrocution', 'flood', 'collapse',
]


def ai_categorize(text: str) -> str:
    """Return the best-matching category from CATEGORY_KEYWORDS, or 'General'."""
    text_lower = text.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return category
    return 'General'


def ai_escalate_priority(text: str) -> bool:
    """Return True if an emergency keyword is detected in the text."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in EMERGENCY_KEYWORDS)


# ---------------------------------------------------------------------------
# DUPLICATE DETECTION
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# AI ENGINE — ENHANCED DUPLICATE DETECTION
# ---------------------------------------------------------------------------

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Returns distance in meters between two points using Haversine formula.
    """
    if not all([lat1, lon1, lat2, lon2]):
        return float('inf')
    
    R = 6371000 # radius of Earth in meters
    phi1, phi2 = math.radians(float(lat1)), math.radians(float(lat2))
    dphi = math.radians(float(lat2 - lat1))
    dlambda = math.radians(float(lon2 - lon1))

    a = math.sin(dphi / 2)**2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def get_text_similarity(str1, str2):
    """Returns ratio (0 to 1) of similarity between two strings."""
    if not str1 or not str2:
        return 0.0
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

def check_enhanced_duplicates(new_complaint):
    """
    Compares the new complaint against existing 'Open' (pending, assigned, in_progress)
    complaints in the same ward.
    """
    open_statuses = ['pending', 'assigned', 'in_progress']
    candidates = Complaint.objects.filter(
        ward=new_complaint.ward,
        status__in=open_statuses
    ).exclude(id=new_complaint.id)

    best_match = None
    highest_sim = 0.0

    for cand in candidates:
        # 1. Proximity check (50m)
        dist = calculate_distance(
            new_complaint.latitude, new_complaint.longitude,
            cand.latitude, cand.longitude
        )
        
        if dist <= 100:
            # 2. Text similarity check (70%+)
            sim = get_text_similarity(new_complaint.description, cand.description)
            if sim >= 0.75 and sim > highest_sim:
                highest_sim = sim
                best_match = cand

    return best_match


# ---------------------------------------------------------------------------
# VIEWS
# ---------------------------------------------------------------------------

@login_required
def report_complaint(request):
    """
    Main view for citizens to submit a new complaint.
    Responsibilities:
      1. Validate the ComplaintForm.
      2. Auto-assign the logged-in user and their ward.
      3. Run the AI categorisation engine on the description.
      4. Run sentiment-based priority escalation.
      5. Run duplicate detection against recent ward complaints.
      6. Save and redirect with an appropriate feedback message.
    """
    if request.method == 'POST':
        form = ComplaintForm(request.POST, request.FILES)
        if form.is_valid():
            complaint = form.save(commit=False)

            # --- Auth assignment ---
            complaint.user = request.user
            complaint.ward = request.user.ward  # auto-fill from user profile

            # --- AI CATEGORISATION ENGINE ---
            description = form.cleaned_data.get('description', '')
            title = form.cleaned_data.get('title', '')
            full_text = f"{title} {description}"

            complaint.category = ai_categorize(full_text)

            # --- SENTIMENT / EMERGENCY ESCALATION ---
            if ai_escalate_priority(full_text):
                complaint.priority = 'high'
                messages.warning(
                    request,
                    '⚠️ Your complaint has been automatically escalated to '
                    '<strong>High Priority</strong> due to emergency keywords detected.',
                    extra_tags='safe',
                )

            # --- ENHANCED DUPLICATE DETECTION (GPS + AI) ---
            potential_match = check_enhanced_duplicates(complaint)
            if potential_match:
                complaint.is_duplicate = True
                complaint.potential_duplicate_of = potential_match
                messages.info(
                    request,
                    'ℹ️ AI Detection: A similar complaint was found nearby. '
                    'Your report has been flagged for verification by the Ward Member.',
                )

            complaint.save()

            messages.success(
                request,
                f'✅ Your complaint has been submitted successfully! '
                f'Category auto-detected: <strong>{complaint.category}</strong>.',
                extra_tags='safe',
            )
            return redirect('complaint_list')

    else:
        form = ComplaintForm()

    context = {
        'form': form,
        # Progress steps — we are always on step 2 (form fill) when this view renders
        'progress_step': 2,
        'progress_steps': ['Login', 'Fill Details', 'Submit'],
    }
    return render(request, 'complaints/report_issue.html', context)


@login_required
def complaint_list(request):
    """
    Show complaints relevant to the logged-in user's role.
    Ward members / admins see all complaints in their ward;
    citizens see only their own.
    """
    privileged_roles = ('ward_member', 'panchayath_admin', 'field_worker')

    if request.user.role in privileged_roles:
        complaints = Complaint.objects.filter(
            ward=request.user.ward
        ).order_by('-created_at')
    else:
        complaints = Complaint.objects.filter(
            user=request.user
        ).order_by('-created_at')

    return render(request, 'complaints/list.html', {'complaints': complaints})


@login_required
def complaint_detail(request, complaint_id):
    """Simple detail view for a single complaint."""
    complaint = get_object_or_404(Complaint, id=complaint_id)
    return render(request, 'complaints/detail.html', {'complaint': complaint})


@login_required
def worker_task_detail(request, complaint_id):
    """
    Dedicated view for field workers to see task specifics and submit resolution.
    Optimized for high-impact mobile actions.
    """
    complaint = get_object_or_404(Complaint, id=complaint_id)
    
    # Security: only the assigned worker or admin can view this tactical layout
    if request.user.role not in ('field_worker', 'panchayath_admin', 'ward_member') and not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    form = TaskCompletionForm()
    
    context = {
        'complaint': complaint,
        'form': form,
        'history': complaint.status_history.all().order_by('-created_at')
    }
    return render(request, 'complaints/worker_task_detail.html', context)


@login_required
def complete_task(request, complaint_id):
    """
    POST-only view to handle task completion with proof.
    """
    complaint = get_object_or_404(Complaint, id=complaint_id)
    
    if request.method == 'POST':
        form = TaskCompletionForm(request.POST, request.FILES)
        if form.is_valid():
            # Create status history record
            ComplaintStatusHistory.objects.create(
                complaint=complaint,
                new_status='resolved',
                description=form.cleaned_data['description'],
                proof_image=form.cleaned_data['resolution_image'],
                actor=request.user
            )
            
            # Update complaint status
            complaint.status = 'resolved'
            complaint.resolution_image = form.cleaned_data['resolution_image']
            complaint.save()
            
            messages.success(request, '✅ Task completed and marked as Resolved.')
            return redirect('complaint_list')
        else:
            messages.error(request, 'Please provide both a description and proof photo.')
            
    return redirect('worker_task_detail', complaint_id=complaint.id)


@login_required
def submit_feedback(request, complaint_id):
    """
    Citizen view: Rate the resolution of the complaint.
    If rating is 1 or 2 stars -> Re-open as 'pending' + 'high' priority.
    """
    complaint = get_object_or_404(Complaint, id=complaint_id)

    # Security check: only the owner can submit feedback
    if request.user != complaint.user:
        messages.error(request, 'You do not have permission to rate this complaint.')
        return redirect('dashboard')

    if request.method == 'POST':
        try:
            rating = int(request.POST.get('rating', 0))
            if 1 <= rating <= 5:
                complaint.citizen_rating = rating
                
                # AI Re-Opening Logic
                if rating <= 2:
                    complaint.status = 'pending'
                    complaint.priority = 'high'
                    messages.warning(
                        request, 
                        '⚠️ We are sorry you were unhappy with the resolution. '
                        'Your complaint has been re-opened with High Priority for the Ward Member to review.'
                    )
                else:
                    messages.success(request, '✅ Thank you for your feedback! Glad we could help.')
                
                complaint.save()
            else:
                messages.error(request, 'Invalid rating value.')
        except ValueError:
            messages.error(request, 'Invalid input.')
            
    return redirect('complaint_detail', complaint_id=complaint.id)


@login_required
def post_complaint_message(request, complaint_id):
    """
    Admin/Ward Member view: Post a message on a complaint thread.
    Allows for Admin-to-Citizen direct communication.
    """
    if request.user.role not in ('panchayath_admin', 'ward_member', 'is_superuser'):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    complaint = get_object_or_404(Complaint, id=complaint_id)

    if request.method == 'POST':
        message_text = request.POST.get('message', '').strip()
        if message_text:
            from .models import ComplaintMessage
            ComplaintMessage.objects.create(
                complaint=complaint,
                sender=request.user,
                message=message_text
            )
            messages.success(request, 'Message posted successfully.')
        else:
            messages.error(request, 'Message cannot be empty.')
            
    return redirect('complaint_detail', complaint_id=complaint.id)


@login_required
def reassign_worker(request, complaint_id):
    """
    Admin control to reassign a complaint to a different user.
    """
    if not (request.user.role == 'panchayath_admin' or request.user.is_superuser):
         messages.error(request, 'Access denied. Administrative privileges required.')
         return redirect('dashboard')
         
    complaint = get_object_or_404(Complaint, id=complaint_id)
    
    if request.method == 'POST':
        worker_id = request.POST.get('worker_id')
        try:
            from accounts.models import User
            worker = User.objects.get(id=worker_id)
            complaint.assigned_worker = worker
            complaint.status = 'assigned' # bump status back to assigned 
            complaint.save()
            messages.success(request, f'Complaint #{complaint.id} successfully reassigned to {worker.username}.')
        except User.DoesNotExist:
            messages.error(request, 'Selected worker does not exist.')
            
    # Typically this redirects back to wherever the admin was
    return redirect(request.META.get('HTTP_REFERER', 'admin_dashboard'))


@login_required
def merge_complaint(request, duplicate_id):
    """
    Ward Member action to merge a flagged duplicate into a master complaint.
    """
    if request.user.role not in ('ward_member', 'panchayath_admin', 'is_superuser'):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    duplicate = get_object_or_404(Complaint, id=duplicate_id)
    master_id = request.POST.get('master_id')
    
    if request.method == 'POST' and master_id:
        master = get_object_or_404(Complaint, id=master_id)
        
        duplicate.parent_complaint = master
        duplicate.status = 'rejected'  # Mark as rejected because it's a duplicate
        duplicate.save()
        
        # Log in history
        from .models import ComplaintStatusHistory
        ComplaintStatusHistory.objects.create(
            complaint=duplicate,
            new_status='rejected',
            description=f"Merged into master complaint #{master.id} by Ward Member.",
            actor=request.user
        )
        
        messages.success(request, f'✅ Complaint #{duplicate.id} successfully merged into #{master.id}.')
        return redirect(request.META.get('HTTP_REFERER', 'admin_dashboard'))
        
    return redirect('complaint_detail', complaint_id=duplicate_id)

@login_required
def suggest_worker(request, complaint_id):
    """
    AI Logic: Returns the 'Best Fit' field worker for a complaint.
    Criteria:
    1. Lowest current task load (assigned or in_progress).
    2. Geographically closest to the complaint coordinates.
    """
    if request.user.role not in ('ward_member', 'panchayath_admin', 'is_superuser'):
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    complaint = get_object_or_404(Complaint, id=complaint_id)
    if not complaint.latitude or not complaint.longitude:
        return JsonResponse({'error': 'Complaint lacks GPS coordinates'}, status=400)
        
    from accounts.models import User
    # Only workers in the same ward
    workers = User.objects.filter(role='field_worker', ward=complaint.ward)
    
    if not workers.exists():
        return JsonResponse({'error': 'No field workers available in this ward'}, status=404)
        
    best_worker = None
    min_score = float('inf')
    
    for worker in workers:
        # Task Load Score
        load = Complaint.objects.filter(assigned_worker=worker, status__in=['assigned', 'in_progress']).count()
        
        # Distance Score (in km for scaling)
        dist_m = calculate_distance(complaint.latitude, complaint.longitude, worker.latitude, worker.longitude)
        dist_km = (dist_m / 1000.0) if dist_m != float('inf') else 100.0 # penalty for no location
        
        # Heuristic: Score = (Load * 5) + Distance_KM
        # This prioritizes load (1 extra task is like being 5km further away)
        score = (load * 5) + dist_km
        
        if score < min_score:
            min_score = score
            best_worker = worker
            
    if best_worker:
        active_load = Complaint.objects.filter(assigned_worker=best_worker, status__in=['assigned', 'in_progress']).count()
        dist_final = calculate_distance(complaint.latitude, complaint.longitude, best_worker.latitude, best_worker.longitude)
        
        return JsonResponse({
            'worker_id': best_worker.id,
            'username': best_worker.username,
            'load': active_load,
            'distance_m': round(dist_final, 1) if dist_final != float('inf') else "Unknown"
        })
        
    return JsonResponse({'error': 'Could not determine best worker'}, status=500)
