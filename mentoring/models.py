from django.db import models

from accounts.models import MenteeProfile, MentorProfile
from meetings.models import Meeting


class MentoringRecord(models.Model):
    class ImprovementStatus(models.TextChoices):
        IMPROVING = "IMPROVING", "Improving"
        STABLE = "STABLE", "Stable"
        NEEDS_ATTENTION = "NEEDS_ATTENTION", "Needs Attention"

    meeting = models.OneToOneField(Meeting, on_delete=models.CASCADE, related_name="mentoring_record")
    mentor = models.ForeignKey(MentorProfile, on_delete=models.CASCADE, related_name="mentoring_records")
    mentee = models.ForeignKey(MenteeProfile, on_delete=models.CASCADE, related_name="mentoring_records")

    # Academic progress
    current_semester = models.CharField(max_length=20, blank=True)
    improvement_status = models.CharField(max_length=20, choices=ImprovementStatus.choices, blank=True)

    # Discussion
    remarks = models.TextField(blank=True)
    academic_challenges = models.TextField(blank=True)
    personal_issues = models.TextField(blank=True)
    emotional_psychological_concerns = models.TextField(blank=True)
    career_counseling = models.TextField(blank=True)
    examination_stress = models.TextField(blank=True)
    logistical_challenges = models.TextField(blank=True)

    # Goals
    short_term_goals = models.TextField(blank=True)
    long_term_goals = models.TextField(blank=True)
    personal_development_goals = models.TextField(blank=True)

    # Feedback
    mentor_comments = models.TextField(blank=True)
    student_reflection = models.TextField(blank=True)

    # Next meeting
    next_meeting_date = models.DateField(null=True, blank=True)
    next_meeting_focus = models.TextField(blank=True)

    pdf_file = models.FileField(upload_to="mentoring_pdfs/", blank=True, null=True)
    is_finalized = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Record: {self.mentee} - {self.meeting.meeting_date}"


class SubjectAttendance(models.Model):
    record = models.ForeignKey(MentoringRecord, on_delete=models.CASCADE, related_name="subjects")
    subject = models.CharField(max_length=120)
    attendance_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    performance_remarks = models.CharField(max_length=255, blank=True)


class ActionItem(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"

    record = models.ForeignKey(MentoringRecord, on_delete=models.CASCADE, related_name="action_items")
    task_description = models.CharField(max_length=255)
    assigned_to = models.CharField(max_length=120)
    deadline = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.PENDING)

    def __str__(self):
        return self.task_description
