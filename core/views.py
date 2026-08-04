import io

import openpyxl
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from accounts.decorators import admin_required
from accounts.models import MenteeProfile, MentorProfile
from meetings.models import Meeting, Notification
from mentoring.models import ActionItem, MentoringRecord


@login_required
def dashboard(request):
    user = request.user
    if user.is_admin_role:
        return admin_dashboard(request)
    if user.is_mentor_role:
        return mentor_dashboard(request)
    return mentee_dashboard(request)


def admin_dashboard(request):
    today = timezone.now().date()
    context = {
        "total_mentors": MentorProfile.objects.count(),
        "total_students": MenteeProfile.objects.count(),
        "upcoming_meetings": Meeting.objects.filter(meeting_date__gte=today, status__in=["SCHEDULED", "RESCHEDULED"]).count(),
        "completed_meetings": Meeting.objects.filter(status="COMPLETED").count(),
        "pdfs_generated": MentoringRecord.objects.filter(is_finalized=True).count(),
        "department_stats": MentorProfile.objects.values("department").annotate(count=Count("id")).order_by("-count"),
        "monthly_meetings": (
            Meeting.objects.annotate(month=TruncMonth("meeting_date"))
            .values("month").annotate(count=Count("id")).order_by("month")
        ),
        "recent_meetings": Meeting.objects.select_related("mentor__user").order_by("-created_at")[:10],
    }
    return render(request, "core/admin_dashboard.html", context)


def mentor_dashboard(request):
    mentor = request.user.mentor_profile
    today = timezone.now().date()
    context = {
        "mentee_count": mentor.mentees.count(),
        "upcoming_meetings": Meeting.objects.filter(mentor=mentor, meeting_date__gte=today, status__in=["SCHEDULED", "RESCHEDULED"]).order_by("meeting_date")[:10],
        "pending_followups": ActionItem.objects.filter(record__mentor=mentor, status__in=["PENDING", "IN_PROGRESS"]).select_related("record__mentee__user")[:10],
        "recent_completed": Meeting.objects.filter(mentor=mentor, status="COMPLETED").order_by("-meeting_date")[:5],
        "recent_pdfs": MentoringRecord.objects.filter(mentor=mentor, is_finalized=True).order_by("-created_at")[:5],
        "notifications": Notification.objects.filter(recipient=request.user)[:5],
    }
    return render(request, "core/mentor_dashboard.html", context)


def mentee_dashboard(request):
    mentee = request.user.mentee_profile
    today = timezone.now().date()
    context = {
        "upcoming_meetings": Meeting.objects.filter(students=mentee, meeting_date__gte=today).order_by("meeting_date")[:10],
        "notifications": Notification.objects.filter(recipient=request.user)[:5],
        "recent_pdfs": MentoringRecord.objects.filter(mentee=mentee, is_finalized=True).order_by("-created_at")[:5],
        "previous_meetings": Meeting.objects.filter(students=mentee, status="COMPLETED").order_by("-meeting_date")[:5],
    }
    return render(request, "core/mentee_dashboard.html", context)


@admin_required
def global_search(request):
    query = request.GET.get("q", "").strip()
    results = {"mentors": [], "students": [], "meetings": []}
    if query:
        results["mentors"] = MentorProfile.objects.select_related("user").filter(
            Q(user__first_name__icontains=query) | Q(user__last_name__icontains=query)
            | Q(employee_id__icontains=query) | Q(department__icontains=query)
        )[:25]
        results["students"] = MenteeProfile.objects.select_related("user", "mentor__user").filter(
            Q(user__first_name__icontains=query) | Q(user__last_name__icontains=query)
            | Q(registration_number__icontains=query) | Q(department__icontains=query)
        )[:25]
        results["meetings"] = Meeting.objects.select_related("mentor__user").filter(
            Q(venue__icontains=query)
            | Q(room_visit__hostel_name__icontains=query)
            | Q(room_visit__room_number__icontains=query)
            | Q(meeting_date__icontains=query)
        )[:25]
    return render(request, "core/search_results.html", {"query": query, "results": results})


@admin_required
def reports(request):
    mentor_id = request.GET.get("mentor")
    department = request.GET.get("department")
    date_from = request.GET.get("date_from")
    date_to = request.GET.get("date_to")

    records = MentoringRecord.objects.filter(is_finalized=True).select_related("mentor__user", "mentee__user", "meeting")
    if mentor_id:
        records = records.filter(mentor_id=mentor_id)
    if department:
        records = records.filter(mentee__department__icontains=department)
    if date_from:
        records = records.filter(meeting__meeting_date__gte=date_from)
    if date_to:
        records = records.filter(meeting__meeting_date__lte=date_to)

    if request.GET.get("export") == "excel":
        return _export_records_excel(records)

    context = {
        "records": records.order_by("-meeting__meeting_date")[:200],
        "mentors": MentorProfile.objects.select_related("user").all(),
    }
    return render(request, "core/reports.html", context)


def _export_records_excel(records):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Mentoring Records"
    ws.append(["Student Name", "Registration No.", "Mentor", "Department", "Meeting Date", "Meeting Type", "Status"])
    for r in records:
        ws.append([
            r.mentee.user.get_full_name(), r.mentee.registration_number, r.mentor.user.get_full_name(),
            r.mentee.department, r.meeting.meeting_date.strftime("%Y-%m-%d"),
            r.meeting.get_meeting_type_display(), "Finalized" if r.is_finalized else "Draft",
        ])
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    response = HttpResponse(
        buffer.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = "attachment; filename=mentoring_records_report.xlsx"
    return response
