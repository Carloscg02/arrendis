import pytest
from unittest.mock import Mock

from backend.application.use_cases import CheckLLMHealthUseCase
from backend.domain.ports import LLMProviderPort
from backend.domain.value_objects import LLMResponse
from backend.domain.entities import LLMProviderError

# T-17-13: llm_provider=None -> status "not_configured"
def test_llm_health_not_configured():
    use_case = CheckLLMHealthUseCase(llm_provider=None)
    result = use_case.execute()
    assert result == {"status": "not_configured", "model": None}

# T-17-14: Mock returns LLMResponse -> status "ok", model name present
def test_llm_health_ok():
    mock_llm = Mock(spec=LLMProviderPort)
    mock_llm.generate.return_value = LLMResponse(
        text="pong", 
        model_name="mock-model",
        input_tokens=1,
        output_tokens=1
    )
    
    use_case = CheckLLMHealthUseCase(llm_provider=mock_llm)
    result = use_case.execute()
    
    assert result == {"status": "ok", "model": "mock-model"}
    mock_llm.generate.assert_called_once()
    req = mock_llm.generate.call_args[0][0]
    assert req.user_prompt == "ping"

# T-17-15: Mock raises LLMProviderError -> status "error", message present
def test_llm_health_error():
    mock_llm = Mock(spec=LLMProviderPort)
    mock_llm.generate.side_effect = LLMProviderError("Connection failed", provider="TestProvider")
    
    use_case = CheckLLMHealthUseCase(llm_provider=mock_llm)
    result = use_case.execute()
    
    assert result["status"] == "error"
    assert result["model"] is None
    assert "[TestProvider] Connection failed" in result["message"]
