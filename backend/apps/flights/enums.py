from django.db import models


class FlightResult(models.TextChoices):
    COMPLETED = "COMPLETED"
    ABORTED = "ABORTED"
    TRAINING = "TRAINING"
