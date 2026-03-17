from django.db import models
from django.utils.text import slugify
from accounts.models import User
import uuid

class Survey(models.Model):
    """
    Main model for a data collection form.
    Stores metadata and access control (expiry, status).
    """
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True, max_length=100)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_surveys')
    created_at = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            # Generate a secure unique slug
            self.slug = slugify(self.title)[:40] + "-" + str(uuid.uuid4())[:8]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class SurveyField(models.Model):
    """
    Individual field definitions for a dynamic survey.
    """
    FIELD_TYPES = (
        ('text', 'Short Text'),
        ('textarea', 'Long Text'),
        ('select', 'Dropdown'),
        ('checkbox', 'Checkbox'),
        ('file', 'File Upload'),
    )
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='fields')
    label = models.CharField(max_length=200)
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES)
    required = models.BooleanField(default=True)
    options = models.TextField(blank=True, help_text="Comma-separated options for dropdowns (e.g. Red, Blue, Green)")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.label} ({self.field_type})"

class Submission(models.Model):
    """
    A single response entry for a survey.
    Stores non-file data in a JSONField for scalability.
    """
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='submissions')
    data = models.JSONField(default=dict)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Submission for {self.survey.title} at {self.submitted_at}"

class SubmissionFile(models.Model):
    """
    Tracks files uploaded as part of a dynamic form submission.
    """
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='files')
    field_label = models.CharField(max_length=200)
    file = models.FileField(upload_to='survey_uploads/%Y/%m/%d/')

    def __str__(self):
        return f"File for {self.field_label} in {self.submission}"
