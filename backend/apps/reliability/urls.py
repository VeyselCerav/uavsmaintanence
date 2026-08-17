from django.urls import path

from apps.reliability.views import ReliabilityViewSet

urlpatterns = [
    path("", ReliabilityViewSet.as_view({"get": "list"}), name="reliability"),
]
