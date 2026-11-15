from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Organization, User


class SuperuserOnlyAdminMixin:
    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    has_add_permission = has_view_permission
    has_change_permission = has_view_permission
    has_delete_permission = has_view_permission


@admin.register(Organization)
class OrganizationAdmin(SuperuserOnlyAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'slug')


@admin.register(User)
class PlatformUserAdmin(SuperuserOnlyAdminMixin, UserAdmin):
    fieldsets = UserAdmin.fieldsets + (('Organization', {'fields': ('organization', 'role')}),)
    add_fieldsets = UserAdmin.add_fieldsets + (('Organization', {'fields': ('organization', 'role')}),)
    list_display = ('username', 'organization', 'role', 'is_active', 'is_superuser')

admin.site.site_header = 'Access Granted Platform Administration'
admin.site.site_title = 'Access Granted Admin'
