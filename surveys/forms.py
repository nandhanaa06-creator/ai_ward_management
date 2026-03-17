from django import forms
from .models import Survey, SurveyField, Submission, SubmissionFile

class SurveyForm(forms.ModelForm):
    """
    Form to create/edit the survey metadata.
    """
    class Meta:
        model = Survey
        fields = ['title', 'description', 'expiry_date', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Ration Card Verification 2024'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Briefly explain the purpose of this data collection...'}),
            'expiry_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class SurveyFieldForm(forms.ModelForm):
    """
    Form for individual field configuration.
    """
    class Meta:
        model = SurveyField
        fields = ['label', 'field_type', 'required', 'options', 'order']
        widgets = {
            'label': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Field label (e.g. Full Name)'}),
            'field_type': forms.Select(attrs={'class': 'form-select'}),
            'required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'options': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Comma-separated (for dropdowns)'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }

# Inline formset for managing dynamic fields
SurveyFieldFormSet = forms.inlineformset_factory(
    Survey, SurveyField, form=SurveyFieldForm,
    extra=1, can_delete=True
)

class DynamicSubmissionForm(forms.Form):
    """
    Form that dynamically generates its fields based on the Survey definition.
    """
    def __init__(self, survey, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.survey = survey
        for field in survey.fields.all():
            form_field = None
            attrs = {'class': 'form-control'}
            
            if field.field_type == 'text':
                form_field = forms.CharField(label=field.label, required=field.required, widget=forms.TextInput(attrs=attrs))
            elif field.field_type == 'textarea':
                form_field = forms.CharField(label=field.label, required=field.required, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))
            elif field.field_type == 'select':
                choices = [(opt.strip(), opt.strip()) for opt in field.options.split(',') if opt.strip()]
                form_field = forms.ChoiceField(label=field.label, required=field.required, choices=choices, widget=forms.Select(attrs={'class': 'form-select'}))
            elif field.field_type == 'checkbox':
                form_field = forms.BooleanField(label=field.label, required=field.required, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
            elif field.field_type == 'file':
                form_field = forms.FileField(label=field.label, required=field.required, widget=forms.ClearableFileInput(attrs={'class': 'form-control'}))
            
            if form_field:
                self.fields[f'field_{field.id}'] = form_field

    def clean(self):
        cleaned_data = super().clean()
        
        # ── Cross-Field Validation Logic ──
        # We look for fields that might represent Age and Date of Birth
        age_val = None
        dob_val = None
        
        for field in self.survey.fields.all():
            field_key = f'field_{field.id}'
            label_lower = field.label.lower()
            
            if 'age' in label_lower:
                try:
                    age_val = int(cleaned_data.get(field_key))
                except (ValueError, TypeError):
                    pass
            
            if 'birth' in label_lower or 'dob' in label_lower:
                val = cleaned_data.get(field_key)
                if val:
                    from datetime import datetime, date
                    if isinstance(val, (date, datetime)):
                        dob_val = val
                    else:
                        # Try standard formats
                        for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y'):
                            try:
                                dob_val = datetime.strptime(str(val), fmt).date()
                                break
                            except (ValueError, TypeError):
                                pass

        # Perform the consistency check
        if age_val is not None and dob_val is not None:
            from datetime import date
            today = date.today()
            if isinstance(dob_val, datetime):
                dob_val = dob_val.date()
            calculated_age = today.year - dob_val.year - ((today.month, today.day) < (dob_val.month, dob_val.day))
            
            # Allow for a small margin of error (e.g. 1 year) due to calculation timing
            if abs(calculated_age - age_val) > 1:
                raise forms.ValidationError(
                    f"Data Inconsistency Detected: The provided Age ({age_val}) does not match "
                    f"the calculated age from Date of Birth ({calculated_age}). Please verify."
                )

        return cleaned_data
