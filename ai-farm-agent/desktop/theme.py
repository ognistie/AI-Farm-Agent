"""
Tokens visuais do AI Farm Agent Desktop.

Herda o DNA do projeto antigo (acento verde 'Matrix', glifo hexagonal,
mono font para terminal) mas troca a paleta CRT/scanline por superficies
neutras estilo macOS Sonoma com vibrancy.

Estes tokens sao expostos ao QML via context property `Theme` em
`desktop/main.py`. Mude aqui e a UI inteira segue.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class Palette:
    # Superficies — preto profundo + vidro fume (estetica Claude/Lanes.sh)
    bg_base:        str = "#0A0A0B"
    bg_sidebar:     str = "#0C0D0F"
    bg_topbar:      str = "#0A0A0B"
    bg_surface:     str = "#121316"
    bg_surface_hi:  str = "#191B1F"
    bg_input:       str = "#0E0F11"
    hairline:       str = "#1C1E22"
    hairline_hi:    str = "#26292E"

    # Texto off-white
    text_primary:   str = "#EDEEF0"
    text_secondary: str = "#8B8E96"
    text_muted:     str = "#56595F"
    text_inverse:   str = "#0A0A0B"

    # Acentos (teal vibrante + roxo sutil)
    accent:         str = "#2dd4bf"
    accent_dim:     str = "#0f766e"
    cyan:           str = "#2dd4bf"
    coral:          str = "#f87171"
    amber:          str = "#fbbf24"
    violet:         str = "#a78bfa"
    info:           str = "#7dd3fc"

    # Status semantico
    status_online:  str = "#2dd4bf"
    status_idle:    str = "#56595F"
    status_running: str = "#a78bfa"
    status_waiting: str = "#fbbf24"
    status_error:   str = "#f87171"

    # Agentes (cores estaveis)
    agent_maestro:  str = "#a78bfa"
    agent_code:     str = "#2dd4bf"
    agent_data:     str = "#7dd3fc"
    agent_web:      str = "#22d3ee"
    agent_desktop:  str = "#fbbf24"
    agent_file:     str = "#fb923c"
    agent_vision:   str = "#f87171"
    agent_memory:   str = "#8B8E96"


@dataclass(frozen=True)
class Typography:
    font_sans:  str = "Inter"
    font_mono:  str = "JetBrains Mono"
    font_brand: str = "Inter"  # caps + tracking para titulos

    size_xs:    int = 11
    size_sm:    int = 12
    size_md:    int = 13
    size_lg:    int = 15
    size_xl:    int = 18
    size_xxl:   int = 24
    size_brand: int = 32

    weight_regular: int = 400
    weight_medium:  int = 500
    weight_semi:    int = 600
    weight_bold:    int = 700


@dataclass(frozen=True)
class Spacing:
    xxs:    int = 2
    xs:     int = 4
    sm:     int = 8
    md:     int = 12
    lg:     int = 16
    xl:     int = 24
    xxl:    int = 32

    radius_sm:  int = 6
    radius_md:  int = 10
    radius_lg:  int = 14
    radius_pill: int = 999


@dataclass(frozen=True)
class Motion:
    dur_fast:    int = 120
    dur_normal:  int = 220
    dur_slow:    int = 420
    easing:      str = "OutCubic"


# Singleton acessivel via context property no QML como `Theme`.
PALETTE = Palette()
TYPO = Typography()
SPACING = Spacing()
MOTION = Motion()


def as_qml_dict() -> dict:
    """Achata todos os tokens em um unico dict para o QML."""
    out: dict = {}
    out.update(asdict(PALETTE))
    for k, v in asdict(TYPO).items():
        out[f"typo_{k}"] = v
    for k, v in asdict(SPACING).items():
        out[f"sp_{k}"] = v
    for k, v in asdict(MOTION).items():
        out[f"motion_{k}"] = v
    return out


def agent_color(agent_name: str) -> str:
    """Cor estavel por agente (para faixas laterais nos logs)."""
    name = (agent_name or "").upper()
    mapping = {
        "MAESTRO":  PALETTE.agent_maestro,
        "CODE":     PALETTE.agent_code,
        "DATA":     PALETTE.agent_data,
        "WEB":      PALETTE.agent_web,
        "DESKTOP":  PALETTE.agent_desktop,
        "FILE":     PALETTE.agent_file,
        "VISION":   PALETTE.agent_vision,
        "MEMORY":   PALETTE.agent_memory,
    }
    return mapping.get(name, PALETTE.text_secondary)


def level_color(level: str) -> str:
    """Cor por nivel de log."""
    lvl = (level or "").upper()
    return {
        "ERROR":   PALETTE.coral,
        "WARN":    PALETTE.amber,
        "WARNING": PALETTE.amber,
        "INFO":    PALETTE.info,
        "SUCCESS": PALETTE.accent,
        "DEBUG":   PALETTE.text_muted,
    }.get(lvl, PALETTE.text_secondary)


def status_color(status: str) -> str:
    """Cor por status de agente."""
    s = (status or "").lower()
    return {
        "online":  PALETTE.status_online,
        "running": PALETTE.status_running,
        "waiting": PALETTE.status_waiting,
        "error":   PALETTE.status_error,
        "idle":    PALETTE.status_idle,
    }.get(s, PALETTE.text_muted)
