# llm_config.py - Centralized LLM Configuration with Fallback System
# Primary: OpenAI GPT-4o-mini | Fallback: GLM-4.5-Air

import os
import logging
from typing import Optional, Dict, Any
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# LLM Configuration
LLM_CONFIG = {
    'primary': {
        'name': 'gpt-4o-mini',
        'model': 'gpt-4o-mini',
        'api_key_env': 'OPENAI_API_KEY',
        # 'base_url': None,  # Uses default OpenAI endpoint
        'temperature': 0.7,
        'max_tokens': 1024,
        'timeout': 30
    },
    'fallback': {
        'name': 'GLM-4.5-Air',
        'model': 'GLM-4.5-Air',
        'api_key_env': 'GLM_API_KEY',
        'base_url': 'https://api.z.ai/api/paas/v4/',
        'temperature': 0.7,
        'max_tokens': 500,
        'timeout': 10
    }
}

class LLMManager:
    """Manages LLM instances with automatic fallback"""

    def __init__(self):
        self.primary_llm = None
        self.fallback_llm = None
        self.current_model = None
        self.failure_count = {'primary': 0, 'fallback': 0}
        self.max_retries = 2

        self._initialize_llms()

    def _initialize_llms(self):
        """Initialize both primary and fallback LLMs"""
        try:
            # Initialize Primary LLM (GPT-3.5-turbo)
            primary_key = os.getenv(LLM_CONFIG['primary']['api_key_env'])
            if not primary_key:
                raise ValueError(f" {LLM_CONFIG['primary']['api_key_env']} environment variable must be set")
            self.primary_llm = ChatOpenAI(
                model=LLM_CONFIG['primary']['model'],
                openai_api_key=primary_key,
                temperature=LLM_CONFIG['primary']['temperature'],
                max_tokens=LLM_CONFIG['primary']['max_tokens'],
                request_timeout=LLM_CONFIG['primary']['timeout']
            )
            logger.info(f" Primary LLM initialized: {LLM_CONFIG['primary']['name']}")

        except Exception as e:
            logger.error(f" Failed to initialize primary LLM: {e}")

        try:
            # Initialize Fallback LLM (GLM-4.5-Air)
            fallback_key = os.getenv(LLM_CONFIG['fallback']['api_key_env'])
            if fallback_key:
                self.fallback_llm = ChatOpenAI(
                    model=LLM_CONFIG['fallback']['model'],
                    openai_api_key=fallback_key,
                    base_url=LLM_CONFIG['fallback']['base_url'],
                    temperature=LLM_CONFIG['fallback']['temperature'],
                    max_tokens=LLM_CONFIG['fallback']['max_tokens'],
                    request_timeout=LLM_CONFIG['fallback']['timeout']
                )
                logger.info(f" Fallback LLM initialized: {LLM_CONFIG['fallback']['name']}")
            else:
                logger.warning(f" Fallback LLM API key not found: {LLM_CONFIG['fallback']['api_key_env']}")

        except Exception as e:
            logger.error(f" Failed to initialize fallback LLM: {e}")

    def get_llm(self, use_case: str = 'general') -> ChatOpenAI:
        """
        Get LLM with automatic fallback logic

        Args:
            use_case: Description of use case for logging

        Returns:
            ChatOpenAI instance (primary or fallback)
        """
        # Try primary first
        if self.primary_llm and self.failure_count['primary'] < self.max_retries:
            self.current_model = LLM_CONFIG['primary']['name']
            logger.debug(f" Using primary LLM for {use_case}: {self.current_model}")
            return self.primary_llm

        # Fallback to GLM
        if self.fallback_llm:
            self.current_model = LLM_CONFIG['fallback']['name']
            logger.info(f" Using fallback LLM for {use_case}: {self.current_model}")
            return self.fallback_llm

        # No LLM available
        logger.error(f" No LLM available for {use_case}")
        raise Exception("No LLM configured. Please set OPENAI_API_KEY or GLM_API_KEY in .env")

    def invoke_with_fallback(self, prompt: str, use_case: str = 'general') -> str:
        """
        Invoke LLM with automatic fallback on failure

        Args:
            prompt: The prompt to send to LLM
            use_case: Description of use case

        Returns:
            LLM response content
        """
        # Try primary LLM
        if self.primary_llm and self.failure_count['primary'] < self.max_retries:
            try:
                logger.debug(f"Attempting primary LLM ({LLM_CONFIG['primary']['name']}) for {use_case}")
                response = self.primary_llm.invoke(prompt)

                # Reset failure count on success
                self.failure_count['primary'] = 0
                self.current_model = LLM_CONFIG['primary']['name']

                logger.info(f" Primary LLM success: {use_case}")
                return response.content

            except Exception as e:
                self.failure_count['primary'] += 1
                logger.warning(f" Primary LLM failed ({self.failure_count['primary']}/{self.max_retries}): {e}")
                logger.info(f" Falling back to {LLM_CONFIG['fallback']['name']}")

        # Try fallback LLM
        if self.fallback_llm:
            try:
                logger.debug(f"Attempting fallback LLM ({LLM_CONFIG['fallback']['name']}) for {use_case}")
                response = self.fallback_llm.invoke(prompt)

                # Reset failure count on success
                self.failure_count['fallback'] = 0
                self.current_model = LLM_CONFIG['fallback']['name']

                logger.info(f" Fallback LLM success: {use_case}")
                return response.content

            except Exception as e:
                self.failure_count['fallback'] += 1
                logger.error(f" Fallback LLM also failed ({self.failure_count['fallback']}/{self.max_retries}): {e}")
                raise Exception(f"Both primary and fallback LLMs failed for {use_case}")

        # No LLM available
        raise Exception("No LLM configured or all LLMs failed")

    def get_current_model_name(self) -> str:
        """Get name of currently active model"""
        return self.current_model or "None"

    def reset_failure_counts(self):
        """Reset failure counts (useful for testing)"""
        self.failure_count = {'primary': 0, 'fallback': 0}
        logger.info(" Failure counts reset")

    def get_status(self) -> Dict[str, Any]:
        """Get status of LLM manager"""
        return {
            'primary_available': self.primary_llm is not None,
            'fallback_available': self.fallback_llm is not None,
            'current_model': self.current_model,
            'primary_failures': self.failure_count['primary'],
            'fallback_failures': self.failure_count['fallback'],
            'primary_name': LLM_CONFIG['primary']['name'],
            'fallback_name': LLM_CONFIG['fallback']['name']
        }

# Global instance
llm_manager = LLMManager()

# Convenience functions
def get_llm(use_case: str = 'general') -> ChatOpenAI:
    """Get LLM instance with fallback"""
    return llm_manager.get_llm(use_case)

def invoke_llm(prompt: str, use_case: str = 'general') -> str:
    """Invoke LLM with automatic fallback"""
    return llm_manager.invoke_with_fallback(prompt, use_case)

def get_llm_status() -> Dict[str, Any]:
    """Get LLM manager status"""
    return llm_manager.get_status()

def reset_llm_failures():
    """Reset LLM failure counts"""
    llm_manager.reset_failure_counts()

# Print initialization status
if __name__ != "__main__":
    status = llm_manager.get_status()
    logger.info("=" * 60)
    logger.info("LLM Configuration Loaded")
    logger.info(f"Primary: {status['primary_name']} - {' Available' if status['primary_available'] else ' Not Available'}")
    logger.info(f"Fallback: {status['fallback_name']} - {' Available' if status['fallback_available'] else ' Not Available'}")
    logger.info("=" * 60)
