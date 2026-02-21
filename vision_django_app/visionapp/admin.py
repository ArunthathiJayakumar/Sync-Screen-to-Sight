from django.contrib import admin
from .models import UserVisionData

@admin.register(UserVisionData)
class UserVisionDataAdmin(admin.ModelAdmin):
    list_display = ('user', 'left_v', 'right_v', 'left_d', 'right_d', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
