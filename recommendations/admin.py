from django.contrib import admin
from .models import SchemeRecommendation

@admin.register(SchemeRecommendation)
class SchemeRecommendationAdmin(admin.ModelAdmin):
    list_display = ('user', 'scheme', 'match_score', 'is_viewed', 'is_applied', 'created_at')
    list_filter = ('is_viewed', 'is_applied', 'created_at')
    search_fields = ('user__username', 'scheme__name')
    readonly_fields = ('created_at', 'viewed_at', 'applied_at')
    ordering = ('-match_score', '-created_at')
