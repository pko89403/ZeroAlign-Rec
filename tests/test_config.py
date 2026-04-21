from sid_reco.config import (
    DATA_DIR,
    DEFAULT_EMBED_MODEL,
    DEFAULT_LLM_BACKEND,
    DEFAULT_LLM_MAX_TOKENS,
    DEFAULT_LLM_MODEL,
    DEFAULT_LLM_TEMPERATURE,
    DEFAULT_LLM_TOP_P,
    SID_CACHE_DIR,
    Settings,
    ensure_project_directories,
)


def test_settings_default_paths(monkeypatch) -> None:
    monkeypatch.delenv("SID_RECO_CATALOG_PATH", raising=False)
    monkeypatch.delenv("SID_RECO_CACHE_DIR", raising=False)

    settings = Settings.from_env()

    assert settings.llm_backend == DEFAULT_LLM_BACKEND
    assert settings.llm_model == DEFAULT_LLM_MODEL
    assert settings.embed_model == DEFAULT_EMBED_MODEL
    assert settings.sid_catalog_path == DATA_DIR / "catalog.csv"
    assert settings.sid_cache_dir == SID_CACHE_DIR
    assert settings.llm_max_tokens == DEFAULT_LLM_MAX_TOKENS
    assert settings.llm_temperature == DEFAULT_LLM_TEMPERATURE
    assert settings.llm_top_p == DEFAULT_LLM_TOP_P


def test_directories_exist_after_bootstrap() -> None:
    ensure_project_directories()

    assert DATA_DIR.exists()
    assert SID_CACHE_DIR.exists()


def test_relative_env_paths_resolve_from_project_root(monkeypatch) -> None:
    monkeypatch.setenv("SID_RECO_CATALOG_PATH", "data/custom.csv")
    monkeypatch.setenv("SID_RECO_CACHE_DIR", "data/custom_cache")

    settings = Settings.from_env()

    assert settings.sid_catalog_path == DATA_DIR / "custom.csv"
    assert settings.sid_cache_dir == DATA_DIR / "custom_cache"
