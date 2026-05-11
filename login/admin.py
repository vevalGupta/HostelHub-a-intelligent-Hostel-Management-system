from django.contrib import admin
from .models import Complaint, Fee, Room, StudentProfile, ActivityLog

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'student_id', 'room', 'phone')

admin.site.register(Room)
admin.site.register(ActivityLog)
@admin.register(Fee)
class FeeAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'paid', 'created_at']
    list_filter = ['paid']

@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ['user', 'category', 'created_at']
    list_filter = ['category']
    search_fields = ['user__username']



