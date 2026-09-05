from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Response, Cookie
import os

from backend.adapters.sqlite_adapter import SQLiteConnection, SQLiteUserRepository
from backend.adapters.auth_adapter import BcryptPasswordHasherAdapter, JWTTokenServiceAdapter
from backend.api.dependencies import get_db, get_user_repo, get_hasher, get_token_service, get_current_user
from backend.api.schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    TokenResponse,
    ForwardingEmailUpdate,
    ForwardingEmailResponse,
)
from backend.application.use_cases import (
    RegisterUserUseCase,
    LoginUserUseCase,
    RefreshTokenUseCase,
    UpdateForwardingEmailUseCase,
)
from backend.domain.entities import User

router = APIRouter(prefix="/api/auth", tags=["auth"])

def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,  # False for local dev (HTTP), True in production
        samesite="lax",
        path="/api/auth",
        max_age=7 * 24 * 3600,
    )

def _user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email.value,
        username=user.username,
        forwarding_email=user.forwarding_email,
    )


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(
    body: UserRegisterRequest,
    response: Response,
    db: SQLiteConnection = Depends(get_db),
    hasher: BcryptPasswordHasherAdapter = Depends(get_hasher),
    tokens: JWTTokenServiceAdapter = Depends(get_token_service),
):
    user_repo = SQLiteUserRepository(db)
    use_case = RegisterUserUseCase(user_repo, hasher)
    try:
        user = use_case.execute(body.email, body.username, body.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    access = tokens.create_access_token(user.id)
    refresh = tokens.create_refresh_token(user.id)
    _set_refresh_cookie(response, refresh)
    return TokenResponse(access_token=access, user=_user_response(user))


@router.post("/login", response_model=TokenResponse)
def login(
    body: UserLoginRequest,
    response: Response,
    db: SQLiteConnection = Depends(get_db),
    hasher: BcryptPasswordHasherAdapter = Depends(get_hasher),
    tokens: JWTTokenServiceAdapter = Depends(get_token_service),
):
    user_repo = SQLiteUserRepository(db)
    use_case = LoginUserUseCase(user_repo, hasher, tokens)
    try:
        user, access, refresh = use_case.execute(body.email, body.password)
    except ValueError:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    _set_refresh_cookie(response, refresh)
    return TokenResponse(access_token=access, user=_user_response(user))


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    response: Response,
    refresh_token: str | None = Cookie(None),
    db: SQLiteConnection = Depends(get_db),
    tokens: JWTTokenServiceAdapter = Depends(get_token_service),
):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No se encontró token de refresco")
    user_repo = SQLiteUserRepository(db)
    use_case = RefreshTokenUseCase(user_repo, tokens)
    try:
        new_access, new_refresh = use_case.execute(refresh_token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Token de refresco inválido o expirado")
    # Get user for response
    user_id = tokens.verify_token(new_access)
    user = user_repo.find_by_id(user_id)
    _set_refresh_cookie(response, new_refresh)
    return TokenResponse(access_token=new_access, user=_user_response(user))


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key="refresh_token", path="/api/auth")
    return {"message": "Sesión cerrada"}


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return _user_response(current_user)


@router.get("/forwarding-email", response_model=ForwardingEmailResponse)
def get_forwarding_email(current_user: User = Depends(get_current_user)):
    inbound_address = os.getenv("INBOUND_EMAIL_ADDRESS", "facturas@rental-handler.com")
    return ForwardingEmailResponse(
        forwarding_email=current_user.forwarding_email,
        inbound_address=inbound_address,
    )


@router.put("/forwarding-email", response_model=ForwardingEmailResponse)
def update_forwarding_email(
    body: ForwardingEmailUpdate,
    current_user: User = Depends(get_current_user),
    db: SQLiteConnection = Depends(get_db),
):
    user_repo = SQLiteUserRepository(db)
    use_case = UpdateForwardingEmailUseCase(user_repo)
    try:
        updated_user = use_case.execute(current_user.id, body.forwarding_email)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    inbound_address = os.getenv("INBOUND_EMAIL_ADDRESS", "facturas@rental-handler.com")
    return ForwardingEmailResponse(
        forwarding_email=updated_user.forwarding_email,
        inbound_address=inbound_address,
    )
