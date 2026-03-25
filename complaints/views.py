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
from .models import Complaint, ComplaintStatusHistory, ComplaintFeedback

# Import AI prediction modules
from ai_model.predict import predict_category
from ai_model.priority_model import predict_priority
from ai_model.duplicate_detection import find_duplicate_complaints


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
    'electrocution', 'flood', 'collapse', 'broken', 'immediate',
]


def ai_categorize(text: str) -> str:
    """Return the best-matching category from CATEGORY_KEYWORDS, or 'General'."""
    text_lower = text.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return category
    return 'General'


def ai_get_urgency_reason(text: str) -> str:
    """
    Scans text for emergency keywords and returns a comma-separated string 
    of detected words, or None if no match.
    """
    text_lower = text.lower()
    detected = [kw for kw in EMERGENCY_KEYWORDS if kw in text_lower]
    if detected:
        return ", ".join(detected)
    return None


def ai_escalate_priority(text: str) -> bool:
    """Return True if an emergency keyword is detected in the text."""
    return ai_get_urgency_reason(text) is not None


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

            # --- AI CATEGORISATION ENGINE (Machine Learning) ---
            description = form.cleaned_data.get('description', '')
            title = form.cleaned_data.get('title', '')
            full_text = f"{title} {description}"

            # Use AI model to predict category
            try:
                ai_result = predict_category(full_text)
                complaint.category = ai_result['category']
                ai_confidence = ai_result['confidence']
                
                # Store AI analysis reason with confidence score
                if ai_confidence > 0:
                    complaint.ai_analysis_reason = f"AI Predicted Category: {ai_result['category']} (Confidence: {ai_confidence:.1f}%)"
            except Exception as e:
                # Fallback to keyword-based categorization if AI fails
                print(f"AI categorization failed: {e}")
                complaint.category = ai_categorize(full_text)
                complaint.ai_analysis_reason = "Fallback: Keyword-based categorization"

            # --- AI PRIORITY PREDICTION (Machine Learning) ---
            try:
                priority_result = predict_priority(full_text, complaint.category)
                complaint.priority = priority_result['priority']
                priority_confidence = priority_result['confidence']
                
                # Append priority prediction to AI analysis reason
                priority_reason = f"AI Predicted Priority: {priority_result['priority'].upper()} (Confidence: {priority_confidence:.1f}%)"
                if priority_result.get('reason'):
                    priority_reason += f" - {priority_result['reason']}"
                
                if complaint.ai_analysis_reason:
                    complaint.ai_analysis_reason += f"; {priority_reason}"
                else:
                    complaint.ai_analysis_reason = priority_reason
                
                # Auto-escalate status if high priority
                if complaint.priority == 'high':
                    complaint.status = 'urgent_review'
                    messages.warning(
                        request,
                        f'⚠️ Your complaint has been automatically escalated to '
                        f'<strong>High Priority (Urgent Review)</strong>. {priority_result.get("reason", "")}',
                        extra_tags='safe',
                    )
            except Exception as e:
                # Fallback to keyword-based priority if AI fails
                print(f"AI priority prediction failed: {e}")
                urgency_reason = ai_get_urgency_reason(full_text)
                if urgency_reason:
                    complaint.priority = 'high'
                    complaint.status = 'urgent_review'
                else:
                    complaint.priority = 'medium'  # Default priority

            # --- ENHANCED DUPLICATE DETECTION (AI + GPS) ---
            # Get existing open complaints in the same ward
            from datetime import timedelta
            time_window = timezone.now() - timedelta(days=30)
            
            existing_complaints = Complaint.objects.filter(
                ward=complaint.ward,
                status__in=['pending', 'assigned', 'in_progress', 'urgent_review'],
                created_at__gte=time_window
            ).exclude(id=complaint.id).values(
                'id', 'title', 'description', 'category', 
                'latitude', 'longitude', 'status', 'created_at'
            )
            
            # Prepare data for duplicate detection
            existing_data = [
                {
                    'id': c['id'],
                    'title': c['title'],
                    'text': c['description'],
                    'category': c['category'],
                    'latitude': c['latitude'],
                    'longitude': c['longitude'],
                    'status': c['status'],
                    'created_at': c['created_at']
                }
                for c in existing_complaints
            ]
            
            # Run AI duplicate detection
            try:
                duplicate_result = find_duplicate_complaints(
                    complaint.description,
                    complaint.title,
                    existing_data,
                    category=complaint.category,
                    latitude=complaint.latitude,
                    longitude=complaint.longitude
                )
                
                if duplicate_result['is_duplicate']:
                    complaint.is_duplicate = True
                    
                    # Link to the most similar complaint
                    if duplicate_result['duplicate_complaint_id']:
                        try:
                            parent = Complaint.objects.get(id=duplicate_result['duplicate_complaint_id'])
                            complaint.potential_duplicate_of = parent
                        except Complaint.DoesNotExist:
                            pass
                    
                    # Update AI analysis reason
                    similarity_pct = duplicate_result['highest_similarity_percentage']
                    if complaint.ai_analysis_reason:
                        complaint.ai_analysis_reason += f"; Duplicate Detection: {similarity_pct}% similar to Complaint #{duplicate_result['duplicate_complaint_id']}"
                    else:
                        complaint.ai_analysis_reason = f"Duplicate Detection: {similarity_pct}% similar to Complaint #{duplicate_result['duplicate_complaint_id']}"
                    
                    # Show warning to user
                    similar_complaint = duplicate_result['similar_complaints'][0]
                    messages.warning(
                        request,
                        f'⚠️ AI Detection: A similar complaint already exists '
                        f'(#{similar_complaint["id"]}: {similar_complaint["title"]}). '
                        f'Similarity: {similar_complaint["similarity_percentage"]}%. '
                        f'Your complaint has been flagged for review by the Ward Member.',
                        extra_tags='safe'
                    )
            except Exception as e:
                print(f"Duplicate detection failed: {e}")
                # Fallback to old duplicate detection if AI fails
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


