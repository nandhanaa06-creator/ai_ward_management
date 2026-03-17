from django.db import models
from accounts.models import Ward, User

class Meeting(models.Model):
    ward = models.ForeignKey(Ward, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    meeting_date = models.DateTimeField()
    location = models.CharField(max_length=255)
    agenda_pdf = models.FileField(upload_to='agendas/', null=True, blank=True)
    
    # Minutes fields
    minutes_summary = models.TextField(null=True, blank=True)
    minutes_pdf = models.FileField(upload_to='minutes/', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.ward.ward_name}"

class MeetingRSVP(models.Model):
    RSVP_CHOICES = (
        ('attending', 'Attending'),
        ('not_attending', 'Not Attending'),
        ('tentative', 'Tentative'),
    )
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='rsvps')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meeting_rsvps')
    status = models.CharField(max_length=20, choices=RSVP_CHOICES, default='attending')
    submitted_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('meeting', 'user')

    def __str__(self):
        return f"{self.user.username} - {self.meeting.title} ({self.status})"

class MeetingFeedback(models.Model):
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='feedbacks')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    is_question = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Feedback by {self.user.username} on {self.meeting.title}"