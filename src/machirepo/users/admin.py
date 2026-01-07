from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin 

CustomUser = get_user_model()

class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}), 
        (('Personal info'), {'fields': ('email',)}),  
        (('Permissions'), {'fields': ('is_staff', 'is_superuser'), }),
        (('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    list_display = ('username', 'email', 'is_staff', 'is_superuser')
    list_filter = ('is_staff', 'is_superuser')
    filter_horizontal = () 

    ordering = ('username',)
    search_fields = ('username', 'email')


admin.site.register(CustomUser, CustomUserAdmin)