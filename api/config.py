"""Configuration settings for FireRedASR API."""

from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ASR Model Configuration
    asr_type: str = "llm"  # "aed" or "llm"
    model_dir: str = "pretrained_models/FireRedASR-LLM-L"
    device: str = "cuda"  # "cuda" or "cpu"

    # Audio Constraints
    max_audio_duration: int = 30  # seconds
    max_batch_size: int = 8

    # Default Decoding Parameters
    default_beam_size: int = 3
    default_repetition_penalty: float = 3.0
    default_decode_max_len: int = 0
    default_decode_min_len: int = 0
    default_temperature: float = 1.0
    default_llm_length_penalty: float = 0.0

    # AED-specific defaults
    default_nbest: int = 1
    default_softmax_smoothing: float = 1.0
    default_aed_length_penalty: float = 0.0
    default_eos_penalty: float = 1.0

    # API Authentication
    api_keys: str = ""  # Comma-separated API keys

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    timeout_keep_alive: int = 300

    @property
    def valid_api_keys(self) -> List[str]:
        """Parse comma-separated API keys into a list."""
        if not self.api_keys:
            return []
        return [key.strip() for key in self.api_keys.split(",") if key.strip()]

    @property
    def use_gpu(self) -> bool:
        """Check if GPU should be used."""
        return self.device == "cuda"

    class Config:
        env_prefix = ""
        env_file = ".env"
        extra = "ignore"


# Global settings instance
settings = Settings()
