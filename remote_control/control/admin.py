from django.contrib import admin

from control.models import RecordDriver


class RecordActionAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'action', 'speed', 'angle')


admin.site.register(RecordDriver, RecordActionAdmin)
