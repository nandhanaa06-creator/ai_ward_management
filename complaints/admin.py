from django.contrib import admin
from .models import Complaint, ComplaintMessage, ComplaintStatusHistory, ComplaintFeedback

admin.site.register(Complaint)
admin.site.register(ComplaintMessage)
admin.site.register(ComplaintStatusHistory)
admin.site.register(ComplaintFeedback)
