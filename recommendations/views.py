from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Count, Avg, Q
from django.utils import timezone
from recommendations.models import SchemeRecommendation
from recommendations.engine import SchemeRecommendationEngine
from schemes.models import Scheme

@login_required
def citizen_recommendations(request):
    """Citizen dashboard showing personalized scheme recommendations"""
    user = request.user
    
    # Generate recommendations if not exists
    if SchemeRecommendation.objects.filter(user=user).count() == 0:
        SchemeRecommendationEngine.generate_recommendations(user)
    
    # Get recommendations
    recommendations = SchemeRecommendation.objects.filter(user=user).select_related('scheme')
    
    # Stats
    total_recommendations = recommendations.count()
    high_match = recommendations.filter(match_score__gte=80).count()
    viewed_count = recommendations.filter(is_viewed=True).count()
    applied_count = recommendations.filter(is_applied=True).count()
    
    context = {
        'recommendations': recommendations,
        'total_recommendations': total_recommendations,
        'high_match': high_match,
        'viewed_count': viewed_count,
        'applied_count': applied_count,
    }
    return render(request, 'recommendations/citizen_dashboard.html', context)

@login_required
def refresh_recommendations(request):
    """Force refresh recommendations for current user"""
    if request.method == 'POST':
        count = SchemeRecommendationEngine.generate_recommendations(request.user, force_refresh=True)
        return JsonResponse({'success': True, 'count': count})
    return JsonResponse({'success': False})

@login_required
def mark_recommendation_viewed(request, rec_id):
    """Mark recommendation as viewed"""
    if request.method == 'POST':
        success = SchemeRecommendationEngine.mark_viewed(rec_id)
        return JsonResponse({'success': success})
    return JsonResponse({'success': False})

@login_required
def mark_recommendation_applied(request, rec_id):
    """Mark recommendation as applied"""
    if request.method == 'POST':
        success = SchemeRecommendationEngine.mark_applied(rec_id)
        return JsonResponse({'success': success})
    return JsonResponse({'success': False})

@login_required
def admin_recommendation_analytics(request):
    """Admin dashboard for scheme recommendation analytics"""
    if not request.user.is_staff:
        return redirect('admin_dashboard')
    
    # Overall stats
    total_recommendations = SchemeRecommendation.objects.count()
    total_users_with_recs = SchemeRecommendation.objects.values('user').distinct().count()
    avg_match_score = SchemeRecommendation.objects.aggregate(Avg('match_score'))['match_score__avg'] or 0
    
    viewed_rate = 0
    applied_rate = 0
    if total_recommendations > 0:
        viewed_count = SchemeRecommendation.objects.filter(is_viewed=True).count()
        applied_count = SchemeRecommendation.objects.filter(is_applied=True).count()
        viewed_rate = (viewed_count / total_recommendations) * 100
        applied_rate = (applied_count / total_recommendations) * 100
    
    # Top schemes by recommendations
    top_schemes = SchemeRecommendation.objects.values('scheme__name').annotate(
        rec_count=Count('id'),
        avg_score=Avg('match_score'),
        applied=Count('id', filter=Q(is_applied=True))
    ).order_by('-rec_count')[:10]
    
    # Recent recommendations
    recent_recs = SchemeRecommendation.objects.select_related('user', 'scheme').order_by('-created_at')[:20]
    
    context = {
        'total_recommendations': total_recommendations,
        'total_users_with_recs': total_users_with_recs,
        'avg_match_score': round(avg_match_score, 1),
        'viewed_rate': round(viewed_rate, 1),
        'applied_rate': round(applied_rate, 1),
        'top_schemes': top_schemes,
        'recent_recs': recent_recs,
    }
    return render(request, 'recommendations/admin_analytics.html', context)

# API endpoints for charts
@login_required
def recommendation_score_distribution(request):
    """API: Distribution of match scores"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    ranges = [
        ('50-60%', 50, 60),
        ('60-70%', 60, 70),
        ('70-80%', 70, 80),
        ('80-90%', 80, 90),
        ('90-100%', 90, 100),
    ]
    
    data = []
    for label, min_score, max_score in ranges:
        count = SchemeRecommendation.objects.filter(
            match_score__gte=min_score,
            match_score__lt=max_score if max_score < 100 else 101
        ).count()
        data.append({'label': label, 'count': count})
    
    return JsonResponse({'data': data})

@login_required
def recommendation_conversion_funnel(request):
    """API: Conversion funnel data"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    total = SchemeRecommendation.objects.count()
    viewed = SchemeRecommendation.objects.filter(is_viewed=True).count()
    applied = SchemeRecommendation.objects.filter(is_applied=True).count()
    
    data = [
        {'stage': 'Recommended', 'count': total},
        {'stage': 'Viewed', 'count': viewed},
        {'stage': 'Applied', 'count': applied},
    ]
    
    return JsonResponse({'data': data})
