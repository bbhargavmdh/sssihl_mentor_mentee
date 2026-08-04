"""
Generates the official SSSIHL Weekly/Fortnightly Mentor-Mentee Report PDF,
laid out to match the institute's Word template: logo + header block,
Meeting Details, Participants, Academic Progress table, Challenges Faced,
Goals, Action Items table, Feedback, Next Meeting Plan, signature line.
"""
import io
import os

from django.conf import settings
from django.core.files.base import ContentFile
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

LOGO_PATH = settings.BASE_DIR / "static" / "img" / "sssihl_logo.png"

styles = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=13, alignment=1, spaceAfter=2, textColor=colors.HexColor("#7a1f1f"))
SUB = ParagraphStyle("Sub", parent=styles["Normal"], fontSize=9, alignment=1, textColor=colors.HexColor("#444444"))
H2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=11, spaceBefore=10, spaceAfter=4, textColor=colors.HexColor("#7a1f1f"))
BODY = ParagraphStyle("Body", parent=styles["Normal"], fontSize=9.5, leading=13)
LABEL = ParagraphStyle("Label", parent=styles["Normal"], fontSize=9.5, leading=13, fontName="Helvetica-Bold")


def _kv_table(pairs, col_widths=(4.5 * cm, 12.5 * cm)):
    rows = [[Paragraph(f"{label}:", LABEL), Paragraph(str(value) if value else "-", BODY)] for label, value in pairs]
    table = Table(rows, colWidths=col_widths)
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
    ]))
    return table


def build_mentoring_record_pdf(record):
    """Returns a BytesIO buffer containing the rendered PDF for a MentoringRecord."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=1.8 * cm, rightMargin=1.8 * cm, topMargin=1.5 * cm, bottomMargin=1.5 * cm,
    )
    elements = []

    # --- Header: logo + institute name -------------------------------
    if os.path.exists(LOGO_PATH):
        header_row = Table(
            [[Image(str(LOGO_PATH), width=1.7 * cm, height=1.7 * cm),
              Paragraph("Sri Sathya Sai Institute of Higher Learning<br/>"
                        "<font size=8>(Deemed to be University)</font><br/>"
                        "<font size=8>Nandigiri Campus [NDG]</font>", H1)]],
            colWidths=[2 * cm, 15 * cm],
        )
        header_row.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (1, 0), (1, 0), "CENTER")]))
        elements.append(header_row)
    else:
        elements.append(Paragraph("Sri Sathya Sai Institute of Higher Learning", H1))

    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "Weekly/Fortnightly Mentor-Mentee Report &mdash; Academic Year 2025-26",
        ParagraphStyle("Title", parent=H1, fontSize=12, textColor=colors.black, underlineWidth=1),
    ))
    elements.append(Spacer(1, 10))

    meeting = record.meeting
    room = getattr(meeting, "room_visit", None)
    venue = meeting.venue or (f"{room.hostel_name}, Block {room.block}, Room {room.room_number}" if room else "-")

    elements.append(Paragraph("Meeting Details", H2))
    elements.append(_kv_table([
        ("Department / Class", record.mentee.department or "-"),
        ("Reporting Period", meeting.get_meeting_type_display()),
        ("Date of Meeting", meeting.meeting_date.strftime("%d-%b-%Y")),
        ("Meeting Venue", venue),
    ]))

    elements.append(Paragraph("Participants", H2))
    elements.append(_kv_table([
        ("Mentor Name (Class Teacher)", record.mentor.user.get_full_name()),
        ("Mentee Name (Student)", record.mentee.user.get_full_name()),
        ("Registration Number", record.mentee.registration_number),
    ]))

    elements.append(Paragraph("Academic Progress", H2))
    subj_rows = [["Subject", "Attendance (%)", "Performance / Remarks"]]
    subjects = list(record.subjects.all())
    if subjects:
        for s in subjects:
            subj_rows.append([s.subject, f"{s.attendance_percent}" if s.attendance_percent is not None else "-", s.performance_remarks or "-"])
    else:
        subj_rows.append(["-", "-", "-"])
    subj_table = Table(subj_rows, colWidths=[5.5 * cm, 3.5 * cm, 8 * cm], repeatRows=1)
    subj_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7a1f1f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(subj_table)
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(f"<b>Current Semester:</b> {record.current_semester or '-'} &nbsp;&nbsp; "
                               f"<b>Improvement Status:</b> {record.get_improvement_status_display() if record.improvement_status else '-'}", BODY))

    elements.append(Paragraph("Challenges Faced", H2))
    challenge_pairs = [
        ("Remarks", record.remarks),
        ("Academic Challenges", record.academic_challenges),
        ("Personal Issues", record.personal_issues),
        ("Emotional / Psychological Concerns", record.emotional_psychological_concerns),
        ("Career Counseling", record.career_counseling),
        ("Examination Stress", record.examination_stress),
        ("Logistical Challenges", record.logistical_challenges),
    ]
    elements.append(_kv_table(challenge_pairs))

    elements.append(Paragraph("Goals for Next Week/Fortnight", H2))
    elements.append(_kv_table([
        ("Short-Term Goals", record.short_term_goals),
        ("Long-Term Goals", record.long_term_goals),
        ("Personal Development Goals", record.personal_development_goals),
    ]))

    elements.append(Paragraph("Action Items / Follow-up", H2))
    action_rows = [["Task", "Assigned To", "Deadline", "Status"]]
    items = list(record.action_items.all())
    if items:
        for a in items:
            action_rows.append([a.task_description, a.assigned_to, a.deadline.strftime("%d-%b-%Y") if a.deadline else "-", a.get_status_display()])
    else:
        action_rows.append(["-", "-", "-", "-"])
    action_table = Table(action_rows, colWidths=[6 * cm, 4 * cm, 3.5 * cm, 3.5 * cm], repeatRows=1)
    action_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7a1f1f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    elements.append(action_table)

    elements.append(Paragraph("Feedback", H2))
    elements.append(_kv_table([
        ("Mentor's Comments", record.mentor_comments),
        ("Mentee's Reflections", record.student_reflection),
    ]))

    elements.append(Paragraph("Next Meeting Plan", H2))
    elements.append(_kv_table([
        ("Tentative Date", record.next_meeting_date.strftime("%d-%b-%Y") if record.next_meeting_date else "-"),
        ("Focus Areas", record.next_meeting_focus),
    ]))

    elements.append(Spacer(1, 30))
    elements.append(Paragraph("_______________________________", BODY))
    elements.append(Paragraph("Mentor's Name and Signature", BODY))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_and_attach_pdf(record):
    buffer = build_mentoring_record_pdf(record)
    filename = f"mentoring_record_{record.mentee.registration_number}_{record.meeting.meeting_date}.pdf"
    record.pdf_file.save(filename, ContentFile(buffer.read()), save=True)
    return record.pdf_file