def complaint_list(request):
    """
    Show complaints relevant to the logged-in user's role.
    Admins see all complaints (Unified Spectrum);
    Ward members see their ward's complaints;
    Citizens see only their own.
    """
    status_filter = request.GET.get('status', 'all')
    privileged_roles = ('ward_member', 'field_worker')
    
    # ── Role-Based Queryset ──
    if request.user.role == 'panchayath_admin' or request.user.is_superuser:
        complaints = Complaint.objects.all()
    elif request.user.role in privileged_roles:
        complaints = Complaint.objects.filter(ward=request.user.ward)
    else:
        complaints = Complaint.objects.filter(user=request.user)

    # ── Unified Filtering Logic ──
    if status_filter and status_filter != 'all':
        if status_filter == 'pending':
            # Include 'pending', 'in_progress', and 'urgent_review' for action-oriented lists
            complaints = complaints.filter(status__in=['pending', 'in_progress', 'urgent_review'])
        elif status_filter == 'resolved':
            complaints = complaints.filter(status='resolved')
        else:
            complaints = complaints.filter(status=status_filter)

    complaints = complaints.order_by('-created_at')

    return render(request, 'complaints/list.html', {
        'complaints': complaints,
        'current_filter': status_filter
    })


@login_required
def complaint_detail(request, complaint_id):
    """
    Detailed view for a single complaint.
    Now includes available field workers in the same ward with workload counts.
    """
    complaint = get_object_or_404(Complaint, id=complaint_id)
    
    # Simplified worker fetching as per request
    from accounts.models import User
    from django.db.models import Count, Q
    
    available_workers = User.objects.filter(role='field_worker').annotate(
        active_tasks=Count('assigned_tasks', filter=Q(assigned_tasks__status__in=['assigned', 'in_progress', 'urgent_review']))
    ).order_by('active_tasks')
    
    context = {
        'complaint': complaint,
        'available_workers': available_workers
    }
    return render(request, 'complaints/detail.html', context)


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
    return render(request, 'complaints/tactical_view.html', context)


@login_required
def complete_task(request, complaint_id):
    """
    POST-only view to handle task completion with proof.
    """
    complaint = get_object_or_404(Complaint, id=complaint_id)
    old_status = complaint.status
    
    if request.method == 'POST':
        form = TaskCompletionForm(request.POST, request.FILES)
        if form.is_valid():
            # Update complaint status
            complaint.status = 'resolved'
            complaint.resolution_image = form.cleaned_data['resolution_image']
            complaint.resolution_report = form.cleaned_data['resolution_report']
            complaint.save()

            # Create status history record
            ComplaintStatusHistory.objects.create(
                complaint=complaint,
                new_status='resolved',
                description=form.cleaned_data['resolution_report'],
                proof_image=form.cleaned_data['resolution_image'],
                actor=request.user
            )
            
            # Send real-time notification
            from notifications.utils import notify_complaint_status_change
            notify_complaint_status_change(complaint, old_status, 'resolved')
            
            messages.success(request, '✅ Task completed and marked as Resolved.')
            return redirect('complaint_detail', complaint_id=complaint.id)
        else:
            messages.error(request, 'Please provide both a description and proof photo.')
            
    return redirect('tactical_task_view', complaint_id=complaint.id)


