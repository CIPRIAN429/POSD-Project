import logging
from functools import wraps
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db import connection, transaction
from django.db.models import Count, Q
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .authorization import authorize, audit, policy_catalog
from .forms import CourseForm, MaterialForm, OrganizationUserForm
from .guide import load_guide
from .models import AuditEvent, Course, Enrollment, Material, Organization, User
from .services import (archive_course, check_manager, complete_enrollment, enroll_student,
                       promote_waitlist, withdraw_student)


def user_guide(request):
    return render(request, 'learning/guide.html', {'guide': load_guide()})


def guide_download(request):
    return FileResponse((settings.BASE_DIR / 'docs' / 'user-guide.md').open('rb'),
                        as_attachment=True, filename='access-granted-user-guide.md',
                        content_type='text/markdown; charset=utf-8')


def page(request, queryset, size=12):
    return Paginator(queryset, size).get_page(request.GET.get('page'))


def courses_for(user):
    return Course.objects.filter(organization_id=user.organization_id).select_related(
        'organization', 'instructor').annotate(
        active_count=Count('enrollments', filter=Q(enrollments__status='ENROLLED'))).order_by('title', 'pk')


def visible_courses(user):
    courses = courses_for(user)
    if user.role == 'STUDENT':
        return courses.filter(status='PUBLISHED')
    if user.role == 'INSTRUCTOR':
        return courses.filter(Q(status='PUBLISHED') | Q(instructor=user))
    return courses


def get_course(pk):
    return get_object_or_404(Course.objects.select_related('organization', 'instructor'), pk=pk)


def own_enrollment(user, course):
    return Enrollment.objects.filter(student=user, course=course).first()


def show_validation(request, exc):
    for message in exc.messages:
        messages.error(request, message)


def organization_account(view):
    @login_required
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.organization_id:
            if request.user.is_superuser:
                return redirect('admin:index')
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return wrapped


@organization_account
def dashboard(request):
    user = request.user
    authorize(user, 'dashboard')
    scoped_courses = courses_for(user)
    if user.role == 'INSTRUCTOR':
        scoped_courses = scoped_courses.filter(instructor=user)
    enrollments = Enrollment.objects.filter(course__in=scoped_courses)
    if user.role == 'STUDENT':
        enrollments = enrollments.filter(student=user)
    stats = {'courses': visible_courses(user).count(),
             'enrolled': enrollments.filter(status='ENROLLED').count(),
             'completed': enrollments.filter(status='COMPLETED').count(),
             'waiting': enrollments.filter(status='WAITLISTED').count()}
    return render(request, 'learning/dashboard.html', {
        'stats': stats, 'featured_courses': visible_courses(user)[:4],
        'recent_enrollments': enrollments.select_related('course', 'student').order_by('-updated_at')[:5],
    })


@organization_account
def catalog(request):
    authorize(request.user, 'catalog')
    query = request.GET.get('q', '').strip()
    courses = visible_courses(request.user)
    if query:
        courses = courses.filter(title__icontains=query)
    return render(request, 'learning/catalog.html', {'page_obj': page(request, courses), 'query': query,
                                                     'page_title': 'Course catalog', 'management': False})


@organization_account
def manage_courses(request):
    authorize(request.user, 'course_create')
    courses = courses_for(request.user)
    if request.user.role == 'INSTRUCTOR':
        courses = courses.filter(instructor=request.user)
    query = request.GET.get('q', '').strip()
    if query:
        courses = courses.filter(title__icontains=query)
    return render(request, 'learning/catalog.html', {'page_obj': page(request, courses), 'query': query,
                                                     'page_title': 'Manage courses', 'management': True})


