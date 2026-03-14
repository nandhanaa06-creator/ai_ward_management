from django.db import models
from accounts.models import Ward

class Meeting(models.Model):
    ward = models.ForeignKey(Ward, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    meeting_date = models.DateTimeField()
    location = models.CharField(max_length=255)
    agenda_pdf = models.FileField(upload_to='agendas/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.ward.ward_name}"