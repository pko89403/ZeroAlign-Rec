"""Project-level configuration helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
SID_CACHE_DIR = ARTIFACTS_DIR / "sid_cache"
DEFAULT_LLM_BACKEND = "mlx"
DEFAULT_LLM_MODEL = "mlx-community/Qwen3.5-9B-OptiQ-4bit"
DEFAULT_EMBED_MODEL = "mlx-community/Qwen3-Embedding-4B-4bit-DWQ"
DEFAULT_LLM_MAX_TOKENS = 256
DEFAULT_LLM_TEMPERATURE = 0.0
DEFAULT_LLM_TOP_P = 1.0

load_dotenv(PROJECT_ROOT / ".env", override=False)


@dataclass(frozen=True, slots=True)
class Settings:
    """Runtime settings resolved from the environment."""

    project_root: Path
    llm_backend: str
    llm_model: str
    embed_model: str
    sid_catalog_path: Path
    sid_cache_dir: Path
    llm_max_tokens: int
    llm_temperature: float
    llm_top_p: float

    @classmethod
    def from_env(cls) -> Settings:
        catalog_path = _resolve_project_path(
            os.getenv("SID_RECO_CATALOG_PATH"),
            DATA_DIR / "catalog.csv",
        )
        cache_dir = _resolve_project_path(
            os.getenv("SID_RECO_CACHE_DIR"),
            SID_CACHE_DIR,
        )
        return cls(
            project_root=PROJECT_ROOT,
            llm_backend=os.getenv("SID_RECO_LLM_BACKEND", DEFAULT_LLM_BACKEND),
            llm_model=os.getenv("SID_RECO_LLM_MODEL", DEFAULT_LLM_MODEL),
            embed_model=os.getenv("SID_RECO_EMBED_MODEL", DEFAULT_EMBED_MODEL),
            sid_catalog_path=catalog_path,
            sid_cache_dir=cache_dir,
            llm_max_tokens=int(os.getenv("SID_RECO_LLM_MAX_TOKENS", DEFAULT_LLM_MAX_TOKENS)),
            llm_temperature=float(
                os.getenv("SID_RECO_LLM_TEMPERATURE", DEFAULT_LLM_TEMPERATURE),
            ),
            llm_top_p=float(os.getenv("SID_RECO_LLM_TOP_P", DEFAULT_LLM_TOP_P)),
        )


def ensure_project_directories() -> None:
    """Create default directories used by the local workflow."""
    for path in (DATA_DIR, ARTIFACTS_DIR, SID_CACHE_DIR):
        path.mkdir(parents=True, exist_ok=True)


def _resolve_project_path(raw_value: str | None, default_path: Path) -> Path:
    """Resolve relative paths against the project root."""
    if raw_value is None:
        return default_path

    candidate = Path(raw_value)
    if candidate.is_absolute():
        return candidate
    return PROJECT_ROOT / candidate
