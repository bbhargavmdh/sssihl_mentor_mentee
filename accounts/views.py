import io
from datetime import timedelta

import pandas as pd
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone

from .decorators import admin_required
from .forms import (
    ExcelImportForm,
    ForcedSetPasswordForm,
    MenteeAssignForm,
    MentorCreateForm,
    MentorEditForm,
    ProfilePhotoForm,
    StyledAuthenticationForm,
)
from .models import LoginAttempt, MenteeProfile, MentorProfile, User
from .utils import create_mentee_account, create_mentor_account, send_credentials_email


class RateLimitedLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = StyledAuthenticationForm
    redirect_authenticated_user = True

    def dispatch(self, request, *args, **kwargs):
        if request.method == "POST":
            username = request.POST.get("username", "")
            window_start = timezone.now() - timedelta(seconds=settings.LOGIN_LOCKOUT_SECONDS)
            recent_failures = LoginAttempt.objects.filter(
                username=username, success=False, timestamp__gte=window_start
            ).count()
            if recent_failures >= settings.LOGIN_MAX_ATTEMPTS:
                messages.error(
                    request,
                    "Too many failed login attempts. Please try again in a few minutes.",
                )
                return render(request, self.template_name, {"form": self.authentication_form()})
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        LoginAttempt.objects.create(
            username=form.get_user().username, ip_address=self.request.META.get("REMOTE_ADDR"), success=True
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        LoginAttempt.objects.create(
            username=self.request.POST.get("username", ""),
            ip_address=self.request.META.get("REMOTE_ADDR"),
            success=False,
        )
        return super().form_invalid(form)


class RoleAwareLogoutView(LogoutView):
    next_page = reverse_lazy("accounts:login")


@login_required
def force_password_change(request):
    if not request.user.must_change_password:
        return redirect("core:dashboard")
    if request.method == "POST":
        form = ForcedSetPasswordForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Password updated successfully.")
            return redirect("core:dashboard")
    else:
        form = ForcedSetPasswordForm(request.user)
    return render(request, "accounts/force_password_change.html", {"form": form})


@login_required
def profile(request):
    if request.method == "POST":
        form = ProfilePhotoForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile photo updated.")
            return redirect("accounts:profile")
    else:
        form = ProfilePhotoForm(instance=request.user)
    return render(request, "accounts/profile.html", {"form": form})


# ------------------------- Administrator: Mentor management -------------------------

@admin_required
def mentor_list(request):
    query = request.GET.get("q", "")
    mentors = MentorProfile.objects.select_related("user").all()
    if query:
        mentors = mentors.filter(
            Q(user__first_name__icontains=query)
            | Q(user__last_name__icontains=query)
            | Q(employee_id__icontains=query)
            | Q(department__icontains=query)
        )
    paginator = Paginator(mentors.order_by("user__first_name"), 20)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "accounts/mentor_list.html", {"page_obj": page_obj, "query": query})


@admin_required
def mentor_create(request):
    if request.method == "POST":
        form = MentorCreateForm(request.POST)
        if form.is_valid():
            create_mentor_account(**form.cleaned_data)
            messages.success(request, "Mentor account created and credentials emailed.")
            return redirect("accounts:mentor_list")
    else:
        form = MentorCreateForm()
    return render(request, "accounts/mentor_form.html", {"form": form, "title": "Add Mentor"})


@admin_required
def mentor_edit(request, pk):
    mentor = get_object_or_404(MentorProfile, pk=pk)
    if request.method == "POST":
        form = MentorEditForm(request.POST, instance=mentor)
        if form.is_valid():
            form.save()
            messages.success(request, "Mentor details updated.")
            return redirect("accounts:mentor_list")
    else:
        form = MentorEditForm(instance=mentor)
    return render(request, "accounts/mentor_form.html", {"form": form, "title": "Edit Mentor"})


@admin_required
def mentor_delete(request, pk):
    mentor = get_object_or_404(MentorProfile, pk=pk)
    if request.method == "POST":
        mentor.user.delete()
        messages.success(request, "Mentor account deleted.")
        return redirect("accounts:mentor_list")
    return render(request, "accounts/confirm_delete.html", {"object": mentor})


@admin_required
def mentor_reset_password(request, pk):
    mentor = get_object_or_404(MentorProfile, pk=pk)
    if request.method == "POST":
        mentor.user.set_password(settings.DEFAULT_USER_PASSWORD)
        mentor.user.must_change_password = True
        mentor.user.save()
        send_credentials_email(mentor.user, mentor.user.username, settings.DEFAULT_USER_PASSWORD, "Mentor")
        messages.success(request, "Password reset to default and emailed to the mentor.")
        return redirect("accounts:mentor_list")
    return render(request, "accounts/confirm_reset.html", {"object": mentor})


