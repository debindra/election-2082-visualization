"""
DeepSeek LLM Service

Handles interactions with DeepSeek API via OpenAI-compatible interface.
"""
import logging
from typing import List
import asyncio
from langchain_openai import ChatOpenAI
from openai import APITimeoutError, APIError, RateLimitError

from config.settings import settings

logger = logging.getLogger(__name__)


class DeepSeekLLMService:
    """
    Service for DeepSeek LLM integration.
    
    Uses OpenAI-compatible API for easy integration.
    """
    
    def __init__(self,
                 model: str = None,
                 temperature: float = None,
                 max_tokens: int = None,
                 timeout: int = None):
        """
        Initialize DeepSeek LLM service.
        
        Args:
            model: DeepSeek model name
            temperature: Sampling temperature (0=deterministic, 1=random)
            max_tokens: Maximum tokens in response
            timeout: Request timeout in seconds
        """
        self.model = model or settings.deepseek_model
        self.temperature = temperature or settings.deepseek_temperature
        self.max_tokens = max_tokens or settings.deepseek_max_tokens
        self.timeout = timeout or settings.deepseek_timeout
        
        logger.info(f"Initializing DeepSeek LLM: {self.model}")
        logger.info(f"Temperature: {self.temperature}")
        logger.info(f"Max tokens: {self.max_tokens}")
        
        # Initialize DeepSeek via OpenAI-compatible API
        try:
            self.llm = ChatOpenAI(
                api_key=settings.deepseek_api_key,
                base_url=settings.deepseek_base_url,
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                timeout=self.timeout
            )
            logger.info("DeepSeek LLM service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize DeepSeek: {e}")
            raise
    
    def invoke(self, prompt: str, max_retries: int = 3) -> str:
        """
        Invoke LLM with a prompt with retry logic.

        Args:
            prompt: Text prompt to send to LLM
            max_retries: Maximum number of retry attempts

        Returns:
            Generated response text
        """
        import time

        last_exception = None

        for attempt in range(max_retries):
            try:
                response = self.llm.invoke(prompt)
                content = response.content

                logger.debug(f"LLM response length: {len(content)} characters")
                return content
            except (APITimeoutError, TimeoutError) as e:
                last_exception = e
                logger.warning(f"Timeout on attempt {attempt + 1}/{max_retries}: {e}")
                if attempt < max_retries - 1:
                    wait_time = min(2 ** attempt, 10)
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"All {max_retries} retry attempts failed due to timeout")
                    raise
            except RateLimitError as e:
                last_exception = e
                logger.warning(f"Rate limit on attempt {attempt + 1}/{max_retries}: {e}")
                if attempt < max_retries - 1:
                    wait_time = min(5 * (attempt + 1), 30)
                    logger.info(f"Rate limited. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error("All retry attempts failed due to rate limiting")
                    raise
            except APIError as e:
                last_exception = e
                logger.error(f"API error on attempt {attempt + 1}/{max_retries}: {e}")
                raise
            except Exception as e:
                last_exception = e
                logger.error(f"Unexpected error on attempt {attempt + 1}/{max_retries}: {e}")
                if attempt < max_retries - 1:
                    wait_time = min(2 ** attempt, 5)
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"All {max_retries} retry attempts failed")
                    raise

        raise last_exception or Exception("Unknown error occurred")
    
    async def ainvoke(self, prompt: str, max_retries: int = 3) -> str:
        """
        Async invoke LLM with a prompt with retry logic.

        Args:
            prompt: Text prompt to send to LLM
            max_retries: Maximum number of retry attempts

        Returns:
            Generated response text
        """
        last_exception = None

        for attempt in range(max_retries):
            try:
                response = await self.llm.ainvoke(prompt)
                content = response.content

                logger.debug(f"LLM async response length: {len(content)} characters")
                return content
            except APITimeoutError as e:
                last_exception = e
                logger.warning(f"Timeout on attempt {attempt + 1}/{max_retries}: {e}")
                if attempt < max_retries - 1:
                    # Exponential backoff: 2^attempt seconds
                    wait_time = min(2 ** attempt, 10)  # Cap at 10 seconds
                    logger.info(f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"All {max_retries} retry attempts failed due to timeout")
                    raise
            except RateLimitError as e:
                last_exception = e
                logger.warning(f"Rate limit on attempt {attempt + 1}/{max_retries}: {e}")
                if attempt < max_retries - 1:
                    wait_time = min(5 * (attempt + 1), 30)  # Progressive backoff
                    logger.info(f"Rate limited. Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error("All retry attempts failed due to rate limiting")
                    raise
            except APIError as e:
                last_exception = e
                logger.error(f"API error on attempt {attempt + 1}/{max_retries}: {e}")
                # Don't retry on API errors (they're not transient)
                raise
            except Exception as e:
                last_exception = e
                logger.error(f"Unexpected error on attempt {attempt + 1}/{max_retries}: {e}")
                if attempt < max_retries - 1:
                    wait_time = min(2 ** attempt, 5)
                    logger.info(f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"All {max_retries} retry attempts failed")
                    raise

        # This should never be reached, but just in case
        raise last_exception or Exception("Unknown error occurred")
    
    def batch_invoke(self, prompts: List[str]) -> List[str]:
        """
        Invoke multiple prompts in batch.
        
        Args:
            prompts: List of prompts to send
            
        Returns:
            List of response texts
        """
        try:
            responses = self.llm.batch([self.llm.__class__.construct(messages=[prompt]) for prompt in prompts])
            contents = [r.content for r in responses]
            
            logger.info(f"Batch LLM invoked: {len(contents)} responses")
            return contents
        except Exception as e:
            logger.error(f"Error batch invoking LLM: {e}")
            raise
    
    def stream(self, prompt: str):
        """
        Stream responses from LLM.
        
        Args:
            prompt: Text prompt to send
            
        Yields:
            Response chunks as they arrive
        """
        try:
            logger.info("Starting LLM stream")
            
            for chunk in self.llm.stream(prompt):
                if hasattr(chunk, 'content') and chunk.content:
                    yield chunk.content
            
            logger.info("LLM stream completed")
        except Exception as e:
            logger.error(f"Error streaming LLM: {e}")
            raise
    
    def is_configured(self) -> bool:
        """
        Check if DeepSeek API is properly configured.
        
        Returns:
            True if API key is set, False otherwise
        """
        return bool(settings.deepseek_api_key and len(settings.deepseek_api_key) > 0)
