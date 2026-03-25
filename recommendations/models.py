from django.db import models
from django.conf import settings
from schemes.models import Scheme

class SchemeRecommendation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='scheme_recommendations')
    scheme = models.ForeignKey(Scheme, on_delete=models.CASCADE, related_name='recommendations')
    match_score = models.FloatField(help_text="Eligibility match percentage (0-100)")
    match_reasons = models.TextField(help_text="Why this scheme matches the user")
    is_viewed = models.BooleanField(default=False)
    is_applied = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    viewed_at = models.DateTimeField(null=True, blank=True)
    applied_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-match_score', '-created_at']
        unique_together = ('user', 'scheme')

    def __str__(self):
        return f"{self.user.username} - {self.scheme.name} ({self.match_score}%)"
