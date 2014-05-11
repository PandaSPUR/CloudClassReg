from django.contrib import admin
from registration.models import *

admin.site.register(Student)
admin.site.register(Course)
admin.site.register(Transcript)
admin.site.register(CoursePrereq)
admin.site.register(Cart)
admin.site.register(Major)

# Register your models here.
