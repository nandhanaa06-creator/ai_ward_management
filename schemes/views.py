from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q
from decimal import Decimal
from datetime import date, timedelta

from .models import Scheme
from accounts.models import CitizenProfile, User
from .forms import SchemeForm


# ── Constants ───────────────────────────────────────────────────────────────
# Percentage margin used to identify "near-miss" schemes.
# A user whose income is within NEAR_MATCH_MARGIN above the limit is still
# shown the scheme as "Recommended with Review".
NEAR_MATCH_MARGIN = Decimal('0.05')   # 5 % over the income cap


# ── Helpers ─────────────────────────────────────────────────────────────────

def _calculate_age(date_of_birth):
    """Return the integer age today for a given date_of_birth."""
    today = date.today()
    return (
        today.year - date_of_birth.year
        - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
    )


def _occupation_matches(scheme, user_occupation):
    """
    Return True if the scheme is open to the user's occupation.
    An empty target_occupation means "open to all".
    """
    targets = scheme.get_occupation_targets()
    if not targets:
        return True   # open to all occupations
    user_occ = (user_occupation or '').strip().lower()
    return user_occ in targets


def _build_base_queryset(user_age, user_gender):
    """
    Use Q objects to get all active schemes whose age AND gender criteria
    *could* match this user (income / occupation checked in Python for
    near-match granularity).
    """
    return Scheme.objects.filter(
        is_active=True,
        min_age__lte=user_age,
        max_age__gte=user_age,
    ).filter(
        Q(gender_target='A') | Q(gender_target=user_gender)
    )


# ── Main Matching Engine ────────────────────────────────────────────────────

def run_matching_engine(profile, user_age):
    """
    Multi-criteria matching engine.

    Returns a tuple of three lists:
      eligible       — user fully meets all criteria
      near_match     — user is ineligible by ≤ NEAR_MATCH_MARGIN on income only
      ineligible     — all remaining active schemes (for optional display)

    Each item in the lists is a dict carrying the scheme plus match metadata.
    """
    eligible    = []
    near_match  = []

    user_income     = profile.annual_income or Decimal('0')
    user_gender     = profile.gender or 'A'
    user_occupation = profile.occupation or ''

    candidate_schemes = _build_base_queryset(user_age, user_gender)

    for scheme in candidate_schemes:
        income_ok       = user_income <= scheme.max_income
        # Near-match: income is within 5 % above the limit
        income_near     = (
            not income_ok and
            scheme.max_income > 0 and
            user_income <= scheme.max_income * (1 + NEAR_MATCH_MARGIN)
        )
        occupation_ok   = _occupation_matches(scheme, user_occupation)

        if income_ok and occupation_ok:
            eligible.append({
                'scheme': scheme,
                'match_type': 'eligible',
                'income_gap': None,
                'income_pct': None,
            })
        elif income_near and occupation_ok:
            # How far over the limit, as a percentage?
            overage_pct = int(
                ((user_income - scheme.max_income) / scheme.max_income) * 100
            )
            near_match.append({
                'scheme': scheme,
                'match_type': 'near_match',
                'income_gap': user_income - scheme.max_income,
                'income_pct': overage_pct,
            })

    return eligible, near_match


def get_eligible_beneficiaries(scheme):
    """
    Reverse matching engine: finds all citizens eligible for a specific scheme.
    Returns a QuerySet of User objects (citizens).
    """
    today = date.today()
    birth_year_min = today.year - scheme.max_age
    birth_year_max = today.year - scheme.min_age
    
    # 1. Base QuerySet: Active Citizen Profiles
    queryset = CitizenProfile.objects.filter(user__role='citizen')
    
    # 2. Age Filter (approximate by year for QuerySet performance)
    queryset = queryset.filter(
        date_of_birth__year__gte=birth_year_min,
        date_of_birth__year__lte=birth_year_max
    )
    
    # 3. Gender Filter
    if scheme.gender_target != 'A':
        queryset = queryset.filter(gender=scheme.gender_target)
        
    # 4. Income Filter
    queryset = queryset.filter(annual_income__lte=scheme.max_income)
    
    # 5. Occupation Filter (Python side for complex comma-separated logic)
    target_occupations = scheme.get_occupation_targets()
    if target_occupations:
        all_profiles = list(queryset)
        eligible_profiles = [
            p for p in all_profiles 
            if (p.occupation or '').strip().lower() in target_occupations
        ]
        return [p.user for p in eligible_profiles]
        
    return [p.user for p in queryset]


