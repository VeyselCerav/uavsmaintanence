from django.db import models


class PdfReportType(models.TextChoices):
    UAV_HISTORY = "uav-history"
    MAINTENANCE = "maintenance"
    WORK_ORDER = "work-order"
    FAILURE = "failure"
    FMEA = "fmea"
    RCM = "rcm"
    FLEET = "fleet"
    RELIABILITY = "reliability"
    COST = "cost"
    APPROACH_COMPARISON = "approach-comparison"


class XlsxReportType(models.TextChoices):
    UAVS = "uavs"
    COMPONENTS = "components"
    FLIGHTS = "flights"
    MAINTENANCE = "maintenance"
    FAILURES = "failures"
    FMEA = "fmea"
    RCM = "rcm"
    COSTS = "costs"
    APPROACH_COMPARISON = "approach-comparison"
