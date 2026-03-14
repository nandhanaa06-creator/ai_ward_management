from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Ward, CitizenProfile

# 1. Form for Signup
class CitizenRegistrationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('phone_number', 'ward', 'address')

# 2. Form for Admin to add Wards
class WardForm(forms.ModelForm):
    class Meta:
        model = Ward
        fields = ['ward_number', 'ward_name', 'description']

# 3. Form for AI Scheme matching profile
class CitizenProfileForm(forms.ModelForm):
    class Meta:
        model = CitizenProfile
        fields = ['date_of_birth', 'gender', 'occupation', 'annual_income', 'aadhaar_number']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }