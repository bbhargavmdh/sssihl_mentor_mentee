# SSSIHL Mentor-Mentee Management System

A production-ready Django application for managing the mentor-mentee process at
Sri Sathya Sai Institute of Higher Learning.

## Features
- Three roles (Administrator, Mentor, Mentee) with no public signup - accounts are
  created by the Administrator (manually or via Excel import) or from the terminal.
- Individual, Group, and Room Visit (hostel) meetings with scheduling, rescheduling,
  cancellation, and completion, each triggering email + in-app notifications scoped
  only to the students on that specific meeting.
- Full mentoring record capture (academic progress, challenges, goals, action items,
  feedback, next meeting) with an automatic PDF generated on finalization, styled to
  match the institute's official report template.
- Role-scoped dashboards, global search, and an Excel-exportable reports view.
- Render-ready deployment (Procfile, render.yaml, runtime.txt, WhiteNoise, Postgres
  via DATABASE_URL) that also runs unmodified on SQLite for local development.

## Local setup
```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # edit as needed; sqlite works out of the box
python manage.py migrate
python manage.py createadmin --username admin --email admin@sssihl.edu.in
python manage.py runserver
```
Then log in at http://127.0.0.1:8000/accounts/login/ with the admin account you just
created, and use the Mentors/Students pages (or Excel import) to onboard everyone else.

## Deploying to Render
1. Push this repo to GitHub.
2. In Render, "New +" -> "Blueprint", point it at the repo - `render.yaml` provisions
   the web service and a free Postgres database automatically.
3. Set `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` (a Gmail App Password) in the Render
   dashboard's environment variables - `render.yaml` marks these `sync: false` so
   they aren't committed to source control.
4. After the first deploy, open a shell on the service (or run one-off job) and run:
   `python manage.py createadmin`
5. Visit the deployed URL and log in.

## Migrating off Render later
Nothing here is Render-specific except the `render.yaml` blueprint file itself.
Point `DATABASE_URL` at any PostgreSQL server, run `python manage.py migrate`, and
serve with `gunicorn config.wsgi:application` behind any reverse proxy (the
`Procfile` command works as-is on a VPS with a process manager like systemd/supervisor).

## Project layout
- `accounts/` - custom User model, roles, mentor/mentee profiles, Excel import, auth
- `meetings/` - Meeting + RoomVisitDetail + Notification models and views
- `mentoring/` - MentoringRecord, subjects, action items, and the ReportLab PDF builder
- `core/` - role-aware dashboards, global search, reports/export
- `templates/` - Bootstrap 5 templates styled for SSSIHL
- `static/img/sssihl_logo.png` - logo extracted from your uploaded template, reused
  in the UI and on every generated PDF

## Notes on the uploaded template
Your uploaded `Mentor_Mentee_Report_Template.docx` was used as the reference for the
generated PDF's section structure (Meeting Details, Participants, Academic Progress,
Challenges, Goals, Action Items, Feedback, Next Meeting) and its logo. If you'd like
the PDF pixel-matched further (exact fonts/colors/table borders from the Word file),
send specifics and I can tighten `mentoring/pdf.py` to match even more closely.
