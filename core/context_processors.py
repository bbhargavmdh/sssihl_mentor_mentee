def role_flags(request):
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {}
    return {
        "is_admin_role": getattr(user, "is_admin_role", False),
        "is_mentor_role": getattr(user, "is_mentor_role", False),
        "is_mentee_role": getattr(user, "is_mentee_role", False),
    }
