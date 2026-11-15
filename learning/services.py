from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .authorization import audit
from .models import Course, Enrollment, User


def eligible(student, course):
    if (not student.is_active or student.role != User.Role.STUDENT
            or student.organization_id != course.organization_id):
        return False
    required = set(course.prerequisites.values_list('pk', flat=True))
    completed = set(Enrollment.objects.filter(student=student, status=Enrollment.Status.COMPLETED,
                                               course_id__in=required).values_list('course_id', flat=True))
    return required <= completed


def promote_waitlist(course, actor):
    """Caller MUST hold the course row lock in an atomic transaction."""
    if course.status != Course.Status.PUBLISHED:
        return
    free = course.capacity - course.enrollments.filter(status=Enrollment.Status.ENROLLED).count()
    if free <= 0:
        return
    waiting = course.enrollments.filter(status=Enrollment.Status.WAITLISTED).select_related('student').order_by('queue_entered_at', 'pk')
    for enrollment in waiting:
        if free <= 0:
            break
        if not eligible(enrollment.student, course):
            continue
        enrollment.status = Enrollment.Status.ENROLLED
        enrollment.save(update_fields=['status', 'updated_at'])
        audit(actor, 'waitlist_promoted', course=course, resource_type='enrollment', resource_id=enrollment.pk)
        free -= 1


@transaction.atomic
def enroll_student(student, course_id):
    # Serialize every occupancy change on the same course, across all web workers.
    course = Course.objects.select_for_update().get(pk=course_id)
    student = User.objects.get(pk=student.pk)
    if course.status != Course.Status.PUBLISHED:
        raise ValidationError('This course is not accepting enrollments.')
    if not eligible(student, course):
        raise ValidationError('Complete the required courses before enrolling.')
    current = Enrollment.objects.filter(course=course, student=student).first()
    if current and current.status != Enrollment.Status.CANCELLED:
        return current, False
    # Existing eligible waiters have priority over a newly arriving request.
    promote_waitlist(course, student)
    occupied = course.enrollments.filter(status=Enrollment.Status.ENROLLED).count()
    status = Enrollment.Status.ENROLLED if occupied < course.capacity else Enrollment.Status.WAITLISTED
    if current:
        current.status = status
        current.queue_entered_at = timezone.now()
        current.completed_at = None
        current.save(update_fields=['status', 'queue_entered_at', 'completed_at', 'updated_at'])
    else:
        current = Enrollment.objects.create(course=course, student=student, status=status)
    audit(student, 'enrollment_created', course=course, resource_type='enrollment', resource_id=current.pk, reason=status)
    return current, True


@transaction.atomic
def withdraw_student(student, course_id):
    course = Course.objects.select_for_update().get(pk=course_id)
    student = User.objects.get(pk=student.pk)
    if not student.is_active or student.role != User.Role.STUDENT or student.organization_id != course.organization_id:
        raise ValidationError('Your permissions changed. Please refresh and try again.')
    current = Enrollment.objects.filter(course=course, student=student).first()
    if not current or current.status not in [Enrollment.Status.ENROLLED, Enrollment.Status.WAITLISTED]:
        raise ValidationError('There is no active enrollment or waitlist entry to withdraw.')
    current.status = Enrollment.Status.CANCELLED
    current.save(update_fields=['status', 'updated_at'])
    audit(student, 'enrollment_cancelled', course=course, resource_type='enrollment', resource_id=current.pk)
    promote_waitlist(course, student)


def check_manager(actor, course):
    fresh = User.objects.get(pk=actor.pk)
    if (not fresh.is_active or fresh.organization_id != course.organization_id
            or not (fresh.role == User.Role.ADMIN or
                    (fresh.role == User.Role.INSTRUCTOR and course.instructor_id == fresh.pk))):
        raise ValidationError('Your permissions changed. Please refresh and try again.')


@transaction.atomic
def complete_enrollment(actor, enrollment_id):
    course_id = Enrollment.objects.values_list('course_id', flat=True).get(pk=enrollment_id)
    course = Course.objects.select_for_update().get(pk=course_id)
    check_manager(actor, course)
    enrollment = Enrollment.objects.get(pk=enrollment_id)
    if enrollment.status != Enrollment.Status.ENROLLED:
        raise ValidationError('Only an active enrollment can be completed.')
    enrollment.status = Enrollment.Status.COMPLETED
    enrollment.completed_at = timezone.now()
    enrollment.save(update_fields=['status', 'completed_at', 'updated_at'])
    audit(actor, 'enrollment_completed', course=course, resource_type='enrollment', resource_id=enrollment.pk)
    promote_waitlist(course, actor)


@transaction.atomic
def archive_course(actor, course_id):
    course = Course.objects.select_for_update().get(pk=course_id)
    check_manager(actor, course)
    course.status = Course.Status.ARCHIVED
    course.save(update_fields=['status', 'updated_at'])
    course.enrollments.filter(status=Enrollment.Status.WAITLISTED).update(
        status=Enrollment.Status.CANCELLED, updated_at=timezone.now())
    audit(actor, 'course_archived', course=course)


def validate_prerequisites(course, prerequisites):
    ids = {item.pk for item in prerequisites}
    if any(item.organization_id != course.organization_id for item in prerequisites):
        raise ValidationError('Prerequisites must belong to the same organization.')
    if not course.pk:
        return
    if course.pk in ids:
        raise ValidationError('A course cannot require itself.')
    seen, pending = set(), list(ids)
    while pending:
        item = pending.pop()
        if item == course.pk:
            raise ValidationError('These prerequisites would create a circular dependency.')
        if item not in seen:
            seen.add(item)
            pending.extend(Course.objects.get(pk=item).prerequisites.values_list('pk', flat=True))
