from django import forms
from accounts.models import CitizenProfile


class CitizenProfileForm(forms.ModelForm):
    """
    Form for citizens to update their profile.
    All fields used by the scheme matching engine are included and
    given Bootstrap-ready widgets with helpful placeholders.
    """

    class Meta:
        model = CitizenProfile
        fields = [
            'date_of_birth',
            'gender',
            'occupation',
            'annual_income',
            'aadhaar_number',
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
            }),
            'gender': forms.Select(attrs={
                'class': 'form-select',
            }),
            'occupation': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. farmer, daily_wage_worker, student',
            }),
            'annual_income': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Annual income in ₹',
                'min': '0',
                'step': '1000',
            }),
            'aadhaar_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '12-digit Aadhaar number',
                'maxlength': '12',
            }),
        }
        labels = {
            'date_of_birth': 'Date of Birth',
            'gender': 'Gender',
            'occupation': 'Occupation / Profession',
            'annual_income': 'Annual Income (₹)',
            'aadhaar_number': 'Aadhaar Number',
        }
        help_texts = {
            'occupation': (
                'Enter your occupation exactly as listed in scheme criteria '
                '(e.g. farmer, student, daily_wage_worker).'
            ),
            'annual_income': 'Used to determine income-based eligibility for welfare schemes.',
        }