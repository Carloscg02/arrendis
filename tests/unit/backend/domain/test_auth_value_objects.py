import pytest
from backend.domain.value_objects import Email, PasswordHash

def test_email_valid():
    e = Email("User@Test.Com")
    assert e.value == "user@test.com"  # normalized

def test_email_invalid_no_at():
    with pytest.raises(ValueError):
        Email("invalid")

def test_email_empty():
    with pytest.raises(ValueError):
        Email("")

def test_password_hash_valid():
    ph = PasswordHash("$2b$12$abcdefghijklmnopqrstuuABCDEFGHIJKLMNOPQRSTUVWXYZ01234")
    assert ph.hash_value.startswith("$2b$")

def test_password_hash_invalid():
    with pytest.raises(ValueError):
        PasswordHash("plain_text_password")
