from django.db import models


class Currency(models.TextChoices):
    TRY = "TRY"
    USD = "USD"
    EUR = "EUR"
    AZN = "AZN"


class PartStatus(models.TextChoices):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
