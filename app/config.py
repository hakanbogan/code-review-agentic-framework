"""Configuration management using Pydantic Settings."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from domain import LLMProvider


def _find_project_root() -> Path:
    """Find project root directory by looking for .env file or pyproject.toml."""
    current = Path(__file__).resolve().parent

    # Look for project root markers
    markers = [".env", "pyproject.toml", ".git"]

    # Go up the directory tree
    for parent in [current] + list(current.parents):
        if any((parent / marker).exists() for marker in markers):
            return parent

    # Fallback to current directory
    return Path.cwd()


def _get_env_file_path() -> Path:
    """Get absolute path to .env file."""
    project_root = _find_project_root()
    env_file = project_root / ".env"
    return env_file


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=str(_get_env_file_path()),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # LLM Configuration
    llm_provider: LLMProvider = Field(
        default=LLMProvider.OPENAI,
        description="LLM provider to use"
    )
    openai_api_key: str | None = Field(default=None, description="OpenAI API key")
    openai_model: str = Field(default="gpt-4-turbo", description="OpenAI model")
    openai_temperature: float = Field(default=0.0, ge=0.0, le=2.0, description="LLM temperature")
    openai_seed: int = Field(default=42, description="Seed for deterministic outputs")

    # GitHub Configuration
    github_token: str | None = Field(default=None, description="GitHub personal access token")

    # Alternative providers (optional)
    anthropic_api_key: str | None = Field(default=None, description="Anthropic API key")
    anthropic_model: str = Field(
        default="claude-haiku-4-5-20251001",
        description="Anthropic model"
    )

    # Tool Paths
    ruff_path: str = Field(default="ruff", description="Path to ruff executable")
    eslint_path: str = Field(default="eslint", description="Path to eslint executable")
    semgrep_path: str = Field(default="semgrep", description="Path to semgrep executable")
    bandit_path: str = Field(default="bandit", description="Path to bandit executable")

    # Framework Settings
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level"
    )
    log_format: Literal["json", "text"] = Field(
        default="json",
        description="Log output format"
    )
    artifact_storage: Literal["local", "s3"] = Field(
        default="local",
        description="Artifact storage backend"
    )
    artifact_path: Path = Field(
        default=Path("./artifacts"),
        description="Path for artifact storage"
    )

    # Review Configuration
    max_nits_per_review: int = Field(
        default=5,
        ge=0,
        description="Maximum nit-level findings per review"
    )
    max_patch_lines: int = Field(
        default=10,
        ge=1,
        description="Maximum lines in auto-generated patches"
    )
    enable_parallel_agents: bool = Field(
        default=True,
        description="Enable parallel agent execution"
    )

    # Review Storage Settings
    reviews_path: Path = Field(
        default=Path("./reviews"),
        description="Path to store review results"
    )

    # Evaluation Settings
    eval_dataset_path: Path = Field(
        default=Path("./eval/dataset"),
        description="Path to evaluation dataset"
    )
    eval_results_path: Path = Field(
        default=Path("./eval/results"),
        description="Path to store evaluation results"
    )
    seed_for_experiments: int = Field(
        default=42,
        description="Seed for reproducible experiments"
    )

    # S3 Configuration (if artifact_storage == "s3")
    aws_access_key_id: str | None = Field(default=None, description="AWS access key")
    aws_secret_access_key: str | None = Field(default=None, description="AWS secret key")
    s3_bucket_name: str | None = Field(default=None, description="S3 bucket name")
    s3_region: str = Field(default="us-east-1", description="S3 region")

    # Prompt Configuration
    prompt_base_path: Path = Field(
        default=Path("./prompts"),
        description="Base path for prompt templates"
    )
    default_prompt_version: str = Field(
        default="v1",
        description="Default prompt version to use"
    )

    @field_validator("artifact_path", "eval_dataset_path", "eval_results_path", "prompt_base_path", "reviews_path")
    @classmethod
    def create_paths(cls, v: Path) -> Path:
        """Ensure paths exist."""
        v.mkdir(parents=True, exist_ok=True)
        return v

    @field_validator("artifact_storage")
    @classmethod
    def validate_s3_config(cls, v: str, info: any) -> str:
        """Validate S3 configuration if S3 storage is selected."""
        if v == "s3":
            values = info.data
            required_fields = ["aws_access_key_id", "aws_secret_access_key", "s3_bucket_name"]
            missing = [f for f in required_fields if not values.get(f)]
            if missing:
                raise ValueError(
                    f"S3 storage requires: {', '.join(missing)}"
                )
        return v

    @model_validator(mode="after")
    def validate_llm_provider_config(self) -> "Settings":
        """Validate that the appropriate API key exists for the selected provider."""
        if self.llm_provider == LLMProvider.OPENAI and not self.openai_api_key:
            raise ValueError("OpenAI provider requires OPENAI_API_KEY")
        if self.llm_provider == LLMProvider.ANTHROPIC and not self.anthropic_api_key:
            raise ValueError("Anthropic provider requires ANTHROPIC_API_KEY")
        return self

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return True  # Single environment as requested

    def get_prompt_path(self, agent_role: str, version: str | None = None) -> Path:
        """Get path to prompt file for an agent."""
        version = version or self.default_prompt_version
        return self.prompt_base_path / agent_role.lower() / f"{version}.md"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    import os

    settings = Settings()

    # Set API keys as environment variables for CrewAI compatibility
    # CrewAI checks environment variable even when LLM object is provided
    if settings.openai_api_key:
        os.environ["OPENAI_API_KEY"] = settings.openai_api_key
    if settings.anthropic_api_key:
        os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key

    return settings
