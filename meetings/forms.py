from django import forms

from .models import Meeting, RoomVisitDetail


class MeetingForm(forms.ModelForm):
    class Meta:
        model = Meeting
        fields = ["meeting_type", "students", "meeting_date", "meeting_time", "venue", "notes"]
        widgets = {
            "meeting_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "meeting_time": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "students": forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, mentor=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.mentor = mentor
        if mentor is not None:
            self.fields["students"].queryset = mentor.mentees.select_related("user")
        for name in ("meeting_type", "venue", "notes"):
            self.fields[name].widget.attrs.setdefault("class", "form-control")

    def clean_students(self):
        students = self.cleaned_data["students"]
        meeting_type = self.data.get("meeting_type") or self.initial.get("meeting_type")
        if meeting_type == Meeting.MeetingType.INDIVIDUAL and students.count() != 1:
            raise forms.ValidationError("An individual meeting must have exactly one student.")
        if not students:
            raise forms.ValidationError("Select at least one student.")
        return students


class RoomVisitDetailForm(forms.ModelForm):
    class Meta:
        model = RoomVisitDetail
        fields = ["hostel_name", "block", "floor", "room_number"]
        widgets = {f: forms.TextInput(attrs={"class": "form-control"}) for f in fields}
