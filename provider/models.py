from django.db import models

class Provider(models.Model):
    name = models.CharField(max_length=100, unique=True)
    adapter_key = models.CharField(max_length=100)
    api_url = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    priority = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name