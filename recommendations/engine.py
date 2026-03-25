from schemes.models import Scheme
from recommendations.models import SchemeRecommendation
from datetime import datetime

class SchemeRecommendationEngine:
    """AI-powered scheme recommendation engine"""
    
    @staticmethod
    def calculate_eligibility(user, scheme):
        """Calculate eligibility score (0-100) and reasons"""
        score = 0
        reasons = []
        max_score = 100
        
        # Age eligibility (30 points)
        if user.age:
            if scheme.min_age <= user.age <= scheme.max_age:
                score += 30
                reasons.append(f"✓ Age {user.age} matches requirement ({scheme.min_age}-{scheme.max_age} years)")
            else:
                reasons.append(f"✗ Age {user.age} outside range ({scheme.min_age}-{scheme.max_age} years)")
        
        # Income eligibility (30 points)
        if user.annual_income:
            if user.annual_income <= scheme.max_income:
                score += 30
                income_gap = scheme.max_income - user.annual_income
                reasons.append(f"✓ Income ₹{user.annual_income:,.0f} qualifies (limit: ₹{scheme.max_income:,.0f})")
            else:
                reasons.append(f"✗ Income ₹{user.annual_income:,.0f} exceeds limit (₹{scheme.max_income:,.0f})")
        
        # Gender eligibility (20 points)
        if scheme.gender_target == 'A' or scheme.gender_target == user.gender:
            score += 20
            if scheme.gender_target == 'A':
                reasons.append("✓ Open to all genders")
            else:
                reasons.append(f"✓ Gender matches ({user.get_gender_display()})")
        else:
            reasons.append(f"✗ Gender mismatch (scheme for {scheme.get_gender_target_display()})")
        
        # Occupation eligibility (20 points)
        occupation_targets = scheme.get_occupation_targets()
        if not occupation_targets:  # Open to all
            score += 20
            reasons.append("✓ Open to all occupations")
        elif user.occupation and user.occupation.lower() in occupation_targets:
            score += 20
            reasons.append(f"✓ Occupation '{user.occupation}' matches")
        else:
            if user.occupation:
                reasons.append(f"✗ Occupation '{user.occupation}' not targeted")
            else:
                reasons.append("✗ No occupation specified in profile")
        
        return score, "\n".join(reasons)
    
    @staticmethod
    def generate_recommendations(user, force_refresh=False):
        """Generate scheme recommendations for a user"""
        if not force_refresh:
            # Check if recommendations already exist
            existing = SchemeRecommendation.objects.filter(user=user).count()
            if existing > 0:
                return existing
        
        # Clear old recommendations if force refresh
        if force_refresh:
            SchemeRecommendation.objects.filter(user=user).delete()
        
        active_schemes = Scheme.objects.filter(is_active=True)
        recommendations_created = 0
        
        for scheme in active_schemes:
            score, reasons = SchemeRecommendationEngine.calculate_eligibility(user, scheme)
            
            # Only recommend if score >= 50% (at least partially eligible)
            if score >= 50:
                SchemeRecommendation.objects.create(
                    user=user,
                    scheme=scheme,
                    match_score=score,
                    match_reasons=reasons
                )
                recommendations_created += 1
        
        return recommendations_created
    
    @staticmethod
    def get_top_recommendations(user, limit=5):
        """Get top N recommendations for a user"""
        # Generate if not exists
        if SchemeRecommendation.objects.filter(user=user).count() == 0:
            SchemeRecommendationEngine.generate_recommendations(user)
        
        return SchemeRecommendation.objects.filter(user=user)[:limit]
    
    @staticmethod
    def mark_viewed(recommendation_id):
        """Mark recommendation as viewed"""
        try:
            rec = SchemeRecommendation.objects.get(id=recommendation_id)
            if not rec.is_viewed:
                rec.is_viewed = True
                rec.viewed_at = datetime.now()
                rec.save()
            return True
        except SchemeRecommendation.DoesNotExist:
            return False
    
    @staticmethod
    def mark_applied(recommendation_id):
        """Mark recommendation as applied"""
        try:
            rec = SchemeRecommendation.objects.get(id=recommendation_id)
            if not rec.is_applied:
                rec.is_applied = True
                rec.applied_at = datetime.now()
                rec.save()
            return True
        except SchemeRecommendation.DoesNotExist:
            return False
