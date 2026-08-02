import pytest
from backend.application.use_cases import RegisterUserUseCase, LoginUserUseCase, RefreshTokenUseCase, GetCurrentUserUseCase
from backend.domain.value_objects import Email, PasswordHash
from backend.domain.entities import User

def test_register_user(user_repo, hasher):
    uc = RegisterUserUseCase(user_repo, hasher)
    user = uc.execute("test@test.com", "username", "password123")
    assert user.email.value == "test@test.com"
    assert user.username == "username"
    assert user.password_hash.hash_value == "$2b$fake$password123"
    assert user_repo.find_by_email("test@test.com") == user

def test_register_user_duplicate_email(user_repo, hasher):
    uc = RegisterUserUseCase(user_repo, hasher)
    uc.execute("test@test.com", "username", "password123")
    with pytest.raises(ValueError, match="Ya existe un usuario con ese email."):
        uc.execute("test@test.com", "otheruser", "otherpassword")

def test_login_user(user_repo, hasher, token_service):
    user = User(email=Email("test@test.com"), username="user", password_hash=PasswordHash("$2b$fake$password123"))
    user_repo.save(user)
    
    uc = LoginUserUseCase(user_repo, hasher, token_service)
    logged_in_user, access, refresh = uc.execute("test@test.com", "password123")
    assert logged_in_user == user
    assert access == f"access-{user.id}"
    assert refresh == f"refresh-{user.id}"

def test_login_user_wrong_email(user_repo, hasher, token_service):
    uc = LoginUserUseCase(user_repo, hasher, token_service)
    with pytest.raises(ValueError, match="Credenciales incorrectas."):
        uc.execute("wrong@test.com", "password123")

def test_login_user_wrong_password(user_repo, hasher, token_service):
    user = User(email=Email("test@test.com"), username="user", password_hash=PasswordHash("$2b$fake$password123"))
    user_repo.save(user)
    
    uc = LoginUserUseCase(user_repo, hasher, token_service)
    with pytest.raises(ValueError, match="Credenciales incorrectas."):
        uc.execute("test@test.com", "wrongpassword")

def test_refresh_token(user_repo, token_service):
    user = User(email=Email("test@test.com"), username="user", password_hash=PasswordHash("$2b$fake$pass"))
    user_repo.save(user)
    
    uc = RefreshTokenUseCase(user_repo, token_service)
    new_access, new_refresh = uc.execute(f"refresh-{user.id}")
    assert new_access == f"access-{user.id}"
    assert new_refresh == f"refresh-{user.id}"

def test_refresh_token_invalid(user_repo, token_service):
    uc = RefreshTokenUseCase(user_repo, token_service)
    with pytest.raises(ValueError, match="Token de refresco inválido o expirado."):
        uc.execute("invalid-token")

def test_refresh_token_user_not_found(user_repo, token_service):
    uc = RefreshTokenUseCase(user_repo, token_service)
    with pytest.raises(ValueError, match="Usuario no encontrado."):
        uc.execute("refresh-nonexistent_id")

def test_get_current_user(user_repo, token_service):
    user = User(email=Email("test@test.com"), username="user", password_hash=PasswordHash("$2b$fake$pass"))
    user_repo.save(user)
    
    uc = GetCurrentUserUseCase(user_repo, token_service)
    found_user = uc.execute(f"access-{user.id}")
    assert found_user == user

def test_get_current_user_invalid(user_repo, token_service):
    uc = GetCurrentUserUseCase(user_repo, token_service)
    with pytest.raises(ValueError, match="Token de acceso inválido o expirado."):
        uc.execute("invalid-token")

def test_get_current_user_not_found(user_repo, token_service):
    uc = GetCurrentUserUseCase(user_repo, token_service)
    with pytest.raises(ValueError, match="Usuario no encontrado."):
        uc.execute("access-nonexistent_id")
