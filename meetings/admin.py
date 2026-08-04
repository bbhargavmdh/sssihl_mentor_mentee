from django.contrib import admin

from .models import Meeting, Notification, RoomVisitDetail


class RoomVisitInline(admin.StackedInline):
    model = RoomVisitDetail
    extra = 0


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ("mentor", "meeting_type", "meeting_date", "meeting_time", "status")
    list_filter = ("meeting_type", "status")
    inlines = [RoomVisitInline]
    search_fields = ("mentor__user__first_name", "mentor__user__last_name")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("recipient", "message", "is_read", "created_at")
    list_filter = ("is_read",)
