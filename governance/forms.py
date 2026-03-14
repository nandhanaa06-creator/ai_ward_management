from django import forms
from .models import Meeting

class MeetingForm(forms.ModelForm):
    class Meta:
        model = Meeting
        fields = ['title', 'description', 'meeting_date', 'location', 'agenda_pdf']
        widgets = {
            'meeting_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        }