@login_required
def submit_feedback(request, complaint_id):
    """
    Citizen submits rating and feedback for resolved complaint.
    """
    complaint = get_object_or_404(Complaint, id=complaint_id)

    # Security: only the owner can submit feedback
    if request.user != complaint.user:
        messages.error(request, 'You do not have permission to provide feedback for this complaint.')
        return redirect('dashboard')

    # Check if complaint is resolved
    if complaint.status != 'resolved':
        messages.error(request, 'Feedback can only be submitted for resolved complaints.')
        return redirect('complaint_detail', complaint_id=complaint.id)

    # Check if feedback already exists
    if hasattr(complaint, 'feedback'):
        messages.info(request, 'You have already submitted feedback for this complaint.')
        return redirect('complaint_detail', complaint_id=complaint.id)

    if request.method == 'POST':
        try:
            rating = int(request.POST.get('rating', 0))
            feedback_text = request.POST.get('feedback_text', '').strip()
            
            if not (1 <= rating <= 5):
                messages.error(request, 'Please provide a rating between 1 and 5 stars.')
                return redirect('feedback_form', complaint_id=complaint.id)
            
            if not feedback_text:
                messages.error(request, 'Please provide your feedback.')
                return redirect('feedback_form', complaint_id=complaint.id)
            
            # Create feedback
            ComplaintFeedback.objects.create(
                complaint=complaint,
                citizen=request.user,
                rating=rating,
                feedback_text=feedback_text
            )
            
            # Update complaint rating field
            complaint.citizen_rating = rating
            
            # Re-open if rating is poor (1-2 stars)
            if rating <= 2:
                complaint.status = 'pending'
                complaint.priority = 'high'
                complaint.save()
                messages.warning(
                    request, 
                    '⚠️ We are sorry you were unhappy with the resolution. '
                    'Your complaint has been re-opened with High Priority for review.'
                )
            else:
                complaint.save()
                messages.success(request, '✅ Thank you for your feedback! We appreciate your input.')
            
            return redirect('complaint_detail', complaint_id=complaint.id)
            
        except ValueError:
            messages.error(request, 'Invalid rating value.')
            return redirect('feedback_form', complaint_id=complaint.id)
    
    return render(request, 'complaints/feedback_form.html', {'complaint': complaint})


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
    Admin control to reassign a complaint to a field worker.
    Includes role guard and automatic status progression to 'in_progress'.
    """
    if not (request.user.role in ['panchayath_admin', 'ward_member'] or request.user.is_superuser):
         messages.error(request, 'Access denied. Administrative privileges required.')
         return redirect('dashboard')
         
    complaint = get_object_or_404(Complaint, id=complaint_id)
    old_status = complaint.status
    
    if request.method == 'POST':
        worker_id = request.POST.get('worker_id')
        try:
            from accounts.models import User
            worker = User.objects.get(id=worker_id)
            
            # ROLE GUARD: Only allow assignment to Field Workers
            if worker.role != 'field_worker':
                messages.error(request, f'Assignment failed: {worker.username} is not a verified field worker.')
                return redirect('complaint_detail', complaint_id=complaint.id)

            complaint.assigned_worker = worker
            complaint.status = 'in_progress'
            complaint.save()

            # Record in history
            from .models import ComplaintStatusHistory
            ComplaintStatusHistory.objects.create(
                complaint=complaint,
                new_status='in_progress',
                description=f"Task assigned to Authorized Worker: {worker.get_full_name() or worker.username}.",
                actor=request.user
            )
            
            # Send real-time notifications
            from notifications.utils import notify_complaint_status_change, notify_complaint_assigned
            notify_complaint_status_change(complaint, old_status, 'in_progress')
            notify_complaint_assigned(complaint)

            messages.success(request, f'Complaint #{complaint.id} successfully assigned to {worker.username}.')
        except User.DoesNotExist:
            messages.error(request, 'Selected worker does not exist.')
            
    return redirect('complaint_detail', complaint_id=complaint.id)


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


@login_required
def feedback_list(request):
    """
    Admin view: Display all complaint feedbacks with filtering options.
    """
    if not (request.user.role in ['panchayath_admin', 'ward_member'] or request.user.is_superuser):
        messages.error(request, 'Access denied. Administrative privileges required.')
        return redirect('dashboard')
    
    feedbacks = ComplaintFeedback.objects.select_related('complaint', 'citizen', 'complaint__ward').order_by('-created_at')
    
    # Filters
    rating_filter = request.GET.get('rating')
    ward_filter = request.GET.get('ward')
    
    if rating_filter:
        feedbacks = feedbacks.filter(rating=rating_filter)
    
    if ward_filter:
        feedbacks = feedbacks.filter(complaint__ward_id=ward_filter)
    
    # Stats
    from django.db.models import Avg, Count
    stats = ComplaintFeedback.objects.aggregate(
        avg_rating=Avg('rating'),
        total_feedbacks=Count('id'),
        poor_ratings=Count('id', filter=Q(rating__lte=2)),
        good_ratings=Count('id', filter=Q(rating__gte=4))
    )
    
    from accounts.models import Ward
    wards = Ward.objects.all().order_by('ward_number')
    
    context = {
        'feedbacks': feedbacks,
        'stats': stats,
        'wards': wards,
        'current_rating_filter': rating_filter,
        'current_ward_filter': ward_filter,
    }
    
    return render(request, 'complaints/feedback_list.html', context)
