from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from .models import Survey, SurveyField, Submission, SubmissionFile
from .forms import SurveyForm, SurveyFieldFormSet, DynamicSubmissionForm

def is_admin_or_ward(user):
    return user.is_authenticated and (user.role == 'panchayath_admin' or user.role == 'ward_member')

@login_required
@user_passes_test(is_admin_or_ward, login_url='/accounts/login/')
def manage_surveys(request):
    """
    Dashboard for admins to see and manage data collection forms.
    """
    surveys = Survey.objects.filter(created_by=request.user).order_by('-created_at')
    return render(request, 'surveys/manage.html', {'surveys': surveys})

@login_required
@user_passes_test(is_admin_or_ward, login_url='/accounts/login/')
def create_survey(request, survey_id=None):
    """
    Interface to build a new survey or edit an existing one.
    Uses formsets for dynamic fields.
    """
    survey = None
    if survey_id:
        survey = get_object_or_404(Survey, id=survey_id, created_by=request.user)
    
    if request.method == 'POST':
        form = SurveyForm(request.POST, instance=survey)
        formset = SurveyFieldFormSet(request.POST, instance=survey)
        
        if form.is_valid() and formset.is_valid():
            survey = form.save(commit=False)
            survey.created_by = request.user
            survey.save()
            formset.instance = survey
            formset.save()
            messages.success(request, f'Survey "{survey.title}" has been saved.')
            return redirect('manage_surveys')
    else:
        form = SurveyForm(instance=survey)
        formset = SurveyFieldFormSet(instance=survey)
    
    return render(request, 'surveys/create.html', {
        'form': form,
        'formset': formset,
        'survey': survey
    })

def render_survey(request, slug):
    """
    Public citizen-facing view to submit data.
    """
    survey = get_object_or_404(Survey, slug=slug, is_active=True)
    
    # Check expiry
    if survey.expiry_date and survey.expiry_date < timezone.now():
        return render(request, 'surveys/expired.html', {'survey': survey})
    
    if request.method == 'POST':
        form = DynamicSubmissionForm(survey, request.POST, request.FILES)
        if form.is_valid():
            submission = Submission.objects.create(survey=survey)
            data = {}
            for field in survey.fields.all():
                val = form.cleaned_data.get(f'field_{field.id}')
                if field.field_type == 'file' and val:
                    SubmissionFile.objects.create(
                        submission=submission,
                        field_label=field.label,
                        file=val
                    )
                else:
                    data[field.label] = str(val) if val is not None else ""
            
            submission.data = data
            submission.save()
            messages.success(request, 'Your details have been submitted successfully.')
            return render(request, 'surveys/success.html', {'survey': survey})
    else:
        form = DynamicSubmissionForm(survey)
    
    return render(request, 'surveys/render.html', {
        'survey': survey,
        'form': form
    })

@login_required
@user_passes_test(is_admin_or_ward, login_url='/accounts/login/')
def survey_submissions(request, survey_id):
    """
    View to display collected data in a tabular format.
    """
    survey = get_object_or_404(Survey, id=survey_id, created_by=request.user)
    submissions = survey.submissions.all().order_by('-submitted_at')
    
    # Prepare dynamic headers
    headers = [field.label for field in survey.fields.all()]
    
    return render(request, 'surveys/submissions.html', {
        'survey': survey,
        'submissions': submissions,
        'headers': headers
    })

@login_required
@user_passes_test(is_admin_or_ward, login_url='/accounts/login/')
def delete_survey(request, survey_id):
    survey = get_object_or_404(Survey, id=survey_id, created_by=request.user)
    if request.method == 'POST':
        survey.delete()
        messages.success(request, 'Survey deleted successfully.')
    return redirect('manage_surveys')
