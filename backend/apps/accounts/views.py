from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.serializers import (
    ForgotPasswordConfirmSerializer,
    ForgotPasswordSerializer,
    LoginSerializer,
    LogoutSerializer,
    MeSerializer,
    RefreshSerializer,
)
from apps.accounts.services import AuthService, ProfileService


class LoginView(APIView):
    authentication_classes: list = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request,
            username=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )
        if user is None or not user.is_active or user.is_deleted:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_CREDENTIALS",
                        "message_key": "errors.auth.invalid_credentials",
                        "details": {},
                    },
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )
        return Response({"success": True, "data": AuthService.issue_tokens(user)})


class RefreshView(APIView):
    authentication_classes: list = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            token = RefreshToken(serializer.validated_data["refresh"])
            return Response(
                {
                    "success": True,
                    "data": {
                        "access": str(token.access_token),
                        "refresh": str(token),
                    },
                }
            )
        except TokenError:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_REFRESH",
                        "message_key": "errors.auth.invalid_refresh",
                        "details": {},
                    },
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            AuthService.logout(serializer.validated_data["refresh"])
        except TokenError:
            pass
        return Response({"success": True, "data": {"logged_out": True}})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"success": True, "data": MeSerializer(request.user).data})

    def patch(self, request):
        serializer = MeSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = ProfileService.update(
            user=request.user,
            data=serializer.validated_data,
            request=request,
        )
        return Response({"success": True, "data": MeSerializer(user).data})


class ForgotPasswordView(APIView):
    authentication_classes: list = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = AuthService.request_password_reset(email=serializer.validated_data["email"])
        return Response({"success": True, "data": data})


class ForgotPasswordConfirmView(APIView):
    authentication_classes: list = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        AuthService.confirm_password_reset(
            token=serializer.validated_data["token"],
            new_password=serializer.validated_data["new_password"],
        )
        return Response({"success": True, "data": {"reset": True}})
