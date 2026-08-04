from django.urls import path

from . import views

app_name = "mentoring"

urlpatterns = [
    path("meeting/<int:meeting_id>/record/new/", views.record_create, name="record_create"),
    path("meeting/<int:meeting_id>/record/edit/", views.record_edit, name="record_edit"),
    path("records/", views.record_list, name="record_list"),
    path("records/<int:pk>/", views.record_detail, name="record_detail"),
    path("records/<int:pk>/pdf/", views.record_pdf_download, name="record_pdf"),
    path("records/mine/", views.my_records, name="my_records"),
    path("records/all/", views.all_records, name="all_records"),
]
