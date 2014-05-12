from django.contrib import admin
from registration.models import *

admin.site.register(Student)
admin.site.register(Major)
admin.site.register(CredentialsModel)
admin.site.register(FlowModel)
admin.site.register(Calendar)
admin.site.register(Semester)

class CourseAdmin(admin.ModelAdmin):
	list_display = ('code', 'major', 'name', 'professor', 'room')
	list_filter = ['major', 'professor', 'room']
	search_fields = ['code', 'name', 'description', 'professor']
admin.site.register(Course, CourseAdmin)

class TranscriptAdmin(admin.ModelAdmin):
	list_display = ('student', 'course', 'grade')
	list_filter = ['student']
admin.site.register(Transcript, TranscriptAdmin)

class CartAdmin(admin.ModelAdmin):
	list_display = ('student', 'course')
	list_filter = ['student']
admin.site.register(Cart, CartAdmin)

class CoursePrereqAdmin(admin.ModelAdmin):
    list_display = ('course', 'prereq')
    list_filter = ['course']
admin.site.register(CoursePrereq, CoursePrereqAdmin)
