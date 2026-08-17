from django.db import models


class DiscoveredDuring(models.TextChoices):
    FLIGHT = "FLIGHT"
    INSPECTION = "INSPECTION"
    MAINTENANCE = "MAINTENANCE"
    OTHER = "OTHER"


class FailureSeverity(models.TextChoices):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
