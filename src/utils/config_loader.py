"""Configuration loader utility."""
import yaml
from pathlib import Path
from typing import Dict, Any


class Config:
    """Configuration manager for NATO Asset Codifier."""

    def __init__(self, config_path: str = None):
        if config_path is None:
            # Default to config/config.yaml
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config" / "config.yaml"

        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.project_root = Path(__file__).parent.parent.parent

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)

    def get(self, key: str, default=None):
        """Get configuration value by key (supports nested keys with dots)."""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default

    def get_path(self, key: str) -> Path:
        """Get path relative to project root."""
        path_str = self.get(key)
        if path_str:
            return self.project_root / path_str
        return None

    @property
    def ollama_host(self) -> str:
        return self.get('ollama.host')

    @property
    def ollama_model(self) -> str:
        return self.get('ollama.model')

    @property
    def embedding_model(self) -> str:
        return self.get('ollama.embedding_model')

    @property
    def embedding_dim(self) -> int:
        return self.get('embedding.dimension', 768)

    @property
    def top_k(self) -> int:
        return self.get('retrieval.top_k', 5)

    @property
    def similarity_threshold(self) -> float:
        return self.get('retrieval.similarity_threshold', 0.6)


# Global config instance
_config = None

def get_config(config_path: str = None) -> Config:
    """Get or create global config instance."""
    global _config
    if _config is None:
        _config = Config(config_path)
    return _config
