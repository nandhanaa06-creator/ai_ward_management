from django.db import models
from django.conf import settings
from accounts.models import Ward

class Complaint(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('rejected', 'Rejected'),
    )

    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    )

    # Basic Info
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='complaints')
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='complaints/', null=True, blank=True)
    
    # Location Info
    ward = models.ForeignKey(Ward, on_delete=models.CASCADE, related_name='complaints')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    address_extra = models.CharField(max_length=255, help_text="Landmarks or specific spot", blank=True)

    # AI & Management Fields
    category = models.CharField(max_length=100, blank=True, null=True) 
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    is_duplicate = models.BooleanField(default=False)

    # NEW: Workflow Tracking & Proof
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    assigned_worker = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        related_name='assigned_tasks'
    )
    # Allows workers to upload a "fixed" photo
    resolution_image = models.ImageField(upload_to='resolutions/', null=True, blank=True)
    # Allows the user to rate the resolution
    citizen_rating = models.PositiveSmallIntegerField(null=True, blank=True, help_text="1-5 stars")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"


# Admin-to-Citizen Communication
class ComplaintMessage(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message by {self.sender.username} on {self.complaint.id}"