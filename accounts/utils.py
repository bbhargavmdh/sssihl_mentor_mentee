import logging

from django.conf import settings
from django.core.mail import send_mail
from django.utils.crypto import get_random_string

from .models import MenteeProfile, MentorProfile, User

logger = logging.getLogger(__name__)


def generate_username(first_name, last_name, identifier):
    base = f"{first_name}.{last_name}".lower().replace(" ", "") or identifier.lower()
    base = "".join(ch for ch in base if ch.isalnum() or ch == ".")
    candidate = base
    suffix = 1
    while User.objects.filter(username=candidate).exists():
        candidate = f"{base}{suffix}"
        suffix += 1
    return candidate


def create_mentor_account(employee_id, first_name, last_name, email, department):
    username = generate_username(first_name, last_name, employee_id)
    user = User.objects.create_user(
        username=username,
        email=email,
        first_name=first_name,
        last_name=last_name or "",
        role=User.Role.MENTOR,
        password=settings.DEFAULT_USER_PASSWORD,
        must_change_password=True,
    )
    profile = MentorProfile.objects.create(user=user, employee_id=employee_id, department=department)
    send_credentials_email(user, username, settings.DEFAULT_USER_PASSWORD, "Mentor")
    return profile


def create_mentee_account(registration_number, name, email, mentor_employee_id, department="", semester=""):
    parts = name.strip().split(" ", 1)
    first_name = parts[0]
    last_name = parts[1] if len(parts) > 1 else ""
    username = generate_username(first_name, last_name, registration_number)
    user = User.objects.create_user(
        username=username,
        email=email,
        first_name=first_name,
        last_name=last_name,
        role=User.Role.MENTEE,
        password=settings.DEFAULT_USER_PASSWORD,
        must_change_password=True,
    )
    mentor = None
    if mentor_employee_id:
        mentor = MentorProfile.objects.filter(employee_id=str(mentor_employee_id).strip()).first()
    profile = MenteeProfile.objects.create(
        user=user,
        registration_number=registration_number,
        mentor=mentor,
        department=department,
        current_semester=semester,
    )
    send_credentials_email(user, username, settings.DEFAULT_USER_PASSWORD, "Mentee")
    return profile


def send_credentials_email(user, username, password, role_label):
    if not user.email:
        return
    subject = f"Your SSSIHL Mentor-Mentee Portal Account ({role_label})"
    message = (
        f"Dear {user.get_full_name() or username},\n\n"
        f"An account has been created for you on the SSSIHL Mentor-Mentee Portal.\n\n"
        f"Username: {username}\n"
        f"Temporary Password: {password}\n\n"
        f"You will be required to change this password on first login.\n\n"
        f"Regards,\nSSSIHL Mentor-Mentee System"
    )
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True)
    except Exception:
        logger.exception("Failed to send credentials email to %s", user.email)
