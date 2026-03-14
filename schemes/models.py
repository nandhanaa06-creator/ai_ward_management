from django.db import models


class Scheme(models.Model):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('A', 'All'),
    )

    name = models.CharField(max_length=200)
    description = models.TextField()
    benefits = models.TextField()

    # ── Eligibility Criteria ────────────────────────────────────────
    min_age = models.IntegerField(default=0)
    max_age = models.IntegerField(default=100)
    max_income = models.DecimalField(
        max_digits=10, decimal_places=2,
        help_text="Maximum annual income (₹) to qualify"
    )
    gender_target = models.CharField(
        max_length=1, choices=GENDER_CHOICES, default='A'
    )

    # Comma-separated list of occupations, or blank for "All"
    # e.g. "farmer,daily_wage_worker" — blank = open to everyone
    target_occupation = models.CharField(
        max_length=300, blank=True, default='',
        help_text="Comma-separated occupations, or leave blank for all"
    )

    # ── Meta ────────────────────────────────────────────────────────
    is_active = models.BooleanField(default=True)
    application_link = models.URLField(
        blank=True, default='',
        help_text="External portal URL for applications (optional)"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    # ------------------------------------------------------------------
    # Helper: parse target_occupation into a list of stripped lowercase strings
    # ------------------------------------------------------------------
    def get_occupation_targets(self):
        if not self.target_occupation.strip():
            return []  # empty → open to all
        return [o.strip().lower() for o in self.target_occupation.split(',') if o.strip()]