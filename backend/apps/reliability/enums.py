from django.db import models


class ReliabilityScope(models.TextChoices):
    FLEET = "fleet"
    CLASS = "class"
    UAV = "uav"
    COMPONENT = "component"


class ZeroFailurePolicy(models.TextChoices):
    UNDEFINED = "undefined"
    OPERATING_TIME_AS_LOWER_BOUND = "operating_time_as_lower_bound"
