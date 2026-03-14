from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from decimal import Decimal
from datetime import date

from .models import Scheme
from accounts.models import CitizenProfile


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


# ── Views ───────────────────────────────────────────────────────────────────

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