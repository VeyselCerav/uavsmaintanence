from django.urls import path

from apps.accounts.views import (
    ForgotPasswordConfirmView,
    ForgotPasswordView,
    LoginView,
    LogoutView,
    MeView,
    RefreshView,
)

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", RefreshView.as_view(), name="refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
    path("forgot-password/", ForgotPasswordView.as_view(), name="forgot-password"),
    path(
        "forgot-password/confirm/",
        ForgotPasswordConfirmView.as_view(),
        name="forgot-password-confirm",
    ),
]
