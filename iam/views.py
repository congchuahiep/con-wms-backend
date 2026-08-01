from typing import cast

from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    LoginSerializer,
    LogoutSerializer,
    RegisterSerializer,
    TokenObtainPairSerializer,
    UserProfileSerializer,
)

User = get_user_model()


@extend_schema(tags=["Auth"])
@extend_schema_view(
    login=extend_schema(
        summary="Đăng nhập",
        description="Xác thực người dùng và trả về JWT token pair.",
        auth=[],
        request=TokenObtainPairSerializer,
        responses={200: None, 401: None},
    ),
    refresh=extend_schema(
        summary="Làm mới token",
        description="Nhận refresh token và trả về access token mới.",
        auth=[],
        request=TokenRefreshSerializer,
        responses={200: None, 401: None},
    ),
    register=extend_schema(
        summary="Đăng ký",
        description="Tạo tài khoản mới cho người dùng.",
        auth=[],
        request=RegisterSerializer,
        responses={201: None, 400: None},
    ),
    logout=extend_schema(
        summary="Đăng xuất",
        description="Vô hiệu hoá refresh token (blacklist).",
        request=LogoutSerializer,
        responses={204: None, 400: None},
    ),
    me=extend_schema(
        summary="Thông tin người dùng hiện tại",
        description="Trả về profile của user đang đăng nhập.",
        responses={200: UserProfileSerializer},
    ),
)
class AuthViewSet(viewsets.GenericViewSet):
    def get_permissions(self):
        if self.action in ("login", "refresh", "register", "logout"):
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == "login":
            return LoginSerializer
        if self.action == "register":
            return RegisterSerializer
        if self.action == "logout":
            return LogoutSerializer
        if self.action == "me":
            return UserProfileSerializer
        return super().get_serializer_class()

    @action(detail=False, methods=["post"], url_path="login")
    def login(self, request: Request, *_args, **_kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0]) from e
        return Response(serializer.validated_data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="register")
    def register(self, request: Request, *_args, **_kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        password = serializer.validated_data["password"]
        user = serializer.save()

        try:
            token_serializer = TokenObtainPairSerializer(
                data={"email": user.email, "password": password}
            )
            token_serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0]) from e

        return Response(
            {
                "user": UserProfileSerializer(user).data,
                **token_serializer.validated_data,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["post"], url_path="refresh")
    def refresh(self, request: Request, *_args, **_kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0]) from e
        return Response(serializer.validated_data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="logout")
    def logout(self, request: Request, *_args, **_kwargs) -> Response:
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh_token = serializer.validated_data["refresh"]
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError as e:
            raise InvalidToken(e.args[0]) from e
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request: Request, *_args, **_kwargs) -> Response:
        user = cast(User, request.user)
        serializer = UserProfileSerializer(user)
        return Response(serializer.data)
