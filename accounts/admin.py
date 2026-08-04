from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import LoginAttempt, MenteeProfile, MentorProfile, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "first_name", "last_name", "role", "is_active")
    list_filter = ("role", "is_active")
    fieldsets = UserAdmin.fieldsets + (
        ("Role & Portal Info", {"fields": ("role", "must_change_password", "phone_number", "profile_photo")}),
    )


@admin.register(MentorProfile)
class MentorProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "employee_id", "department", "mentee_count")
    search_fields = ("employee_id", "user__first_name", "user__last_name")


@admin.register(MenteeProfile)
class MenteeProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "registration_number", "mentor", "current_semester")
    search_fields = ("registration_number", "user__first_name", "user__last_name")
    list_filter = ("department",)


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ("username", "ip_address", "success", "timestamp")
    list_filter = ("success",)
