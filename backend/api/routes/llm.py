from fastapi import APIRouter, Depends
from backend.domain.ports import LLMProviderPort
from backend.api.dependencies import get_llm_provider, get_current_user
from backend.api.schemas import LLMHealthResponse
from backend.application.use_cases import CheckLLMHealthUseCase
from backend.domain.entities import User

router = APIRouter(prefix="/api/llm", tags=["LLM"])

@router.get("/health", response_model=LLMHealthResponse)
def get_llm_health(
    llm_provider: LLMProviderPort | None = Depends(get_llm_provider),
    current_user: User = Depends(get_current_user),
) -> LLMHealthResponse:
    use_case = CheckLLMHealthUseCase(llm_provider)
    result = use_case.execute()
    return LLMHealthResponse(
        status=result["status"],
        model=result["model"],
        message=result.get("message")
    )