@organization_account
def course_detail(request, pk):
    course = get_course(pk)
    enrollment = own_enrollment(request.user, course)
    has_participation = bool(enrollment and enrollment.status in ['ENROLLED', 'COMPLETED'])
    authorize(request.user, 'course_view', course=course, enrollment=enrollment, has_participation=has_participation)
    can_manage = request.user.role == 'ADMIN' or (request.user.role == 'INSTRUCTOR' and course.instructor_id == request.user.pk)
    can_read = can_manage or (request.user.role == 'STUDENT' and has_participation)
    return render(request, 'learning/detail.html', {
        'course': course, 'enrollment': enrollment,
        'materials': course.materials.all() if can_read else Material.objects.none(),
        'material_count': course.materials.count(),
        'prerequisites': course.prerequisites.all(), 'can_manage': can_manage,
        'can_read_materials': can_read,
        'can_enroll': request.user.role == 'STUDENT' and course.status == 'PUBLISHED'
                      and (not enrollment or enrollment.status == 'CANCELLED'),
        'can_withdraw': request.user.role == 'STUDENT' and bool(enrollment and enrollment.status in ['ENROLLED', 'WAITLISTED']),
        'active_count': course.enrollments.filter(status='ENROLLED').count(),
        'waiting_count': course.enrollments.filter(status='WAITLISTED').count(),
    })


def render_form(request, form, title, cancel_url, subtitle='', submit_label='Save changes', **extra):
    return render(request, 'learning/form.html', {'form': form, 'title': title, 'subtitle': subtitle,
                                                'submit_label': submit_label, 'cancel_url': cancel_url, **extra})


@organization_account
def course_create(request):
    authorize(request.user, 'course_create')
    if request.method == 'POST':
        with transaction.atomic():
            Organization.objects.select_for_update().get(pk=request.user.organization_id)
            form = CourseForm(request.POST, actor=request.user)
            if form.is_valid():
                course = form.save()
                audit(request.user, 'course_created', course=course)
                messages.success(request, 'Course created.')
                return redirect('learning:course_detail', pk=course.pk)
    else:
        form = CourseForm(actor=request.user)
    return render_form(request, form, 'Create a course', reverse('learning:manage_courses'),
                       'Set the course details and publication status.', 'Create course')


@organization_account
def course_edit(request, pk):
    course = get_course(pk)
    authorize(request.user, 'course_manage', course=course)
    if course.status == 'ARCHIVED':
        messages.info(request, 'Archived courses are read-only.')
        return redirect('learning:course_detail', pk=pk)
    if request.method == 'POST':
        with transaction.atomic():
            # Serializing graph edits prevents concurrent prerequisite cycles.
            Organization.objects.select_for_update().get(pk=request.user.organization_id)
            course = Course.objects.select_for_update().get(pk=pk)
            check_manager(request.user, course)
            form = CourseForm(request.POST, instance=course, actor=request.user)
            if form.is_valid():
                course = form.save()
                promote_waitlist(course, request.user)
                audit(request.user, 'course_updated', course=course)
                messages.success(request, 'Course updated.')
                return redirect('learning:course_detail', pk=pk)
    else:
        form = CourseForm(instance=course, actor=request.user)
    return render_form(request, form, 'Edit course', reverse('learning:course_detail', args=[pk]))


@organization_account
@require_POST
def course_archive(request, pk):
    course = get_course(pk)
    authorize(request.user, 'course_manage', course=course)
    try:
        archive_course(request.user, pk)
        messages.success(request, 'Course archived. Waitlist entries have been cancelled.')
    except ValidationError as exc:
        show_validation(request, exc)
    return redirect('learning:course_detail', pk=pk)


@organization_account
@require_POST
def enroll(request, pk):
    course = get_course(pk)
    enrollment = own_enrollment(request.user, course)
    authorize(request.user, 'enroll', course=course, enrollment=enrollment)
    try:
        enrollment, created = enroll_student(request.user, pk)
        if not created:
            messages.info(request, 'You already have an enrollment for this course.')
        elif enrollment.status == 'ENROLLED':
            messages.success(request, 'You are enrolled. Your course materials are ready.')
        else:
            messages.success(request, 'You have joined the waitlist. You will be promoted when a place becomes available.')
    except ValidationError as exc:
        audit(request.user, 'enroll', course=course, allowed=False, reason='ELIGIBILITY_NOT_MET', event_type='WORKFLOW')
        show_validation(request, exc)
    return redirect('learning:course_detail', pk=pk)


