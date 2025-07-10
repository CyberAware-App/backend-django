from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.http import HttpResponse
from django.contrib.auth import get_user_model

# Register your models here.

class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {
          'classes': ['wide'],
          'fields': ('email', 'password')
        }),
        (('Permissions'), {
          'classes': ['wide'],
          'fields': ('is_superuser', 'is_staff', 'is_active', 'groups')
        }),
    )
    add_fieldsets = (
        (None, {
          'classes': ('wide',),
          'fields': ('email', 'password1', 'password2')}
        ),
    )  
    list_display = ['email', 'is_staff', 'created']
    list_filter = ['email', 'is_staff', 'is_active']
    search_fields = ['email']
    ordering = ('email',)  

admin.site.register(get_user_model(), CustomUserAdmin)  
