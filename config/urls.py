from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from learning import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/login/', auth_views.LoginView.as_view(redirect_authenticated_user=True), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('health/', views.health, name='health'),
    path('', include('learning.urls')),
]
handler403 = 'learning.views.forbidden'
handler404 = 'learning.views.not_found'
