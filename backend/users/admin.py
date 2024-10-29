from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin


User = get_user_model()


class ApplicationUserAdmin(UserAdmin):
    model = User
    search_fields = ('username', 'email')


admin.site.register(User, ApplicationUserAdmin)
