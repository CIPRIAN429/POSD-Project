from pathlib import Path
from uuid import uuid4

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class Organization(models.Model):
    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = 'STUDENT', 'Student'
        INSTRUCTOR = 'INSTRUCTOR', 'Instructor'
        ADMIN = 'ADMIN', 'Organization Administrator'

    organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.PROTECT)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)

    def clean(self):
        super().clean()
        if not self.is_superuser and not self.organization_id:
            raise ValidationError({'organization': 'An organization is required.'})

    def __str__(self):
        return self.get_full_name() or self.username


class Course(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        PUBLISHED = 'PUBLISHED', 'Published'
        ARCHIVED = 'ARCHIVED', 'Archived'

    organization = models.ForeignKey(Organization, on_delete=models.PROTECT)
    instructor = models.ForeignKey(User, on_delete=models.PROTECT, related_name='teaching_courses')
    title = models.CharField(max_length=180)
    description = models.TextField()
    capacity = models.PositiveIntegerField(default=20, validators=[MinValueValidator(1)])
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    prerequisites = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='unlocks')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title', 'pk']
        constraints = [models.CheckConstraint(condition=models.Q(capacity__gte=1), name='positive_capacity')]

    def clean(self):
        if self.instructor_id:
            if self.instructor.organization_id != self.organization_id or self.instructor.role != User.Role.INSTRUCTOR:
                raise ValidationError({'instructor': 'Choose an instructor from this organization.'})

    def __str__(self):
        return self.title


def private_upload(instance, filename):
    return f'private/{instance.course.organization_id}/{uuid4().hex}{Path(filename).suffix.lower()}'


class Material(models.Model):
    class Kind(models.TextChoices):
        TEXT = 'TEXT', 'Text lesson'
        PDF = 'PDF', 'PDF handout'

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='materials')
    title = models.CharField(max_length=180)
    body = models.TextField(blank=True)
    kind = models.CharField(max_length=10, choices=Kind.choices, default=Kind.TEXT)
    pdf_file = models.FileField(upload_to=private_upload, blank=True)
    position = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['position', 'pk']

    def __str__(self):
        return self.title


class Enrollment(models.Model):
    class Status(models.TextChoices):
        ENROLLED = 'ENROLLED', 'Enrolled'
        WAITLISTED = 'WAITLISTED', 'Waitlisted'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    student = models.ForeignKey(User, on_delete=models.PROTECT, related_name='enrollments')
    status = models.CharField(max_length=20, choices=Status.choices)
    queue_entered_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['course', 'student'], name='unique_course_student')]
        ordering = ['queue_entered_at', 'pk']
        indexes = [models.Index(fields=['course', 'status', 'queue_entered_at'])]


class AuditEvent(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    actor_name = models.CharField(max_length=150)
    action = models.CharField(max_length=80)
    resource_type = models.CharField(max_length=40, default='organization')
    resource_id = models.PositiveBigIntegerField(null=True)
    allowed = models.BooleanField()
    reason = models.CharField(max_length=200)
    event_type = models.CharField(max_length=30, default='ACCESS')
    policy_version = models.CharField(max_length=40, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-pk']


class DemoState(models.Model):
    key = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
