from django import forms
from .models import Complaint


class ComplaintForm(forms.ModelForm):
    """
    ModelForm for submitting a new complaint.
    Ward is intentionally excluded from the form fields — it is auto-assigned
    in the view from the logged-in user's profile (request.user.ward).
    Latitude/longitude are hidden fields meant to be populated by browser
    Geolocation API via JavaScript.
    """

    latitude = forms.DecimalField(
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'id_latitude'}),
    )
    longitude = forms.DecimalField(
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'id_longitude'}),
    )

    class Meta:
        model = Complaint
        fields = [
            'title',
            'description',
            'image',
            'address_extra',
            'latitude',
            'longitude',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Broken streetlight near market',
                'id': 'id_title',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': (
                    'Describe the issue in detail. Mention if it is an '
                    'emergency or danger so it can be escalated quickly.'
                ),
                'id': 'id_description',
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'id': 'id_image',
            }),
            'address_extra': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Near Gandhi Statue / 4th Cross / Opp. School',
                'id': 'id_address_extra',
            }),
        }
        labels = {
            'title': 'Issue Title',
            'description': 'Detailed Description',
            'image': 'Upload Photo (optional)',
            'address_extra': 'Landmark / Specific Location',
        }
        help_texts = {
            'description': (
                'Tip: Keywords like "pipe", "leak", "wire", "pothole", '
                '"garbage" help our AI categorize your complaint automatically.'
            ),
        }

class TaskCompletionForm(forms.ModelForm):
    """
    Form for field workers to mark a task as resolved.
    Requires proof image and completion report.
    """
    class Meta:
        model = Complaint
        fields = ['resolution_image', 'resolution_report']
        widgets = {
            'resolution_image': forms.ClearableFileInput(attrs={
                'class': 'form-control bg-dark text-white border-secondary',
                'accept': 'image/*',
                'capture': 'environment',
            }),
            'resolution_report': forms.Textarea(attrs={
                'class': 'form-control bg-dark text-white border-secondary',
                'rows': 4,
                'placeholder': 'Explain what was fixed, materials used, and final result...'
            }),
        }
        labels = {
            'resolution_image': 'Upload Resolution Proof (After)',
            'resolution_report': 'Work Completion Report',
        }