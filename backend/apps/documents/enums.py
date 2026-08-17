from django.db import models


class DocumentType(models.TextChoices):
    MANUAL = "MANUAL"
    PROCEDURE = "PROCEDURE"
    CERTIFICATE = "CERTIFICATE"
    PHOTO = "PHOTO"
    REPORT = "REPORT"
    OTHER = "OTHER"
