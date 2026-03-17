from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Ward, CitizenProfile

# 1. FIXES THE EMPTY WARD DROPDOWN
class CitizenRegistrationForm(UserCreationForm):
    ward = forms.ModelChoiceField(
        queryset=Ward.objects.all(), 
        empty_label="Select your Ward",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('phone_number', 'ward', 'address')

# 2. UPDATES CITIZEN SCHEME PROFILE
class CitizenProfileForm(forms.ModelForm):
    class Meta:
        model = CitizenProfile
        fields = ['date_of_birth', 'gender', 'occupation', 'annual_income', 'aadhaar_number']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'occupation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. farmer'}),
            'annual_income': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Annual income in ₹'}),
            'aadhaar_number': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '12'}),
        }

# 3. WARD MANAGEMENT FORM
class WardForm(forms.ModelForm):
    class Meta:
        model = Ward
        fields = ['ward_number', 'ward_name', 'description']