from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            if request.user.role not in roles:
                raise PermissionDenied("You do not have permission to access this page.")
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


def admin_required(view_func):
    return role_required("ADMIN")(view_func)


def mentor_required(view_func):
    return role_required("MENTOR")(view_func)


def mentee_required(view_func):
    return role_required("MENTEE")(view_func)
