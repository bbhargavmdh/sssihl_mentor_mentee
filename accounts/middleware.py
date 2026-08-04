from django.shortcuts import redirect
from django.urls import reverse


EXEMPT_PATH_PREFIXES = (
    "/accounts/password/change/",
    "/accounts/login/",
    "/accounts/logout/",
    "/static/",
    "/media/",
    "/django-admin/",
)


class ForcePasswordChangeMiddleware:
    """
    Redirects any authenticated user who still has the default/assigned
    password to the forced password-change page before they can reach
    anything else in the dashboard.

    Uses request.path rather than request.resolver_match because
    resolver_match is not yet populated at the point early middleware
    runs (it is only set once URL resolution happens deeper in the
    response cycle) - checking it here would always be None and cause
    a redirect loop.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user and user.is_authenticated and getattr(user, "must_change_password", False):
            if not request.path.startswith(EXEMPT_PATH_PREFIXES):
                return redirect(reverse("accounts:force_password_change"))
        return self.get_response(request)