@admin_required
def mentor_import(request):
    if request.method == "POST":
        form = ExcelImportForm(request.POST, request.FILES)
        if form.is_valid():
            created, errors = _import_mentors_from_excel(request.FILES["excel_file"])
            messages.success(request, f"{created} mentor account(s) created.")
            for err in errors:
                messages.warning(request, err)
            return redirect("accounts:mentor_list")
    else:
        form = ExcelImportForm()
    return render(request, "accounts/import_form.html", {
        "form": form,
        "title": "Import Mentors",
        "columns": "Employee ID, Name, Department, Email",
    })


def _import_mentors_from_excel(file_obj):
    df = pd.read_excel(io.BytesIO(file_obj.read()))
    df.columns = [str(c).strip().lower() for c in df.columns]
    required = {"employee id", "name", "department", "email"}
    missing = required - set(df.columns)
    if missing:
        return 0, [f"Missing column(s): {', '.join(missing)}"]

    created, errors = 0, []
    for idx, row in df.iterrows():
        try:
            emp_id = str(row["employee id"]).strip()
            if MentorProfile.objects.filter(employee_id=emp_id).exists():
                errors.append(f"Row {idx + 2}: Employee ID {emp_id} already exists, skipped.")
                continue
            name = str(row["name"]).strip()
            parts = name.split(" ", 1)
            first_name, last_name = parts[0], (parts[1] if len(parts) > 1 else "")
            create_mentor_account(
                employee_id=emp_id,
                first_name=first_name,
                last_name=last_name,
                email=str(row["email"]).strip(),
                department=str(row["department"]).strip(),
            )
            created += 1
        except Exception as exc:
            errors.append(f"Row {idx + 2}: {exc}")
    return created, errors


# ------------------------- Administrator: Mentee management -------------------------

@admin_required
def mentee_list(request):
    query = request.GET.get("q", "")
    mentees = MenteeProfile.objects.select_related("user", "mentor__user").all()
    if query:
        mentees = mentees.filter(
            Q(user__first_name__icontains=query)
            | Q(user__last_name__icontains=query)
            | Q(registration_number__icontains=query)
            | Q(department__icontains=query)
        )
    paginator = Paginator(mentees.order_by("user__first_name"), 20)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "accounts/mentee_list.html", {"page_obj": page_obj, "query": query})


@admin_required
def mentee_assign(request, pk):
    mentee = get_object_or_404(MenteeProfile, pk=pk)
    if request.method == "POST":
        form = MenteeAssignForm(request.POST, instance=mentee)
        if form.is_valid():
            form.save()
            messages.success(request, "Mentor assignment updated.")
            return redirect("accounts:mentee_list")
    else:
        form = MenteeAssignForm(instance=mentee)
    return render(request, "accounts/mentee_assign.html", {"form": form, "mentee": mentee})


@admin_required
def mentee_reset_password(request, pk):
    mentee = get_object_or_404(MenteeProfile, pk=pk)
    if request.method == "POST":
        mentee.user.set_password(settings.DEFAULT_USER_PASSWORD)
        mentee.user.must_change_password = True
        mentee.user.save()
        send_credentials_email(mentee.user, mentee.user.username, settings.DEFAULT_USER_PASSWORD, "Mentee")
        messages.success(request, "Password reset to default and emailed to the student.")
        return redirect("accounts:mentee_list")
    return render(request, "accounts/confirm_reset.html", {"object": mentee})


@admin_required
def mentee_import(request):
    if request.method == "POST":
        form = ExcelImportForm(request.POST, request.FILES)
        if form.is_valid():
            created, errors = _import_mentees_from_excel(request.FILES["excel_file"])
            messages.success(request, f"{created} student account(s) created.")
            for err in errors:
                messages.warning(request, err)
            return redirect("accounts:mentee_list")
    else:
        form = ExcelImportForm()
    return render(request, "accounts/import_form.html", {
        "form": form,
        "title": "Import Students",
        "columns": "Registration Number, Name, Email, Assigned Mentor (Employee ID)",
    })


def _import_mentees_from_excel(file_obj):
    df = pd.read_excel(io.BytesIO(file_obj.read()))
    df.columns = [str(c).strip().lower() for c in df.columns]
    required = {"registration number", "name", "email", "assigned mentor"}
    missing = required - set(df.columns)
    if missing:
        return 0, [f"Missing column(s): {', '.join(missing)}"]

    created, errors = 0, []
    for idx, row in df.iterrows():
        try:
            reg_no = str(row["registration number"]).strip()
            if MenteeProfile.objects.filter(registration_number=reg_no).exists():
                errors.append(f"Row {idx + 2}: Registration {reg_no} already exists, skipped.")
                continue
            create_mentee_account(
                registration_number=reg_no,
                name=str(row["name"]).strip(),
                email=str(row["email"]).strip(),
                mentor_employee_id=str(row["assigned mentor"]).strip(),
            )
            created += 1
        except Exception as exc:
            errors.append(f"Row {idx + 2}: {exc}")
    return created, errors
