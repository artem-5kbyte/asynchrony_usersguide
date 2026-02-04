from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser
# Register your models here.

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['email', 'first_name', 'last_name', 'username', 'phone', 'address1', 'address2', 'city', 'country', 'province', 'postal_code', 'marketing_consent1', 'marketing_consent2']