@organization_account
@require_POST
def withdraw(request, pk):
    course = get_course(pk)
    enrollment = own_enrollment(request.user, course)
    authorize(request.user, 'withdraw', course=course, enrollment=enrollment)
    try:
        withdraw_student(request.user, pk)
        messages.success(request, 'You have withdrawn from the course.')
    except ValidationError as exc:
        show_validation(request, exc)
    return redirect('learning:course_detail', pk=pk)


@organization_account
def my_courses(request):
    authorize(request.user, 'my_courses')
    enrollments = request.user.enrollments.filter(course__organization=request.user.organization).select_related('course', 'course__instructor').order_by('-updated_at')
    return render(request, 'learning/my_courses.html', {'page_obj': page(request, enrollments)})


@organization_account
def participants(request, pk):
    course = get_course(pk)
    authorize(request.user, 'participants', course=course)
    enrollments = course.enrollments.select_related('student')
    counts = {label: enrollments.filter(status=status).count() for label, status in
              [('enrolled', 'ENROLLED'), ('waiting', 'WAITLISTED'), ('completed', 'COMPLETED'), ('cancelled', 'CANCELLED')]}
    return render(request, 'learning/participants.html', {'course': course, 'page_obj': page(request, enrollments, 20), 'counts': counts})


@organization_account
@require_POST
def complete(request, pk):
    enrollment = get_object_or_404(Enrollment.objects.select_related('course', 'course__instructor'), pk=pk)
    authorize(request.user, 'complete', course=enrollment.course, enrollment=enrollment)
    try:
        complete_enrollment(request.user, pk)
        messages.success(request, 'Course completion recorded. Any available place has been offered to the waitlist.')
    except ValidationError as exc:
        show_validation(request, exc)
    return redirect('learning:participants', pk=enrollment.course_id)


@organization_account
def material_detail(request, pk):
    material = get_object_or_404(Material.objects.select_related('course', 'course__instructor'), pk=pk)
    authorize(request.user, 'material_read', course=material.course, enrollment=own_enrollment(request.user, material.course))
    return render(request, 'learning/material_detail.html', {'material': material})


@organization_account
def material_download(request, pk):
    material = get_object_or_404(Material.objects.select_related('course', 'course__instructor'), pk=pk, kind='PDF')
    authorize(request.user, 'material_read', course=material.course, enrollment=own_enrollment(request.user, material.course))
    try:
        response = FileResponse(material.pdf_file.open('rb'), as_attachment=True,
                                filename=f'{material.title}.pdf', content_type='application/pdf')
    except (FileNotFoundError, ValueError):
        raise Http404('The file is not available.')
    response['Cache-Control'] = 'private, no-store'
    return response


@organization_account
def material_create(request, pk):
    course = get_course(pk)
    authorize(request.user, 'course_manage', course=course)
    if course.status == 'ARCHIVED':
        raise PermissionDenied('Archived courses are read-only.')
    form = MaterialForm(request.POST or None, request.FILES or None, instance=Material(course=course))
    if request.method == 'POST' and form.is_valid():
        material = form.save()
        audit(request.user, 'material_created', course=course, resource_type='material', resource_id=material.pk)
        messages.success(request, 'Material added.')
        return redirect('learning:course_detail', pk=pk)
    return render_form(request, form, 'Add course material', reverse('learning:course_detail', args=[pk]), submit_label='Add material')


