from django.urls import path

from apps.core.search_views import SearchView

urlpatterns = [
    path("", SearchView.as_view(), name="search"),
]
