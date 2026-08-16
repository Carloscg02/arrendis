import time
import random
import json

from google import genai
from google.genai import types
from google.genai.errors import APIError

from backend.domain.ports import LLMProviderPort
from backend.domain.value_objects import LLMRequest, LLMResponse
from backend.domain.entities import LLMProviderError, RateLimitError


class GeminiFlashAdapter(LLMProviderPort):
    """Adaptador que implementa LLMProviderPort usando Google Gemini Flash."""

    MODEL_NAME = "gemini-2.0-flash"
    PROVIDER_NAME = "gemini"
    MAX_RETRIES = 3
    INITIAL_BACKOFF_SECONDS = 1.0
    MAX_BACKOFF_SECONDS = 30.0

    def __init__(self, api_key: str):
        """Inicializa el cliente de Gemini.
        
        Args:
            api_key: API key de Google AI Studio.
            
        Raises:
            LLMProviderError: Si la API key está vacía o el cliente no se puede crear.
        """
        if not api_key:
            raise LLMProviderError("API key is required", provider=self.PROVIDER_NAME)
        try:
            self.client = genai.Client(api_key=api_key)
        except Exception as e:
            raise LLMProviderError(f"Failed to initialize client: {str(e)}", provider=self.PROVIDER_NAME)

    def generate(self, request: LLMRequest) -> LLMResponse:
        """Implementa la generación usando google-genai SDK."""
        config = types.GenerateContentConfig(
            temperature=request.temperature,
            max_output_tokens=request.max_output_tokens,
        )
        if request.system_prompt:
            config.system_instruction = request.system_prompt
        
        if request.response_schema:
            config.response_mime_type = "application/json"
            config.response_schema = request.response_schema
        
        retries = 0
        backoff = self.INITIAL_BACKOFF_SECONDS

        while True:
            try:
                response = self.client.models.generate_content(
                    model=self.MODEL_NAME,
                    contents=request.user_prompt,
                    config=config,
                )
                
                text = response.text or ""
                
                parsed_data = None
                if request.response_schema:
                    try:
                        parsed_data = json.loads(text)
                    except json.JSONDecodeError:
                        raise LLMProviderError("Failed to parse JSON response", provider=self.PROVIDER_NAME)
                
                input_tokens = 0
                output_tokens = 0
                if response.usage_metadata:
                    input_tokens = response.usage_metadata.prompt_token_count
                    output_tokens = response.usage_metadata.candidates_token_count
                
                return LLMResponse(
                    text=text,
                    parsed_data=parsed_data,
                    model_name=self.MODEL_NAME,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                )

            except APIError as e:
                is_retryable = False
                if e.code == 429 or (e.code and e.code >= 500):
                    is_retryable = True
                
                if is_retryable and retries < self.MAX_RETRIES:
                    jitter = random.uniform(0, 0.1 * backoff)
                    sleep_time = backoff + jitter
                    time.sleep(sleep_time)
                    retries += 1
                    backoff = min(backoff * 2.0, self.MAX_BACKOFF_SECONDS)
                    continue
                else:
                    if e.code == 429:
                        raise RateLimitError(provider=self.PROVIDER_NAME)
                    raise LLMProviderError(f"API Error: {str(e)}", provider=self.PROVIDER_NAME)
            except RateLimitError:
                raise
            except LLMProviderError:
                raise
            except Exception as e:
                raise LLMProviderError(f"Unexpected error: {str(e)}", provider=self.PROVIDER_NAME)
