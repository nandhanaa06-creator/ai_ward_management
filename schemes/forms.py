from django import forms
from accounts.models import CitizenProfile
from .models import Scheme


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

class SchemeForm(forms.ModelForm):
    """
    Form for Ward Members to create/update Government Schemes.
    Includes all fields for eligibility criteria and visual styling.
    """
    class Meta:
        model = Scheme
        fields = [
            'name', 'description', 'benefits', 'min_age', 'max_age',
            'max_income', 'gender_target', 'target_occupation', 
            'is_active', 'application_link'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Scheme Name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Detailed description of the scheme'}),
            'benefits': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'List of benefits provided'}),
            'min_age': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'max_age': forms.NumberInput(attrs={'class': 'form-control', 'max': 120}),
            'max_income': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Maximum Annual Income (₹)'}),
            'gender_target': forms.Select(attrs={'class': 'form-select'}),
            'target_occupation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. farmer, student (comma separated)'}),
            'application_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'min_age': 'Minimum Age',
            'max_age': 'Maximum Age',
            'max_income': 'Income Ceiling (₹)',
            'gender_target': 'Target Gender',
            'target_occupation': 'Specific Occupations',
        }