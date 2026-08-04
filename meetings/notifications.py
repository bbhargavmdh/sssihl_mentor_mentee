import logging

from django.conf import settings
from django.core.mail import send_mail

from .models import Notification

logger = logging.getLogger(__name__)

ACTION_VERBS = {
    "scheduled": "scheduled a new",
    "rescheduled": "rescheduled your",
    "updated": "updated your",
    "cancelled": "cancelled your",
    "completed": "marked your",
}


def notify_students(meeting, action):
    """
    Emails and in-app-notifies ONLY the students attached to this specific
    meeting - never the mentor's other mentees, and never students who
    belong to a different mentor.
    """
    verb = ACTION_VERBS.get(action, action)
    subject = f"Mentoring Meeting {action.capitalize()} - SSSIHL"

    for mentee in meeting.students.all():
        user = mentee.user
        message = (
            f"Your mentor {meeting.mentor.user.get_full_name()} has {verb} "
            f"meeting on {meeting.meeting_date} at {meeting.meeting_time}."
        )
        Notification.objects.create(recipient=user, meeting=meeting, message=message)
        if user.email:
            try:
                send_mail(
                    subject,
                    (
                        f"Dear {user.get_full_name() or user.username},\n\n{message}\n\n"
                        f"Venue: {meeting.venue or 'TBA'}\n"
                        f"Notes: {meeting.notes or '-'}\n\n"
                        f"Regards,\nSSSIHL Mentor-Mentee System"
                    ),
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=True,
                )
            except Exception:
                logger.exception("Failed to email notification to %s", user.email)
