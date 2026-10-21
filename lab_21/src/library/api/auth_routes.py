"""Роутер аутентификации: /auth/register, /auth/login."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_session
from ..models import Reader
from ..schemas import LoginRequest, TokenResponse, UserRegister
from ..services import AuthService
from .deps import get_auth_service

router = APIRouter()


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=201,
    summary="Регистрация нового читателя (роль USER)",
)
def register(
    data: UserRegister,
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    reader: Reader = service.register(data)
    token = service.token_for(reader)
    return TokenResponse(access_token=token)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Вход по логину и паролю",
)
def login(
    data: LoginRequest,
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    reader = service.login(data)
    token = service.token_for(reader)
    return TokenResponse(access_token=token)