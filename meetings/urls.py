from django.urls import path

from . import views

app_name = "meetings"

urlpatterns = [
    path("", views.meeting_list, name="meeting_list"),
    path("add/", views.meeting_create, name="meeting_create"),
    path("<int:pk>/edit/", views.meeting_edit, name="meeting_edit"),
    path("<int:pk>/cancel/", views.meeting_cancel, name="meeting_cancel"),
    path("<int:pk>/complete/", views.meeting_complete, name="meeting_complete"),
    path("mine/", views.my_meetings, name="my_meetings"),
    path("notifications/", views.notifications_list, name="notifications"),
]
