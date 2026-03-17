from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from governance.models import Meeting
from accounts.models import User

class Command(BaseCommand):
    help = 'Sends reminders to ward citizens 24 hours before a meeting starts.'

    def handle(self, *args, **kwargs):
        now = timezone.now()
        reminder_window_start = now + timedelta(hours=23)
        reminder_window_end = now + timedelta(hours=25)

        # Find meetings starting in ~24 hours
        upcoming_meetings = Meeting.objects.filter(
            meeting_date__range=(reminder_window_start, reminder_window_end)
        )

        if not upcoming_meetings.exists():
            self.stdout.write(self.style.SUCCESS('No meetings found in the 24h reminder window.'))
            return

        for meeting in upcoming_meetings:
            self.stdout.write(f'Processing reminders for meeting: {meeting.title}')
            
            # Identify citizens in the same ward
            citizens = User.objects.filter(ward=meeting.ward, role='citizen')
            
            for citizen in citizens:
                # In a real system, we would trigger an email or SMS here
                # For this demo, we simulate the notification logic
                self.stdout.write(self.style.NOTICE(
                    f'NOTIFICATION SENT to {citizen.username} ({citizen.email}): '
                    f'Reminder: The Grama Sabha meeting "{meeting.title}" starts in 24 hours at {meeting.location}.'
                ))

        self.stdout.write(self.style.SUCCESS(f'Successfully processed reminders for {upcoming_meetings.count()} meetings.'))
