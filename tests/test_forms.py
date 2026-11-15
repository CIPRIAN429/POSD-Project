import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from learning.forms import CourseForm, MaterialForm, OrganizationUserForm
from learning.models import Course, Enrollment, User

pytestmark = pytest.mark.django_db


def course_data(course, **changes):
    data = {'title': course.title, 'description': course.description,
            'capacity': course.capacity, 'status': course.status,
            'instructor': course.instructor_id, 'prerequisites': []}
    data.update(changes)
    return data


def user_data(user, **changes):
    data = {'username': user.username, 'first_name': user.first_name,
            'last_name': user.last_name, 'email': user.email, 'role': user.role,
            'is_active': user.is_active, 'password': ''}
    data.update(changes)
    return data


def test_course_form_rejects_cross_tenant_instructor_and_prerequisite(school):
    form = CourseForm(course_data(school.intro, instructor=school.beta_instructor.pk,
                                 prerequisites=[school.foreign.pk]),
                      actor=school.admin, instance=school.intro)
    assert not form.is_valid()
    assert 'instructor' in form.errors and 'prerequisites' in form.errors


def test_course_form_rejects_cycles_and_self_reference(school):
    form = CourseForm(course_data(school.intro, prerequisites=[school.advanced.pk]),
                      actor=school.admin, instance=school.intro)
    assert not form.is_valid()
    assert 'circular' in str(form.errors).lower()
    form = CourseForm(course_data(school.intro, prerequisites=[school.intro.pk]),
                      actor=school.admin, instance=school.intro)
    assert not form.is_valid()


def test_capacity_and_draft_cannot_invalidate_existing_participation(school):
    for student in school.students[:2]:
        Enrollment.objects.create(course=school.intro, student=student, status=Enrollment.Status.ENROLLED)
    form = CourseForm(course_data(school.intro, capacity=1, status=Course.Status.DRAFT),
                      actor=school.admin, instance=school.intro)
    assert not form.is_valid()
    assert 'capacity' in form.errors and 'status' in form.errors


def test_instructor_form_ignores_forged_owner_and_organization(school):
    form = CourseForm(course_data(school.intro, instructor=school.beta_instructor.pk,
                                 organization=school.beta.pk),
                      actor=school.instructor, instance=school.intro)
    assert form.is_valid(), form.errors
    course = form.save()
    assert course.instructor_id == school.instructor.pk
    assert course.organization_id == school.alpha.pk


def test_blank_password_edit_keeps_hash_and_password_change_hashes(school):
    original_hash = school.students[0].password
    form = OrganizationUserForm(user_data(school.students[0], first_name='Updated'),
                                actor=school.admin, instance=school.students[0])
    assert form.is_valid(), form.errors
    saved = form.save()
    assert saved.password == original_hash and saved.check_password('StudyTogether2026!')
    form = OrganizationUserForm(user_data(saved, password='NewStrongPass2026!'),
                                actor=school.admin, instance=saved)
    assert form.is_valid(), form.errors
    changed = form.save()
    assert changed.password != 'NewStrongPass2026!' and changed.check_password('NewStrongPass2026!')


def test_cannot_remove_own_admin_role_or_demote_assigned_instructor(school):
    form = OrganizationUserForm(user_data(school.admin, role=User.Role.STUDENT, is_active=False),
                                actor=school.admin, instance=school.admin)
    assert not form.is_valid()
    form = OrganizationUserForm(user_data(school.instructor, role=User.Role.STUDENT),
                                actor=school.admin, instance=school.instructor)
    assert not form.is_valid() and 'role' in form.errors


@pytest.mark.parametrize('name,content', [('script.html', b'<script>bad()</script>'),
                                          ('fake.pdf', b'not a PDF')])
def test_pdf_upload_validates_extension_and_signature(name, content):
    form = MaterialForm({'title': 'Handout', 'kind': 'PDF', 'position': 1},
                        {'pdf_file': SimpleUploadedFile(name, content, content_type='application/pdf')})
    assert not form.is_valid() and 'pdf_file' in form.errors
