from django import forms
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm

from .models import MenteeProfile, MentorProfile, User


class StyledAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"


class ForcedSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"

    def save(self, commit=True):
        user = super().save(commit=False)
        user.must_change_password = False
        if commit:
            user.save()
        return user


class MentorCreateForm(forms.Form):
    employee_id = forms.CharField(max_length=30)
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField()
    department = forms.CharField(max_length=120)

    def clean_employee_id(self):
        emp_id = self.cleaned_data["employee_id"]
        if MentorProfile.objects.filter(employee_id=emp_id).exists():
            raise forms.ValidationError("A mentor with this Employee ID already exists.")
        return emp_id

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email


class MentorEditForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField()

    class Meta:
        model = MentorProfile
        fields = ["employee_id", "department"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["first_name"].initial = self.instance.user.first_name
            self.fields["last_name"].initial = self.instance.user.last_name
            self.fields["email"].initial = self.instance.user.email

    def save(self, commit=True):
        profile = super().save(commit=commit)
        profile.user.first_name = self.cleaned_data["first_name"]
        profile.user.last_name = self.cleaned_data["last_name"]
        profile.user.email = self.cleaned_data["email"]
        if commit:
            profile.user.save()
        return profile


class MenteeAssignForm(forms.ModelForm):
    class Meta:
        model = MenteeProfile
        fields = ["mentor"]


class ProfilePhotoForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["profile_photo"]


class ExcelImportForm(forms.Form):
    excel_file = forms.FileField(help_text="Upload a .xlsx file")
