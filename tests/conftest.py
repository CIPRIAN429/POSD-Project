"""Normal authorization calls use the running policy service, not a policy mock."""
from types import SimpleNamespace

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from learning.models import Course, Material, Organization, User


@pytest.fixture(autouse=True)
def isolated_test_settings(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / 'private_media'
    settings.PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
    settings.STORAGES = {
        'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
        'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
    }


@pytest.fixture
def school(db):
    alpha = Organization.objects.create(name='Alpha University', slug='alpha')
    beta = Organization.objects.create(name='Beta Academy', slug='beta')

    def user(name, role, organization=alpha):
        return User.objects.create_user(username=name, password='StudyTogether2026!',
                                        organization=organization, role=role)

    admin = user('alpha.admin', User.Role.ADMIN)
    instructor = user('alpha.instructor', User.Role.INSTRUCTOR)
    other_instructor = user('alpha.other', User.Role.INSTRUCTOR)
    students = [user(f'alpha.student{i}', User.Role.STUDENT) for i in range(1, 5)]
    beta_admin = user('beta.admin', User.Role.ADMIN, beta)
    beta_instructor = user('beta.instructor', User.Role.INSTRUCTOR, beta)
    beta_student = user('beta.student', User.Role.STUDENT, beta)

    def course(title, organization=alpha, owner=instructor):
        return Course.objects.create(title=title, description=f'{title} course description.',
                                     organization=organization, instructor=owner,
                                     capacity=1, status=Course.Status.PUBLISHED)

    intro = course('Alpha Introduction')
    advanced = course('Alpha Advanced')
    advanced.prerequisites.add(intro)
    foreign = course('Beta Private Course', beta, beta_instructor)
    lesson = Material.objects.create(course=intro, title='Protected lesson', body='Private learning content.')
    pdf = Material.objects.create(course=intro, title='Protected handout', kind=Material.Kind.PDF,
                                  pdf_file=SimpleUploadedFile('notes.pdf', b'%PDF-1.4\n%%EOF',
                                                              content_type='application/pdf'))
    return SimpleNamespace(alpha=alpha, beta=beta, admin=admin, instructor=instructor,
                           other_instructor=other_instructor, students=students,
                           beta_admin=beta_admin, beta_instructor=beta_instructor,
                           beta_student=beta_student, intro=intro, advanced=advanced,
                           foreign=foreign, lesson=lesson, pdf=pdf)
