from django.db import models


class UAVStatus(models.TextChoices):
    READY = "READY"
    MAINTENANCE = "MAINTENANCE"
    GROUNDED = "GROUNDED"
    RETIRED = "RETIRED"


class MaintenanceApproach(models.TextChoices):
    STANDARD = "STANDARD"
    CLASS_SPECIFIC = "CLASS_SPECIFIC"
