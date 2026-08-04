from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Single custom user model for all three roles. Role is assigned
    internally by an Administrator - it is never chosen at signup,
    because there is no public signup for any role.
    """

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Administrator"
        MENTOR = "MENTOR", "Mentor"
        MENTEE = "MENTEE", "Mentee"

    role = models.CharField(max_length=10, choices=Role.choices)
    must_change_password = models.BooleanField(default=True)
    phone_number = models.CharField(max_length=20, blank=True)
    profile_photo = models.ImageField(upload_to="profile_photos/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN

    @property
    def is_mentor_role(self):
        return self.role == self.Role.MENTOR

    @property
    def is_mentee_role(self):
        return self.role == self.Role.MENTEE


class MentorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="mentor_profile")
    employee_id = models.CharField(max_length=30, unique=True)
    department = models.CharField(max_length=120)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.employee_id})"

    @property
    def mentee_count(self):
        return self.mentees.count()


class MenteeProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="mentee_profile")
    registration_number = models.CharField(max_length=30, unique=True)
    department = models.CharField(max_length=120, blank=True)
    current_semester = models.CharField(max_length=20, blank=True)
    mentor = models.ForeignKey(
        MentorProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name="mentees"
    )

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.registration_number})"


class LoginAttempt(models.Model):
    """Backing store for simple login rate limiting."""

    username = models.CharField(max_length=150)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    success = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["username", "timestamp"])]
