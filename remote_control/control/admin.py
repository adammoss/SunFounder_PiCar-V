from django.contrib import admin

from control.models import Recording


class RecordingAdmin(admin.ModelAdmin):
    list_display = ('timestamp',)


admin.site.register(Recording, RecordingAdmin)
