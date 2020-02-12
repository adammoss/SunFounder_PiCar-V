from __future__ import unicode_literals

from django.db import models
from django.utils import timezone

# Create your models here.


class RecordDriver(models.Model):
    timestamp = models.DateTimeField(default=timezone.now)
    action = models.CharField(max_length=100)
    angle = models.IntegerField()
    speed = models.IntegerField()
