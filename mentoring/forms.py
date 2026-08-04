from django import forms
from django.forms import inlineformset_factory

from .models import ActionItem, MentoringRecord, SubjectAttendance

TEXT_FIELDS_WIDGET = forms.Textarea(attrs={"class": "form-control", "rows": 2})


class MentoringRecordForm(forms.ModelForm):
    class Meta:
        model = MentoringRecord
        fields = [
            "current_semester", "improvement_status",
            "remarks", "academic_challenges", "personal_issues",
            "emotional_psychological_concerns", "career_counseling",
            "examination_stress", "logistical_challenges",
            "short_term_goals", "long_term_goals", "personal_development_goals",
            "mentor_comments", "student_reflection",
            "next_meeting_date", "next_meeting_focus",
        ]
        widgets = {
            "current_semester": forms.TextInput(attrs={"class": "form-control"}),
            "improvement_status": forms.Select(attrs={"class": "form-control"}),
            "remarks": TEXT_FIELDS_WIDGET,
            "academic_challenges": TEXT_FIELDS_WIDGET,
            "personal_issues": TEXT_FIELDS_WIDGET,
            "emotional_psychological_concerns": TEXT_FIELDS_WIDGET,
            "career_counseling": TEXT_FIELDS_WIDGET,
            "examination_stress": TEXT_FIELDS_WIDGET,
            "logistical_challenges": TEXT_FIELDS_WIDGET,
            "short_term_goals": TEXT_FIELDS_WIDGET,
            "long_term_goals": TEXT_FIELDS_WIDGET,
            "personal_development_goals": TEXT_FIELDS_WIDGET,
            "mentor_comments": TEXT_FIELDS_WIDGET,
            "student_reflection": TEXT_FIELDS_WIDGET,
            "next_meeting_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "next_meeting_focus": TEXT_FIELDS_WIDGET,
        }


SubjectAttendanceFormSet = inlineformset_factory(
    MentoringRecord, SubjectAttendance,
    fields=["subject", "attendance_percent", "performance_remarks"],
    extra=3, can_delete=True,
    widgets={
        "subject": forms.TextInput(attrs={"class": "form-control"}),
        "attendance_percent": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        "performance_remarks": forms.TextInput(attrs={"class": "form-control"}),
    },
)

ActionItemFormSet = inlineformset_factory(
    MentoringRecord, ActionItem,
    fields=["task_description", "assigned_to", "deadline", "status"],
    extra=2, can_delete=True,
    widgets={
        "task_description": forms.TextInput(attrs={"class": "form-control"}),
        "assigned_to": forms.TextInput(attrs={"class": "form-control"}),
        "deadline": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        "status": forms.Select(attrs={"class": "form-control"}),
    },
)
