import yaml
from pathlib import Path
from typing import Any, Dict


class Settings:
    """
    Load and manage centralized settings from YAML.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Settings, cls).__new__(cls)
            cls._instance._load_settings()
        return cls._instance

    def _load_settings(self):
        config_path = Path("config/settings.yaml")
        if not config_path.exists():
            config_path = Path(__file__).parent.parent / "config" / "settings.yaml"

        with open(config_path, "r", encoding="utf-8") as f:
            self._data = yaml.safe_load(f)

    def get(self, key_path: str, default: Any = None) -> Any:
        keys = key_path.split(".")
        val = self._data
        try:
            for k in keys:
                val = val[k]
            return val
        except (KeyError, TypeError):
            return default


settings = Settings()