@organization_account
def material_edit(request, pk):
    material = get_object_or_404(Material.objects.select_related('course'), pk=pk)
    authorize(request.user, 'course_manage', course=material.course)
    if material.course.status == 'ARCHIVED':
        raise PermissionDenied('Archived courses are read-only.')
    old_file = material.pdf_file.name
    form = MaterialForm(request.POST or None, request.FILES or None, instance=material)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            material = form.save()
            if old_file and old_file != material.pdf_file.name:
                transaction.on_commit(lambda: material.pdf_file.storage.delete(old_file))
            audit(request.user, 'material_updated', course=material.course, resource_type='material', resource_id=pk)
        messages.success(request, 'Material updated.')
        return redirect('learning:course_detail', pk=material.course_id)
    return render_form(request, form, 'Edit course material', reverse('learning:course_detail', args=[material.course_id]),
                       delete_url=reverse('learning:material_delete', args=[material.pk]))


@organization_account
@require_POST
def material_delete(request, pk):
    material = get_object_or_404(Material.objects.select_related('course'), pk=pk)
    authorize(request.user, 'course_manage', course=material.course)
    if material.course.status == 'ARCHIVED':
        raise PermissionDenied('Archived courses are read-only.')
    course = material.course
    with transaction.atomic():
        audit(request.user, 'material_deleted', course=course, resource_type='material', resource_id=pk)
        file_name, storage = material.pdf_file.name, material.pdf_file.storage
        material.delete()
        if file_name:
            transaction.on_commit(lambda: storage.delete(file_name))
    messages.success(request, 'Material removed.')
    return redirect('learning:course_detail', pk=course.pk)


@organization_account
def user_list(request):
    authorize(request.user, 'users_manage')
    query = request.GET.get('q', '').strip()
    users = User.objects.filter(organization=request.user.organization, is_superuser=False).order_by('username')
    if query:
        users = users.filter(Q(username__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query))
    return render(request, 'learning/users.html', {'page_obj': page(request, users), 'query': query})


@organization_account
def user_create(request):
    authorize(request.user, 'users_manage')
    form = OrganizationUserForm(request.POST or None, actor=request.user)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        audit(request.user, 'user_created', resource_type='user', resource_id=user.pk)
        messages.success(request, 'Organization user created.')
        return redirect('learning:user_list')
    return render_form(request, form, 'Create organization user', reverse('learning:user_list'), submit_label='Create user')


@organization_account
def user_edit(request, pk):
    authorize(request.user, 'users_manage')
    user = get_object_or_404(User, pk=pk, organization=request.user.organization, is_superuser=False)
    form = OrganizationUserForm(request.POST or None, actor=request.user, instance=user)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        audit(request.user, 'user_updated', resource_type='user', resource_id=user.pk)
        messages.success(request, 'User updated. Access changes apply on the next request.')
        return redirect('learning:user_list')
    return render_form(request, form, 'Edit organization user', reverse('learning:user_list'))


@organization_account
def policies(request):
    authorize(request.user, 'policies_view')
    catalog = policy_catalog()
    return render(request, 'learning/policies.html', {'catalog': catalog, 'policies': catalog['policies'],
                                                    'policy_version': catalog['version'], 'policy_roles': catalog.get('roles', [])})


@organization_account
def audit_log(request):
    authorize(request.user, 'audit_view')
    events = AuditEvent.objects.filter(organization=request.user.organization)
    query = request.GET.get('q', '').strip()
    decision = request.GET.get('decision', '')
    if query:
        events = events.filter(Q(actor_name__icontains=query) | Q(action__icontains=query) | Q(reason__icontains=query))
    if decision in ['allowed', 'denied']:
        events = events.filter(allowed=decision == 'allowed')
    return render(request, 'learning/audit.html', {'page_obj': page(request, events, 30), 'query': query, 'decision': decision})


def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        return JsonResponse({'status': 'ok'})
    except Exception:
        logging.getLogger(__name__).exception('Database health check failed')
        return JsonResponse({'status': 'unavailable'}, status=503)


def forbidden(request, exception=None):
    return render(request, '403.html', status=403)


def not_found(request, exception=None):
    return render(request, '404.html', status=404)
