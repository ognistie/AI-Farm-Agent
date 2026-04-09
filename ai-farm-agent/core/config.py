"""
Config — Sistema de configuração centralizado.
Carrega de config.yaml e expõe como objeto acessível.
Todas as constantes hardcoded do projeto vivem aqui.
"""

import os
import logging
from pathlib import Path

logger = logging.getLogger("config")

# ══════════════════════════════════════════
#  Defaults (usados se config.yaml não existir)
# ══════════════════════════════════════════

DEFAULTS = {
    # Modelos por tipo de tarefa
    "models": {
        "fast": "claude-haiku-4-5-20251001",      # Routing, data, web, files
        "strong": "claude-sonnet-4-20250514",      # Code, desktop, vision, retry
    },

    # Limites
    "limits": {
        "max_task_length": 2000,
        "max_steps_per_agent": 10,
        "max_subtasks": 5,
        "task_timeout_seconds": 120,
        "max_retries": 3,
        "max_tokens_fast": 1500,
        "max_tokens_strong": 2500,
    },

    # Server
    "server": {
        "host": "127.0.0.1",
        "port": 5000,
        "allowed_origins": "http://127.0.0.1:5000",
    },

    # Interaction Layer
    "interaction": {
        "uia_timeout": 5,
        "uia_cache_seconds": 5,
        "vision_confidence_min": 0.15,
        "taskbar_margin_px": 60,
        "screenshot_max_width": 1280,
    },

    # Wait Engine
    "waits": {
        "window_timeout": 15,
        "element_timeout": 10,
        "ocr_interval": 1.0,
        "poll_interval": 0.5,
    },

    # OCR
    "ocr": {
        "languages": ["pt", "en"],
        "gpu": False,
        "confidence_min": 0.5,
    },

    # Paths
    "paths": {
        "captures_dir": "captures",
        "reports_dir": "reports",
        "logs_dir": "logs",
        "workflows_dir": "memory/workflows",
        "state_maps_dir": "state_maps",
    },

    # Agentes → modelos
    "agent_models": {
        "maestro": "fast",
        "vision_maestro": "fast",
        "data": "fast",
        "web": "fast",
        "code": "strong",
        "desktop": "strong",
        "file": "fast",
        "memory": "fast",
    },

    # Segurança
    "security": {
        "blocked_commands": [
            "rm -rf", "rmdir /s", "format c", "del /f /s",
            "shutdown", "reg delete", "diskpart", "bcdedit",
        ],
    },
}

# ══════════════════════════════════════════
#  Config class
# ══════════════════════════════════════════

_config = None


def get_config():
    """Retorna a instância de configuração (singleton)."""
    global _config
    if _config is None:
        _config = Config()
    return _config


class Config:
    """Configuração centralizada do AI Farm Agent."""

    def __init__(self):
        self._data = {}
        self._load()

    def _load(self):
        """Carrega config: YAML > defaults."""
        # Começa com defaults
        self._data = _deep_copy(DEFAULTS)

        # Tenta carregar config.yaml
        config_path = self._find_config_file()
        if config_path:
            try:
                import yaml
                with open(config_path, "r", encoding="utf-8") as f:
                    user_config = yaml.safe_load(f) or {}
                self._data = _deep_merge(self._data, user_config)
                logger.info(f"Config carregada de {config_path}")
            except ImportError:
                logger.info("PyYAML não instalado, usando defaults")
            except Exception as e:
                logger.warning(f"Erro ao carregar config: {e}, usando defaults")
        else:
            logger.info("config.yaml não encontrado, usando defaults")

    def _find_config_file(self):
        """Procura config.yaml no projeto."""
        candidates = [
            Path("config.yaml"),
            Path("config.yml"),
            Path(__file__).parent.parent / "config.yaml",
            Path(__file__).parent.parent / "config.yml",
        ]
        for p in candidates:
            if p.exists():
                return p
        return None

    # ── Accessors ──

    def get(self, key_path, default=None):
        """
        Acessa valor por caminho pontilhado.
        Ex: config.get("models.fast") → "claude-haiku-4-5-20251001"
        """
        keys = key_path.split(".")
        val = self._data
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            else:
                return default
        return val

    def get_model(self, agent_name):
        """Retorna o modelo configurado para um agente."""
        model_type = self.get(f"agent_models.{agent_name.lower()}", "fast")
        return self.get(f"models.{model_type}", DEFAULTS["models"]["fast"])

    @property
    def models(self):
        return self._data.get("models", {})

    @property
    def limits(self):
        return self._data.get("limits", {})

    @property
    def server(self):
        return self._data.get("server", {})

    @property
    def paths(self):
        return self._data.get("paths", {})

    @property
    def security(self):
        return self._data.get("security", {})

    def __repr__(self):
        return f"Config({list(self._data.keys())})"


# ══════════════════════════════════════════
#  Helpers
# ══════════════════════════════════════════

def _deep_copy(d):
    """Deep copy de dict (sem import copy)."""
    if isinstance(d, dict):
        return {k: _deep_copy(v) for k, v in d.items()}
    if isinstance(d, list):
        return [_deep_copy(i) for i in d]
    return d


def _deep_merge(base, override):
    """Merge profundo: override sobrescreve base, recursivamente."""
    result = _deep_copy(base)
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = _deep_copy(v)
    return result
