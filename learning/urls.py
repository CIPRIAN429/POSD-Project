from django.urls import path
from . import views

app_name = 'learning'
urlpatterns = [
    path('guide/', views.user_guide, name='guide'),
    path('guide/download/', views.guide_download, name='guide_download'),
    path('', views.dashboard, name='dashboard'),
    path('courses/', views.catalog, name='catalog'),
    path('my-courses/', views.my_courses, name='my_courses'),
    path('manage/courses/', views.manage_courses, name='manage_courses'),
    path('courses/new/', views.course_create, name='course_create'),
    path('courses/<int:pk>/', views.course_detail, name='course_detail'),
    path('courses/<int:pk>/edit/', views.course_edit, name='course_edit'),
    path('courses/<int:pk>/archive/', views.course_archive, name='course_archive'),
    path('courses/<int:pk>/enroll/', views.enroll, name='enroll'),
    path('courses/<int:pk>/withdraw/', views.withdraw, name='withdraw'),
    path('courses/<int:pk>/participants/', views.participants, name='participants'),
    path('enrollments/<int:pk>/complete/', views.complete, name='complete'),
    path('courses/<int:pk>/materials/new/', views.material_create, name='material_create'),
    path('materials/<int:pk>/', views.material_detail, name='material_detail'),
    path('materials/<int:pk>/download/', views.material_download, name='material_download'),
    path('materials/<int:pk>/edit/', views.material_edit, name='material_edit'),
    path('materials/<int:pk>/delete/', views.material_delete, name='material_delete'),
    path('organization/users/', views.user_list, name='user_list'),
    path('organization/users/new/', views.user_create, name='user_create'),
    path('organization/users/<int:pk>/edit/', views.user_edit, name='user_edit'),
    path('organization/policies/', views.policies, name='policies'),
    path('organization/audit/', views.audit_log, name='audit'),
]
