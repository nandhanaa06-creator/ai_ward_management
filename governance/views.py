from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Meeting
from .forms import MeetingForm

@login_required
def schedule_meeting(request):
    if request.user.role != 'ward_member':
        return redirect('dashboard') # Only ward members can schedule
        
    if request.method == 'POST':
        form = MeetingForm(request.POST, request.FILES)
        if form.is_valid():
            meeting = form.save(commit=False)
            meeting.ward = request.user.ward # Auto-assign to the member's ward
            meeting.save()
            return redirect('meeting_list')
    else:
        form = MeetingForm()
    return render(request, 'governance/schedule.html', {'form': form})

@login_required
def meeting_list(request):
    # Show meetings only for the user's ward
    meetings = Meeting.objects.filter(ward=request.user.ward).order_by('-meeting_date')
    return render(request, 'governance/list.html', {'meetings': meetings})