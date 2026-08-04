from django.contrib import admin

from .models import ActionItem, MentoringRecord, SubjectAttendance


class SubjectInline(admin.TabularInline):
    model = SubjectAttendance
    extra = 0


class ActionItemInline(admin.TabularInline):
    model = ActionItem
    extra = 0


@admin.register(MentoringRecord)
class MentoringRecordAdmin(admin.ModelAdmin):
    list_display = ("mentee", "mentor", "created_at", "is_finalized")
    list_filter = ("is_finalized",)
    inlines = [SubjectInline, ActionItemInline]
