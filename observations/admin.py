from django.contrib import admin
from .models import Task, DailyRecord

admin.site.register(Task)
admin.site.register(DailyRecord)