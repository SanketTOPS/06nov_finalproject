from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'fullname', 'mobile', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('fullname', 'mobile')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('fullname', 'mobile')}),
    )

admin.site.register(CustomUser, CustomUserAdmin)
