from django import forms
from .models import Meeting

class MeetingForm(forms.ModelForm):
    class Meta:
        model = Meeting
        fields = ['ward', 'title', 'description', 'meeting_date', 'location', 'agenda_pdf']
        widgets = {
            'ward': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Meeting Title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Topics for discussion...'}),
            'meeting_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Venue'}),
            'agenda_pdf': forms.FileInput(attrs={'class': 'form-control'}),
        }
        error_messages = {
            'ward': {
                'required': 'Please select a ward for this meeting.',
            }
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['ward'].empty_label = "Select a Ward"

class MeetingMinutesForm(forms.ModelForm):
    """
    Form for Ward Members to publish outcomes after a meeting.
    """
    class Meta:
        model = Meeting
        fields = ['minutes_summary', 'minutes_pdf']
        widgets = {
            'minutes_summary': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 5, 
                'placeholder': 'Summarize the internal decisions and outcomes of the meeting...'
            }),
            'minutes_pdf': forms.FileInput(attrs={'class': 'form-control'}),
        }

from .models import MeetingSummary

class MeetingSummaryForm(forms.ModelForm):
    class Meta:
        model = MeetingSummary
        fields = ['summary_text', 'decisions_taken']
        widgets = {
            'summary_text': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 5, 
                'placeholder': 'Overall discussion summary...'
            }),
            'decisions_taken': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 5, 
                'placeholder': 'List the specific decisions made (e.g., - Approval of new park)'
            }),
        }

from .models import MeetingFeedback

class MeetingFeedbackForm(forms.ModelForm):
    class Meta:
        model = MeetingFeedback
        fields = ['comment', 'is_question']
        widgets = {
            'comment': forms.Textarea(attrs={
                'class': 'form-control shadow-sm',
                'rows': 3,
                'placeholder': 'Share your thoughts or ask a question about the decisions...'
            }),
            'is_question': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'is_question': 'Mark as a Question'
        }