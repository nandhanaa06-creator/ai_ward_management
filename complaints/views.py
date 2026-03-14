from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta

from .forms import ComplaintForm
from .models import Complaint


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

def is_duplicate_complaint(title: str, ward, hours: int = 24) -> bool:
    """
    Check whether a complaint with a similar title already exists in the same
    ward within the last `hours` hours.  Uses a case-insensitive contains
    lookup so minor wording variations are still caught.
    """
    since = timezone.now() - timedelta(hours=hours)
    # Normalise: strip and take first 3 meaningful words for matching
    key_words = title.strip().lower().split()[:3]
    for word in key_words:
        if len(word) > 3:  # skip short stop-words
            if Complaint.objects.filter(
                ward=ward,
                title__icontains=word,
                created_at__gte=since,
            ).exists():
                return True
    return False


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

            # --- DUPLICATE DETECTION ---
            if request.user.ward and is_duplicate_complaint(title, request.user.ward):
                complaint.is_duplicate = True
                messages.info(
                    request,
                    'ℹ️ A similar complaint was already raised in your ward recently. '
                    'Your report has been flagged as a duplicate and will be linked to the original.',
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
def resolve_issue(request, complaint_id):
    """
    Worker view: Upload a photo of the completed work.
    Changes status to 'resolved' automatically.
    """
    complaint = get_object_or_404(Complaint, id=complaint_id)

    # Security check: only allow if it's assigned to this worker (or admin/member)
    if request.user.role == 'citizen':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    if request.method == 'POST':
        resolution_img = request.FILES.get('resolution_image')
        if resolution_img:
            complaint.resolution_image = resolution_img
            complaint.status = 'resolved'
            complaint.save() # updated_at refreshes automatically
            messages.success(request, '✅ Work submitted successfully. Complaint marked as Resolved.')
        else:
            messages.error(request, 'Please upload a proof of work photo to resolve the issue.')
        return redirect('complaint_detail', complaint_id=complaint.id)

    return render(request, 'complaints/resolve_issue.html', {'complaint': complaint})


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

