from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

import pytest
from django.core.exceptions import ValidationError
from django.db import close_old_connections, connection, transaction
from django.utils import timezone

from learning.models import Course, Enrollment, User
from learning.services import (archive_course, complete_enrollment, enroll_student,
                               promote_waitlist, withdraw_student)

pytestmark = pytest.mark.django_db


def test_prerequisite_blocks_until_completed(school):
    student = school.students[0]
    with pytest.raises(ValidationError):
        enroll_student(student, school.advanced.pk)
    assert not Enrollment.objects.filter(course=school.advanced).exists()
    initial, _ = enroll_student(student, school.intro.pk)
    complete_enrollment(school.instructor, initial.pk)
    advanced, created = enroll_student(student, school.advanced.pk)
    assert created and advanced.status == Enrollment.Status.ENROLLED


def test_retry_does_not_duplicate_enrollment_or_move_waiter(school):
    enroll_student(school.students[0], school.intro.pk)
    waiting, _ = enroll_student(school.students[1], school.intro.pk)
    repeated, created = enroll_student(school.students[1], school.intro.pk)
    assert not created
    assert repeated.pk == waiting.pk
    assert repeated.queue_entered_at == waiting.queue_entered_at
    assert Enrollment.objects.filter(course=school.intro).count() == 2


def test_waitlist_promotes_fifo_and_rejoining_goes_to_back(school):
    first, _ = enroll_student(school.students[0], school.intro.pk)
    second, _ = enroll_student(school.students[1], school.intro.pk)
    third, _ = enroll_student(school.students[2], school.intro.pk)
    withdraw_student(school.students[1], school.intro.pk)
    rejoined, created = enroll_student(school.students[1], school.intro.pk)
    assert created and rejoined.pk == second.pk
    assert rejoined.queue_entered_at > third.queue_entered_at
    withdraw_student(school.students[0], school.intro.pk)
    for entry in [first, third, rejoined]:
        entry.refresh_from_db()
    assert first.status == Enrollment.Status.CANCELLED
    assert third.status == Enrollment.Status.ENROLLED
    assert rejoined.status == Enrollment.Status.WAITLISTED


def test_ineligible_waiter_is_skipped_then_restored(school):
    enroll_student(school.students[0], school.intro.pk)
    second, _ = enroll_student(school.students[1], school.intro.pk)
    third, _ = enroll_student(school.students[2], school.intro.pk)
    User.objects.filter(pk=school.students[1].pk).update(is_active=False)
    withdraw_student(school.students[0], school.intro.pk)
    second.refresh_from_db()
    third.refresh_from_db()
    assert second.status == Enrollment.Status.WAITLISTED
    assert third.status == Enrollment.Status.ENROLLED
    User.objects.filter(pk=school.students[1].pk).update(is_active=True)
    withdraw_student(school.students[2], school.intro.pk)
    second.refresh_from_db()
    assert second.status == Enrollment.Status.ENROLLED


def test_promotion_rechecks_changed_prerequisites(school):
    enroll_student(school.students[0], school.intro.pk)
    second, _ = enroll_student(school.students[1], school.intro.pk)
    prerequisite = Course.objects.create(title='Safety Basics', description='Required preparation',
                                        organization=school.alpha, instructor=school.instructor,
                                        status=Course.Status.PUBLISHED)
    school.intro.prerequisites.add(prerequisite)
    withdraw_student(school.students[0], school.intro.pk)
    second.refresh_from_db()
    assert second.status == Enrollment.Status.WAITLISTED
    Enrollment.objects.create(course=prerequisite, student=school.students[1],
                              status=Enrollment.Status.COMPLETED, completed_at=timezone.now())
    with transaction.atomic():
        course = Course.objects.select_for_update().get(pk=school.intro.pk)
        promote_waitlist(course, school.admin)
    second.refresh_from_db()
    assert second.status == Enrollment.Status.ENROLLED


def test_existing_eligible_waiters_take_priority_over_new_arrival(school):
    older = Enrollment.objects.create(course=school.intro, student=school.students[0],
                                      status=Enrollment.Status.WAITLISTED,
                                      queue_entered_at=timezone.now() - timedelta(days=1))
    newcomer, _ = enroll_student(school.students[1], school.intro.pk)
    older.refresh_from_db()
    assert older.status == Enrollment.Status.ENROLLED
    assert newcomer.status == Enrollment.Status.WAITLISTED


def test_completion_frees_seat_and_keeps_history(school):
    active, _ = enroll_student(school.students[0], school.intro.pk)
    waiting, _ = enroll_student(school.students[1], school.intro.pk)
    complete_enrollment(school.instructor, active.pk)
    active.refresh_from_db()
    waiting.refresh_from_db()
    assert active.status == Enrollment.Status.COMPLETED and active.completed_at is not None
    assert waiting.status == Enrollment.Status.ENROLLED
    repeated, created = enroll_student(school.students[0], school.intro.pk)
    assert not created and repeated.status == Enrollment.Status.COMPLETED


def test_archive_cancels_waitlist_but_preserves_enrolled_and_completed(school):
    active, _ = enroll_student(school.students[0], school.intro.pk)
    waiting, _ = enroll_student(school.students[1], school.intro.pk)
    completed = Enrollment.objects.create(course=school.intro, student=school.students[2],
                                         status=Enrollment.Status.COMPLETED)
    archive_course(school.admin, school.intro.pk)
    for record in [active, waiting, completed, school.intro]:
        record.refresh_from_db()
    assert school.intro.status == Course.Status.ARCHIVED
    assert active.status == Enrollment.Status.ENROLLED
    assert completed.status == Enrollment.Status.COMPLETED
    assert waiting.status == Enrollment.Status.CANCELLED
    with pytest.raises(ValidationError):
        enroll_student(school.students[3], school.intro.pk)


def test_domain_services_recheck_student_and_manager_permissions(school):
    with pytest.raises(ValidationError):
        enroll_student(school.beta_student, school.intro.pk)
    with pytest.raises(ValidationError):
        enroll_student(school.instructor, school.intro.pk)
    active, _ = enroll_student(school.students[0], school.intro.pk)
    with pytest.raises(ValidationError):
        complete_enrollment(school.other_instructor, active.pk)
    User.objects.filter(pk=school.instructor.pk).update(is_active=False)
    with pytest.raises(ValidationError):
        complete_enrollment(school.instructor, active.pk)
    active.refresh_from_db()
    assert active.status == Enrollment.Status.ENROLLED


@pytest.mark.django_db(transaction=True)
def test_two_concurrent_requests_for_last_seat(school):
    assert connection.vendor == 'postgresql', 'Concurrency must be verified on PostgreSQL.'
    barrier = Barrier(2)

    def enroll_on_separate_connection(student_id):
        close_old_connections()
        try:
            student = User.objects.get(pk=student_id)
            barrier.wait(timeout=10)
            enrollment, _ = enroll_student(student, school.intro.pk)
            return enrollment.status
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(enroll_on_separate_connection,
                                    [student.pk for student in school.students[:2]]))
    assert sorted(results) == [Enrollment.Status.ENROLLED, Enrollment.Status.WAITLISTED]
    assert Enrollment.objects.filter(course=school.intro).count() == 2
