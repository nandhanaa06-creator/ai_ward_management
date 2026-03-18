from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from .models import Meeting, MeetingRSVP, MeetingFeedback, Notification, MeetingSummary
from .forms import MeetingForm, MeetingMinutesForm, MeetingFeedbackForm, MeetingSummaryForm

def is_ward_member(user):
    return user.is_authenticated and (user.role == 'ward_member' or user.role == 'panchayath_admin')

@login_required
@user_passes_test(is_ward_member, login_url='/accounts/login/')
def schedule_meeting(request):
    """
    Ward Member view to schedule a new meeting.
    """
    if request.method == 'POST':
        form = MeetingForm(request.POST, request.FILES)
        if form.is_valid():
            meeting = form.save(commit=False)
            meeting.ward = request.user.ward
            meeting.save()
            
            # --- Trigger Notifications for all citizens in the ward ---
            from accounts.models import User
            citizens = User.objects.filter(ward=meeting.ward, role='citizen')
            for citizen in citizens:
                Notification.objects.create(
                    user=citizen,
                    title="New Grama Sabha Scheduled",
                    message=f"A new meeting '{meeting.title}' has been scheduled for {meeting.meeting_date.strftime('%d %b %Y at %H:%M')}. Venue: {meeting.location}."
                )
            
            messages.success(request, f'Meeting "{meeting.title}" scheduled successfully. Notifications sent to ward citizens.')
            return redirect('meeting_list')
    else:
        form = MeetingForm()
    return render(request, 'governance/schedule.html', {'form': form})

@login_required
def meeting_list(request):
    """
    List view for all meetings in the user's ward.
    """
    # Citizens see all meetings in their ward. Admins/Ward Members see meetings they manage.
    if not request.user.ward:
        return render(request, 'governance/list.html', {'meetings': [], 'no_ward': True})
    
    all_meetings = Meeting.objects.filter(ward=request.user.ward).order_by('-meeting_date')
    
    upcoming_meetings = all_meetings.filter(meeting_date__gte=timezone.now()).order_by('meeting_date')
    past_meetings = all_meetings.filter(meeting_date__lt=timezone.now())

    # For citizens, we want to know their RSVP status for upcoming ones
    if request.user.role == 'citizen':
        for m in upcoming_meetings:
            rsvp = MeetingRSVP.objects.filter(meeting=m, user=request.user).first()
            m.user_rsvp = rsvp.status if rsvp else None
            
    return render(request, 'governance/list.html', {
        'upcoming_meetings': upcoming_meetings,
        'past_meetings': past_meetings
    })

@login_required
def meeting_detail(request, pk):
    """
    Detailed view of a meeting showing agenda, location, and minutes (if published).
    """
    meeting = get_object_or_404(Meeting, pk=pk, ward=request.user.ward)
    user_rsvp = MeetingRSVP.objects.filter(meeting=meeting, user=request.user).first()
    
    # Handle Feedback submission
    if request.method == 'POST' and 'submit_feedback' in request.POST:
        form = MeetingFeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.meeting = meeting
            feedback.user = request.user
            feedback.save()
            messages.success(request, 'Thank you for your feedback! It has been posted publicly.')
            return redirect('meeting_detail', pk=pk)
    else:
        form = MeetingFeedbackForm()

    # Calculate RSVP stats
    attending_count = meeting.rsvps.filter(status='attending').count()
    feedbacks = meeting.feedbacks.all().select_related('user')
    
    context = {
        'meeting': meeting,
        'user_rsvp': user_rsvp.status if user_rsvp else None,
        'attending_count': attending_count,
        'is_past': meeting.meeting_date < timezone.now(),
        'feedback_form': form,
        'feedbacks': feedbacks,
    }
    return render(request, 'governance/meeting_detail.html', context)

@login_required
@user_passes_test(is_ward_member, login_url='/accounts/login/')
def publish_minutes(request, pk):
    """
    Ward Member view to upload minutes and summaries.
    """
    meeting = get_object_or_404(Meeting, pk=pk, ward=request.user.ward)
    
    summary, _ = MeetingSummary.objects.get_or_create(meeting=meeting)
    
    if request.method == 'POST':
        form = MeetingSummaryForm(request.POST, instance=summary)
        if form.is_valid():
            form.save()
            messages.success(request, f'Minutes and decisions for "{meeting.title}" have been published.')
            return redirect('meeting_detail', pk=meeting.id)
    else:
        form = MeetingSummaryForm(instance=summary)
        
    return render(request, 'governance/publish_minutes.html', {
        'form': form,
        'meeting': meeting
    })

@login_required
def rsvp_meeting(request, pk):
    """
    Citizen RSVP endpoint. toggles between attending/not attending.
    """
    meeting = get_object_or_404(Meeting, pk=pk, ward=request.user.ward)
    
    if request.method == 'POST':
        status = request.POST.get('status', 'attending')
        if status not in ['attending', 'not_attending', 'tentative']:
            status = 'attending'
            
        rsvp, created = MeetingRSVP.objects.get_or_create(
            meeting=meeting, 
            user=request.user,
            defaults={'status': status}
        )
        if not created:
            rsvp.status = status
            rsvp.save()
            
        messages.success(request, f'Your RSVP for "{meeting.title}" has been updated to {status.replace("_", " ").title()}.')
        
    return redirect(request.META.get('HTTP_REFERER', 'meeting_list'))