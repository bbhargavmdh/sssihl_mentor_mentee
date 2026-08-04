from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.RateLimitedLoginView.as_view(), name="login"),
    path("logout/", views.RoleAwareLogoutView.as_view(), name="logout"),
    path("password/change/", views.force_password_change, name="force_password_change"),
    path("profile/", views.profile, name="profile"),

    path("mentors/", views.mentor_list, name="mentor_list"),
    path("mentors/add/", views.mentor_create, name="mentor_create"),
    path("mentors/<int:pk>/edit/", views.mentor_edit, name="mentor_edit"),
    path("mentors/<int:pk>/delete/", views.mentor_delete, name="mentor_delete"),
    path("mentors/<int:pk>/reset-password/", views.mentor_reset_password, name="mentor_reset_password"),
    path("mentors/import/", views.mentor_import, name="mentor_import"),

    path("mentees/", views.mentee_list, name="mentee_list"),
    path("mentees/<int:pk>/assign/", views.mentee_assign, name="mentee_assign"),
    path("mentees/<int:pk>/reset-password/", views.mentee_reset_password, name="mentee_reset_password"),
    path("mentees/import/", views.mentee_import, name="mentee_import"),
]
