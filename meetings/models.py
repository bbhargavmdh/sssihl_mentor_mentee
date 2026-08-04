from django.conf import settings
from django.db import models

from accounts.models import MenteeProfile, MentorProfile


class Meeting(models.Model):
    class MeetingType(models.TextChoices):
        INDIVIDUAL = "INDIVIDUAL", "Individual Meeting"
        GROUP = "GROUP", "Group Meeting"
        ROOM_VISIT = "ROOM_VISIT", "Room Visit Meeting"

    class Status(models.TextChoices):
        SCHEDULED = "SCHEDULED", "Scheduled"
        RESCHEDULED = "RESCHEDULED", "Rescheduled"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    mentor = models.ForeignKey(MentorProfile, on_delete=models.CASCADE, related_name="meetings")
    meeting_type = models.CharField(max_length=15, choices=MeetingType.choices)
    students = models.ManyToManyField(MenteeProfile, related_name="meetings")
    meeting_date = models.DateField()
    meeting_time = models.TimeField()
    venue = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.SCHEDULED)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-meeting_date", "-meeting_time"]

    def __str__(self):
        return f"{self.get_meeting_type_display()} on {self.meeting_date} ({self.mentor})"

    @property
    def is_room_visit(self):
        return self.meeting_type == self.MeetingType.ROOM_VISIT


class RoomVisitDetail(models.Model):
    meeting = models.OneToOneField(Meeting, on_delete=models.CASCADE, related_name="room_visit")
    hostel_name = models.CharField(max_length=120)
    block = models.CharField(max_length=50, blank=True)
    floor = models.CharField(max_length=20, blank=True)
    room_number = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.hostel_name} - Room {self.room_number}"


class Notification(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name="notifications", null=True, blank=True)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.message
