from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import admin_required, mentee_required, mentor_required
from meetings.models import Meeting

from .forms import ActionItemFormSet, MentoringRecordForm, SubjectAttendanceFormSet
from .models import MentoringRecord
from .pdf import generate_and_attach_pdf


@mentor_required
def record_create(request, meeting_id):
    mentor = request.user.mentor_profile
    meeting = get_object_or_404(Meeting, pk=meeting_id, mentor=mentor)
    record, _ = MentoringRecord.objects.get_or_create(
        meeting=meeting,
        defaults={"mentor": mentor, "mentee": meeting.students.first()},
    )

    if request.method == "POST":
        form = MentoringRecordForm(request.POST, instance=record)
        subject_fs = SubjectAttendanceFormSet(request.POST, instance=record, prefix="subjects")
        action_fs = ActionItemFormSet(request.POST, instance=record, prefix="actions")
        if form.is_valid() and subject_fs.is_valid() and action_fs.is_valid():
            record = form.save()
            subject_fs.save()
            action_fs.save()
            if "finalize" in request.POST:
                record.is_finalized = True
                record.save()
                generate_and_attach_pdf(record)
                messages.success(request, "Mentoring record finalized and PDF generated.")
                return redirect("mentoring:record_detail", pk=record.pk)
            messages.success(request, "Mentoring record saved as draft.")
            return redirect("mentoring:record_edit", meeting_id=meeting.id)
    else:
        form = MentoringRecordForm(instance=record)
        subject_fs = SubjectAttendanceFormSet(instance=record, prefix="subjects")
        action_fs = ActionItemFormSet(instance=record, prefix="actions")

    return render(request, "mentoring/record_form.html", {
        "form": form, "subject_fs": subject_fs, "action_fs": action_fs,
        "meeting": meeting, "record": record,
    })


# record_edit reuses the same view/template
record_edit = record_create


@mentor_required
def record_list(request):
    mentor = request.user.mentor_profile
    records = MentoringRecord.objects.filter(mentor=mentor).select_related("mentee__user", "meeting")
    paginator = Paginator(records, 15)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "mentoring/record_list.html", {"page_obj": page_obj})


@login_required
def record_detail(request, pk):
    record = get_object_or_404(MentoringRecord, pk=pk)
    user = request.user
    allowed = (
        user.is_admin_role
        or (user.is_mentor_role and record.mentor.user_id == user.id)
        or (user.is_mentee_role and record.mentee.user_id == user.id)
    )
    if not allowed:
        raise Http404
    return render(request, "mentoring/record_detail.html", {"record": record})


@login_required
def record_pdf_download(request, pk):
    record = get_object_or_404(MentoringRecord, pk=pk)
    user = request.user
    allowed = (
        user.is_admin_role
        or (user.is_mentor_role and record.mentor.user_id == user.id)
        or (user.is_mentee_role and record.mentee.user_id == user.id)
    )
    if not allowed or not record.pdf_file:
        raise Http404
    return FileResponse(record.pdf_file.open("rb"), as_attachment=True, filename=record.pdf_file.name.split("/")[-1])


@mentee_required
def my_records(request):
    mentee = request.user.mentee_profile
    records = MentoringRecord.objects.filter(mentee=mentee, is_finalized=True).select_related("meeting")
    paginator = Paginator(records, 15)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "mentoring/my_records.html", {"page_obj": page_obj})


@admin_required
def all_records(request):
    records = MentoringRecord.objects.filter(is_finalized=True).select_related("mentee__user", "mentor__user")
    mentor_filter = request.GET.get("mentor")
    if mentor_filter:
        records = records.filter(mentor_id=mentor_filter)
    paginator = Paginator(records, 20)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "mentoring/all_records.html", {"page_obj": page_obj})
