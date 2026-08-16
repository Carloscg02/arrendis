import pytest
from dataclasses import FrozenInstanceError

from backend.domain.value_objects import LLMRequest, LLMResponse
from backend.domain.entities import LLMProviderError, RateLimitError

# T-17-01: LLMRequest valid creation
def test_llm_request_valid_creation():
    req = LLMRequest(
        user_prompt="Hello",
        system_prompt="You are helpful",
        response_schema={"type": "object"},
        temperature=0.5,
        max_output_tokens=1000
    )
    assert req.user_prompt == "Hello"
    assert req.system_prompt == "You are helpful"
    assert req.response_schema == {"type": "object"}
    assert req.temperature == 0.5
    assert req.max_output_tokens == 1000

# T-17-02: Empty prompt raises ValueError
def test_llm_request_empty_prompt():
    with pytest.raises(ValueError, match="user_prompt cannot be empty"):
        LLMRequest(user_prompt="")

# T-17-03: Whitespace-only prompt raises ValueError
def test_llm_request_whitespace_prompt():
    with pytest.raises(ValueError, match="user_prompt cannot be empty"):
        LLMRequest(user_prompt="   \n \t  ")

# T-17-04: Invalid temperature raises ValueError
def test_llm_request_invalid_temperature():
    with pytest.raises(ValueError, match="temperature must be between 0.0 and 2.0"):
        LLMRequest(user_prompt="Hello", temperature=-0.1)
    
    with pytest.raises(ValueError, match="temperature must be between 0.0 and 2.0"):
        LLMRequest(user_prompt="Hello", temperature=2.1)

# T-17-05: Invalid max_output_tokens raises ValueError
def test_llm_request_invalid_max_output_tokens():
    with pytest.raises(ValueError, match="max_output_tokens must be positive"):
        LLMRequest(user_prompt="Hello", max_output_tokens=0)
        
    with pytest.raises(ValueError, match="max_output_tokens must be positive"):
        LLMRequest(user_prompt="Hello", max_output_tokens=-10)

# T-17-06: Default values are correct
def test_llm_request_defaults():
    req = LLMRequest(user_prompt="Hello")
    assert req.system_prompt is None
    assert req.response_schema is None
    assert req.temperature == 0.0
    assert req.max_output_tokens == 2048

# T-17-07: Immutability (frozen=True)
def test_llm_request_immutability():
    req = LLMRequest(user_prompt="Hello")
    with pytest.raises(FrozenInstanceError):
        req.user_prompt = "New prompt"

# T-17-08: LLMResponse valid creation
def test_llm_response_valid_creation():
    resp = LLMResponse(
        text="Result",
        parsed_data={"k": "v"},
        model_name="gpt-4",
        input_tokens=10,
        output_tokens=20
    )
    assert resp.text == "Result"
    assert resp.parsed_data == {"k": "v"}
    assert resp.model_name == "gpt-4"
    assert resp.input_tokens == 10
    assert resp.output_tokens == 20

# T-17-09: LLMResponse.total_tokens property
def test_llm_response_total_tokens():
    resp = LLMResponse(text="Result", input_tokens=15, output_tokens=30)
    assert resp.total_tokens == 45

# T-17-10: LLMProviderError includes provider name
def test_llm_provider_error_message():
    err = LLMProviderError("Something went wrong", provider="Anthropic")
    assert "Something went wrong" in str(err)
    assert "[Anthropic]" in str(err)
    assert err.provider == "Anthropic"

# T-17-11: RateLimitError stores retry_after_seconds
def test_rate_limit_error_retry_after():
    err = RateLimitError(provider="OpenAI", retry_after_seconds=30)
    assert err.retry_after_seconds == 30
    assert "retry after 30s" in str(err)
    assert "[OpenAI]" in str(err)

# T-17-12: RateLimitError inherits from LLMProviderError
def test_rate_limit_error_inheritance():
    err = RateLimitError()
    assert isinstance(err, LLMProviderError)
