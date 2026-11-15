"""Load the versioned, synthetic demonstration dataset exactly once."""

import json
import os
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from learning.models import Course, DemoState, Enrollment, Material, Organization, User


def build_handout(course_data, organization_name):
    """Return a deterministic original PDF from the fixture content."""
    buffer = BytesIO()
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Brand", fontName="Helvetica-Bold", fontSize=9,
                              textColor=colors.HexColor("#16765b"), spaceAfter=12))
    styles.add(ParagraphStyle(name="HandoutTitle", fontName="Helvetica-Bold", fontSize=22,
                              leading=27, textColor=colors.HexColor("#142b44"), spaceAfter=12))
    styles.add(ParagraphStyle(name="HandoutBody", fontName="Helvetica", fontSize=10,
                              leading=14, textColor=colors.HexColor("#334155"), spaceAfter=10))
    styles.add(ParagraphStyle(name="HandoutHeading", fontName="Helvetica-Bold", fontSize=12,
                              leading=16, textColor=colors.HexColor("#142b44"), spaceBefore=9,
                              spaceAfter=6))
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=24*mm, leftMargin=24*mm,
                            topMargin=22*mm, bottomMargin=24*mm,
                            title=f"{course_data['title']} - Study Notes", author="Access Granted")
    story = [Paragraph("ACCESS GRANTED / COURSE HANDOUT", styles["Brand"]),
             Paragraph(escape(course_data["title"]), styles["HandoutTitle"]),
             Paragraph(escape(organization_name), styles["HandoutBody"]),
             Paragraph("Learning objective", styles["HandoutHeading"]),
             Paragraph(escape(course_data["objective"]), styles["HandoutBody"]), Spacer(1, 2*mm)]
    for lesson in course_data["lessons"]:
        story.extend([Paragraph(escape(lesson["title"]), styles["HandoutHeading"]),
                      Paragraph(escape(lesson["body"]).replace("\n\n", "<br/><br/>"), styles["HandoutBody"])])
    story.extend([Paragraph("Practice and discussion", styles["HandoutHeading"]),
                  Paragraph(escape(course_data["exercise"]), styles["HandoutBody"])])

    def footer(canvas, document):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#d9e5e2"))
        canvas.line(24*mm, 19*mm, 186*mm, 19*mm)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#64748b"))
        canvas.drawString(24*mm, 14*mm, "Original synthetic teaching material | Access Granted")
        canvas.drawRightString(186*mm, 14*mm, str(document.page))
        canvas.restoreState()

    def invariant_canvas(*args, **kwargs):
        kwargs["invariant"] = 1
        return Canvas(*args, **kwargs)

    doc.build(story, onFirstPage=footer, onLaterPages=footer, canvasmaker=invariant_canvas)
    return buffer.getvalue()


class Command(BaseCommand):
    help = "Load original demo data once; later runs preserve existing data and passwords."

    def handle(self, *args, **options):
        data_path = Path(settings.BASE_DIR) / "data" / "demo.json"
        data = json.loads(data_path.read_text(encoding="utf-8"))
        saved_files = []
        try:
            with transaction.atomic():
                # Serialize simultaneous startup commands without a permanent database lock.
                if connection.vendor == "postgresql":
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT pg_advisory_xact_lock(%s)", [184721906])
                if DemoState.objects.filter(key="initial-v1").exists():
                    self.stdout.write("Demo data already initialized; existing data preserved.")
                    return
                if Organization.objects.exists() or User.objects.exists():
                    raise CommandError("Database contains user data without the demo marker. "
                                       "Initialization stopped to preserve existing records.")
                password = os.environ.get("DEMO_PASSWORD", "LearnTogether2026!")
                User.objects.create_superuser(username="superadmin", email="superadmin@example.test",
                                              password=password, first_name="Platform", last_name="Administrator")
                courses = {}
                for org_data in data["organizations"]:
                    organization = Organization.objects.create(name=org_data["name"], slug=org_data["slug"])
                    for user_data in org_data["users"]:
                        username = f"{organization.slug}.{user_data['suffix']}"
                        User.objects.create_user(username=username, email=f"{username}@example.test",
                                                 password=password, organization=organization,
                                                 role=user_data["role"], first_name=user_data["first_name"],
                                                 last_name=user_data["last_name"])
                    instructor = User.objects.get(username=f"{organization.slug}.instructor")
                    for course_data in org_data["courses"]:
                        course = Course.objects.create(organization=organization, instructor=instructor,
                                                       title=course_data["title"], description=course_data["description"],
                                                       capacity=course_data["capacity"], status="PUBLISHED")
                        courses[course_data["key"]] = course
                        for position, lesson in enumerate(course_data["lessons"], 1):
                            Material.objects.create(course=course, title=lesson["title"], body=lesson["body"],
                                                    kind="TEXT", position=position)
                        material = Material(course=course, title=f"{course_data['title']} - Study Notes",
                                            kind="PDF", position=3,
                                            body="Download the course handout for a concise review and practical exercises.")
                        material.pdf_file.save(f"{course_data['key']}-handout.pdf",
                                               ContentFile(build_handout(course_data, organization.name)), save=False)
                        saved_files.append((material.pdf_file.storage, material.pdf_file.name))
                        material.save()
                for org_data in data["organizations"]:
                    for course_data in org_data["courses"]:
                        courses[course_data["key"]].prerequisites.set(
                            [courses[key] for key in course_data["prerequisites"]])
                now = timezone.now()
                for enrollment in data["enrollments"]:
                    Enrollment.objects.create(course=courses[enrollment["course"]],
                                              student=User.objects.get(username=enrollment["student"]),
                                              status=enrollment["status"], queue_entered_at=now,
                                              completed_at=now if enrollment["status"] == "COMPLETED" else None)
                DemoState.objects.create(key="initial-v1")
        except Exception:
            # File storage does not participate in database transactions.
            for storage, name in saved_files:
                storage.delete(name)
            raise
        self.stdout.write(self.style.SUCCESS("Created 2 organizations, 11 accounts, 6 courses and 18 materials."))