# ── Views ───────────────────────────────────────────────────────────────────

def is_ward_member(user):
    return user.is_authenticated and (user.role == 'ward_member' or user.role == 'panchayath_admin')

@user_passes_test(is_ward_member, login_url='/accounts/login/')
def create_scheme(request):
    """
    Ward Member view to create a new Government Scheme.
    Includes AI-assisted beneficiary matching preview.
    """
    if request.method == 'POST':
        form = SchemeForm(request.POST)
        if form.is_valid():
            scheme = form.save(commit=False)
            scheme.created_by = request.user
            scheme.save()
            
            # Send real-time notifications to all citizens
            try:
                from notifications.utils import notify_new_scheme
                notify_new_scheme(scheme)
            except Exception as e:
                print(f"Real-time notification failed: {e}")
            
            messages.success(request, f'Scheme "{scheme.name}" has been created successfully.')
            return redirect('create_scheme')
    else:
        form = SchemeForm()
        
    # AI Matching Preview: If there's enough data in the form (mocked for now or based on defaults)
    # For a new form, we can show matches for the default values or a specific selection
    preview_scheme = Scheme(
        min_age=18, max_age=60, max_income=Decimal('50000'), gender_target='A'
    )
    eligible_users = get_eligible_beneficiaries(preview_scheme)
    
    # List of schemes created by this user
    schemes = Scheme.objects.filter(created_by=request.user).order_by('-created_at')
    
    context = {
        'form': form,
        'eligible_users': eligible_users,
        'eligible_count': len(eligible_users),
        'schemes': schemes,
    }
    return render(request, 'schemes/create_scheme.html', context)

@user_passes_test(is_ward_member, login_url='/accounts/login/')
def notify_citizens(request, scheme_id):
    """
    Sends alerts to all citizens eligible for the specified scheme.
    """
    try:
        scheme = Scheme.objects.get(id=scheme_id)
        eligible_users = get_eligible_beneficiaries(scheme)
        
        # Mock Notification Logic
        for user in eligible_users:
            # print(f"NOTIFY: Sent alert to {user.username} for scheme {scheme.name}")
            pass
            
        messages.success(request, f'Notifications sent to {len(eligible_users)} eligible citizens.')
    except Scheme.DoesNotExist:
        messages.error(request, 'Scheme not found.')
        
    return redirect('create_scheme')

@login_required
def match_schemes(request):
    """
    Intelligent scheme recommendation view.

    Retrieves the logged-in citizen's profile, runs the multi-criteria
    matching engine, and renders a card-deck results page with three
    tiers: Eligible, Near-Match, and a prompt to complete the profile
    if data is missing.
    """
    user = request.user

    # ── Guard: profile must exist ────────────────────────────────────
    try:
        profile = CitizenProfile.objects.get(user=user)
    except CitizenProfile.DoesNotExist:
        messages.warning(
            request,
            'Please complete your citizen profile before viewing scheme recommendations.'
        )
        return render(request, 'schemes/no_profile.html')

    # ── Guard: date_of_birth required for age calculation ────────────
    if not profile.date_of_birth:
        messages.info(
            request,
            'Your date of birth is missing from your profile. '
            'Please update it to see personalised recommendations.'
        )
        return render(request, 'schemes/no_profile.html')

    # ── Guard: income required for income filtering ───────────────────
    if profile.annual_income is None:
        messages.info(
            request,
            'Your annual income is missing from your profile. '
            'Please update it to see personalised scheme recommendations.'
        )
        return render(request, 'schemes/no_profile.html')

    user_age = _calculate_age(profile.date_of_birth)

    eligible, near_match = run_matching_engine(profile, user_age)

    context = {
        'profile':          profile,
        'user_age':         user_age,
        'eligible':         eligible,
        'near_match':       near_match,
        'eligible_count':   len(eligible),
        'near_match_count': len(near_match),
        'total_count':      len(eligible) + len(near_match),
        'near_match_pct':   int(NEAR_MATCH_MARGIN * 100),
    }
    return render(request, 'schemes/eligible_schemes.html', context)


@login_required
def eligible_schemes(request):
    """Backwards-compatible alias → redirects to match_schemes."""
    return redirect('match_schemes')