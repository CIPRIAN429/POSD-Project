import httpx
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from learning.models import AuditEvent, Course, Enrollment, User

pytestmark = pytest.mark.django_db


def login(client, user):
    client.force_login(user)


@pytest.mark.parametrize('name', ['dashboard', 'catalog', 'my_courses'])
def test_login_required(client, name):
    assert client.get(reverse(f'learning:{name}')).status_code == 302


@pytest.mark.parametrize('role', ['students', 'instructor', 'admin'])
def test_dashboard_and_catalog_render_for_every_role(client, school, role):
    user = school.students[0] if role == 'students' else getattr(school, role)
    login(client, user)
    for route in ['dashboard', 'catalog']:
        response = client.get(reverse(f'learning:{route}'))
        assert response.status_code == 200
        assert b'Beta Private Course' not in response.content


@pytest.mark.parametrize('route', ['course_detail', 'course_edit', 'participants'])
def test_admin_cannot_access_foreign_course(client, school, route):
    login(client, school.admin)
    assert client.get(reverse(f'learning:{route}', args=[school.foreign.pk])).status_code == 404
    assert AuditEvent.objects.filter(organization=school.alpha, reason='TENANT_MISMATCH', allowed=False).exists()


def test_instructor_cannot_manage_other_instructors_course(client, school):
    login(client, school.other_instructor)
    for route in ['course_edit', 'participants']:
        assert client.get(reverse(f'learning:{route}', args=[school.intro.pk])).status_code == 403


@pytest.mark.parametrize('status,allowed', [('ENROLLED', True), ('COMPLETED', True), ('WAITLISTED', False), ('CANCELLED', False)])
def test_material_and_download_follow_enrollment(client, school, status, allowed):
    user = school.students[0]
    Enrollment.objects.create(student=user, course=school.intro, status=status)
    login(client, user)
    text = client.get(reverse('learning:material_detail', args=[school.lesson.pk]))
    pdf = client.get(reverse('learning:material_download', args=[school.pdf.pk]))
    assert text.status_code == (200 if allowed else 403)
    assert pdf.status_code == (200 if allowed else 403)
    if allowed:
        assert pdf['Content-Type'] == 'application/pdf'
        assert pdf['Cache-Control'] == 'private, no-store'
        assert b''.join(pdf.streaming_content).startswith(b'%PDF-')
    else:
        assert b'Private learning content.' not in text.content


def test_no_public_media_route_and_foreign_pdf_denied(client, school):
    login(client, school.beta_student)
    assert client.get(reverse('learning:material_download', args=[school.pdf.pk])).status_code == 404
    assert client.get('/media/' + school.pdf.pdf_file.name).status_code == 404
    assert client.get('/private_media/' + school.pdf.pdf_file.name).status_code == 404


def test_draft_hidden_archived_participant_can_read(client, school):
    user = school.students[0]
    login(client, user)
    school.intro.status = Course.Status.DRAFT
    school.intro.save()
    assert client.get(reverse('learning:course_detail', args=[school.intro.pk])).status_code == 403
    Enrollment.objects.create(student=user, course=school.intro, status='COMPLETED')
    school.intro.status = Course.Status.ARCHIVED
    school.intro.save()
    assert client.get(reverse('learning:course_detail', args=[school.intro.pk])).status_code == 200
    assert client.get(reverse('learning:material_detail', args=[school.lesson.pk])).status_code == 200
    assert client.post(reverse('learning:enroll', args=[school.intro.pk])).status_code == 403


def test_role_change_and_deactivation_apply_next_request(client, school):
    login(client, school.admin)
    assert client.get(reverse('learning:user_list')).status_code == 200
    User.objects.filter(pk=school.admin.pk).update(role='STUDENT')
    assert client.get(reverse('learning:user_list')).status_code == 403
    User.objects.filter(pk=school.admin.pk).update(is_active=False)
    assert client.get(reverse('learning:dashboard')).status_code == 302


