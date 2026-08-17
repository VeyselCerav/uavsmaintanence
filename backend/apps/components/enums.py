from django.db import models


class ComponentStatus(models.TextChoices):
    INSTALLED = "INSTALLED"
    REMOVED = "REMOVED"
    QUARANTINE = "QUARANTINE"
    SCRAPPED = "SCRAPPED"
