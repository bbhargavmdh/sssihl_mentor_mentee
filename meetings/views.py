from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.decorators import mentee_required, mentor_required
from .forms import MeetingForm, RoomVisitDetailForm
from .models import Meeting, Notification
from .notifications import notify_students


@mentor_required
def meeting_list(request):
    mentor = request.user.mentor_profile
    query = request.GET.get("q", "")
    meetings = Meeting.objects.filter(mentor=mentor).prefetch_related("students__user")
    if query:
        meetings = meetings.filter(
            Q(venue__icontains=query) | Q(students__user__first_name__icontains=query)
        ).distinct()
    paginator = Paginator(meetings, 15)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "meetings/meeting_list.html", {"page_obj": page_obj, "query": query})


@mentor_required
def meeting_create(request):
    mentor = request.user.mentor_profile
    if request.method == "POST":
        form = MeetingForm(request.POST, mentor=mentor)
        room_form = RoomVisitDetailForm(request.POST)
        is_room_visit = request.POST.get("meeting_type") == Meeting.MeetingType.ROOM_VISIT
        if form.is_valid() and (not is_room_visit or room_form.is_valid()):
            meeting = form.save(commit=False)
            meeting.mentor = mentor
            meeting.save()
            form.save_m2m()
            if is_room_visit:
                room = room_form.save(commit=False)
                room.meeting = meeting
                room.save()
            notify_students(meeting, "scheduled")
            messages.success(request, "Meeting scheduled and students notified.")
            return redirect("meetings:meeting_list")
    else:
        form = MeetingForm(mentor=mentor)
        room_form = RoomVisitDetailForm()
    return render(request, "meetings/meeting_form.html", {
        "form": form, "room_form": room_form, "title": "Schedule Meeting",
    })


@mentor_required
def meeting_edit(request, pk):
    mentor = request.user.mentor_profile
    meeting = get_object_or_404(Meeting, pk=pk, mentor=mentor)
    room_instance = getattr(meeting, "room_visit", None)
    if request.method == "POST":
        form = MeetingForm(request.POST, instance=meeting, mentor=mentor)
        room_form = RoomVisitDetailForm(request.POST, instance=room_instance)
        is_room_visit = request.POST.get("meeting_type") == Meeting.MeetingType.ROOM_VISIT
        if form.is_valid() and (not is_room_visit or room_form.is_valid()):
            was_rescheduled = (
                form.cleaned_data["meeting_date"] != meeting.meeting_date
                or form.cleaned_data["meeting_time"] != meeting.meeting_time
            )
            meeting = form.save(commit=False)
            meeting.status = Meeting.Status.RESCHEDULED if was_rescheduled else meeting.status
            meeting.save()
            form.save_m2m()
            if is_room_visit:
                room = room_form.save(commit=False)
                room.meeting = meeting
                room.save()
            notify_students(meeting, "rescheduled" if was_rescheduled else "updated")
            messages.success(request, "Meeting updated and students notified.")
            return redirect("meetings:meeting_list")
    else:
        form = MeetingForm(instance=meeting, mentor=mentor)
        room_form = RoomVisitDetailForm(instance=room_instance)
    return render(request, "meetings/meeting_form.html", {
        "form": form, "room_form": room_form, "title": "Update Meeting",
    })


@mentor_required
def meeting_cancel(request, pk):
    mentor = request.user.mentor_profile
    meeting = get_object_or_404(Meeting, pk=pk, mentor=mentor)
    if request.method == "POST":
        meeting.status = Meeting.Status.CANCELLED
        meeting.save()
        notify_students(meeting, "cancelled")
        messages.success(request, "Meeting cancelled and students notified.")
        return redirect("meetings:meeting_list")
    return render(request, "meetings/confirm_cancel.html", {"meeting": meeting})


@mentor_required
def meeting_complete(request, pk):
    mentor = request.user.mentor_profile
    meeting = get_object_or_404(Meeting, pk=pk, mentor=mentor)
    if request.method == "POST":
        meeting.status = Meeting.Status.COMPLETED
        meeting.save()
        messages.success(request, "Meeting marked as completed. You can now fill the mentoring record.")
        return redirect("mentoring:record_create", meeting_id=meeting.id)
    return render(request, "meetings/confirm_complete.html", {"meeting": meeting})


@mentee_required
def my_meetings(request):
    mentee = request.user.mentee_profile
    meetings = Meeting.objects.filter(students=mentee).prefetch_related("students__user")
    paginator = Paginator(meetings, 15)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "meetings/my_meetings.html", {"page_obj": page_obj})


@login_required
def notifications_list(request):
    notifications = Notification.objects.filter(recipient=request.user)
    notifications.filter(is_read=False).update(is_read=True)
    paginator = Paginator(notifications, 20)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "meetings/notifications.html", {"page_obj": page_obj})