def test_user_management_and_audit_are_admin_only(client, school):
    login(client, school.students[0])
    for route in ['user_list', 'policies', 'audit', 'manage_courses']:
        assert client.get(reverse(f'learning:{route}')).status_code == 403
    login(client, school.admin)
    for route in ['user_list', 'policies', 'audit', 'manage_courses']:
        assert client.get(reverse(f'learning:{route}')).status_code == 200
    assert client.get(reverse('learning:user_edit', args=[school.beta_admin.pk])).status_code == 404


def test_outage_fails_closed_and_no_enrollment_created(client, school, monkeypatch):
    login(client, school.students[0])
    def fail(*args, **kwargs):
        raise httpx.ConnectError('offline')
    monkeypatch.setattr('learning.authorization.httpx.post', fail)
    response = client.post(reverse('learning:enroll', args=[school.intro.pk]))
    assert response.status_code == 503
    assert not Enrollment.objects.filter(student=school.students[0]).exists()
    assert AuditEvent.objects.filter(reason='POLICY_UNAVAILABLE', allowed=False).exists()


def test_malformed_policy_response_fails_closed(client, school, monkeypatch):
    login(client, school.students[0])
    def malformed(*args, **kwargs):
        return httpx.Response(200, json={'allowed': 'true'}, request=httpx.Request('POST', 'http://policy/authorize'))
    monkeypatch.setattr('learning.authorization.httpx.post', malformed)
    assert client.post(reverse('learning:enroll', args=[school.intro.pk])).status_code == 503
    assert not Enrollment.objects.filter(student=school.students[0]).exists()


def test_enrollment_endpoint_checks_prerequisite_then_allows(client, school):
    login(client, school.students[0])
    response = client.post(reverse('learning:enroll', args=[school.advanced.pk]), follow=True)
    assert response.status_code == 200
    assert b'Complete the required courses' in response.content
    assert not Enrollment.objects.filter(course=school.advanced).exists()
    Enrollment.objects.create(student=school.students[0], course=school.intro, status='COMPLETED')
    assert client.post(reverse('learning:enroll', args=[school.advanced.pk])).status_code == 302
    assert Enrollment.objects.get(course=school.advanced).status == 'ENROLLED'


def test_mutations_require_post_and_csrf(school):
    from django.test import Client
    client = Client(enforce_csrf_checks=True)
    client.force_login(school.students[0])
    assert client.get(reverse('learning:enroll', args=[school.intro.pk])).status_code == 405
    assert client.post(reverse('learning:enroll', args=[school.intro.pk])).status_code == 403
    assert not Enrollment.objects.exists()


def test_capacity_increase_promotes_waitlist_via_edit(client, school):
    for user, status in zip(school.students[:2], ['ENROLLED', 'WAITLISTED']):
        Enrollment.objects.create(student=user, course=school.intro, status=status)
    login(client, school.admin)
    response = client.post(reverse('learning:course_edit', args=[school.intro.pk]), {
        'title': school.intro.title, 'description': school.intro.description,
        'instructor': school.instructor.pk, 'capacity': 2, 'status': 'PUBLISHED', 'prerequisites': [],
    })
    assert response.status_code == 302
    assert school.intro.enrollments.filter(status='ENROLLED').count() == 2


def test_audit_listing_is_tenant_scoped(client, school):
    AuditEvent.objects.create(organization=school.beta, actor=school.beta_admin,
                              actor_name='FOREIGN-SECRET-ACTOR', action='foreign', allowed=True, reason='OK')
    login(client, school.admin)
    response = client.get(reverse('learning:audit'))
    assert response.status_code == 200
    assert b'FOREIGN-SECRET-ACTOR' not in response.content


def test_all_management_pages_and_material_delete_render(client, school):
    login(client, school.instructor)
    for name, args in [('course_create', []), ('course_edit', [school.intro.pk]),
                       ('material_create', [school.intro.pk]), ('material_edit', [school.lesson.pk]),
                       ('participants', [school.intro.pk])]:
        assert client.get(reverse(f'learning:{name}', args=args)).status_code == 200
    response = client.post(reverse('learning:material_delete', args=[school.lesson.pk]))
    assert response.status_code == 302
    assert not school.intro.materials.filter(pk=school.lesson.pk).exists()
