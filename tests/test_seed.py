import pytest
from django.core.management import call_command
from learning.models import Course, DemoState, Enrollment, Material, Organization, User

pytestmark = pytest.mark.django_db


def test_seed_is_complete_and_preserves_edits_and_passwords():
    call_command('seed_demo')
    assert Organization.objects.count() == 2
    assert User.objects.count() == 11
    assert Course.objects.count() == 6
    assert Material.objects.count() == 18
    assert Material.objects.filter(kind='PDF').count() == 6
    user = User.objects.get(username='atlas.student1')
    user.set_password('AChangedPassword2026!')
    user.save()
    course = Course.objects.first()
    course.title = 'Our team changed this title'
    course.save()
    counts = [Enrollment.objects.count(), Material.objects.count()]
    pdfs = list(Material.objects.filter(kind='PDF').values_list('pdf_file', flat=True))
    call_command('seed_demo')
    user.refresh_from_db()
    course.refresh_from_db()
    assert user.check_password('AChangedPassword2026!')
    assert course.title == 'Our team changed this title'
    assert [Enrollment.objects.count(), Material.objects.count()] == counts
    assert list(Material.objects.filter(kind='PDF').values_list('pdf_file', flat=True)) == pdfs
    assert DemoState.objects.count() == 1
