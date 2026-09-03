"""
Configuración centralizada del sistema de predicciones de fútbol.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    # TheStatsAPI
    STATS_API_BASE: str = "https://api.thestatsapi.com/api"
    STATS_API_KEY: str = ""
    
    # SharpAPI
    SHARP_API_BASE: str = "https://api.sharpapi.io/api/v1"
    SHARP_API_KEY: str = ""
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    
    # Parámetros del modelo
    MIN_PROBABILITY: float = 0.75
    TOP_N_MATCHES: int = 10
    RECENT_MATCHES_COUNT: int = 5
    
    # Filtro de competición (opcional)
    COMPETITION_FILTER: str = ""
    
    # Mercados a analizar
    MARKETS = [
        "shots_on_target",
        "corners",
        "goals",
        "yellow_cards",
        "throw_ins",
        "total_shots",
        "fouls",
        "big_chances",
    ]
    
    @classmethod
    def from_env(cls) -> "Config":
        """Carga configuración desde variables de entorno."""
        return cls(
            STATS_API_KEY=os.getenv("STATS_API_KEY", ""),
            SHARP_API_KEY=os.getenv("SHARP_API_KEY", ""),
            TELEGRAM_BOT_TOKEN=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            TELEGRAM_CHAT_ID=os.getenv("TELEGRAM_CHAT_ID", ""),
            COMPETITION_FILTER=os.getenv("COMPETITION_FILTER", ""),
        )
    
    def validate(self) -> None:
        """Valida que las claves esenciales estén configuradas."""
        missing = []
        if not self.STATS_API_KEY:
            missing.append("STATS_API_KEY")
        if not self.SHARP_API_KEY:
            missing.append("SHARP_API_KEY")
        if not self.TELEGRAM_BOT_TOKEN:
            missing.append("TELEGRAM_BOT_TOKEN")
        if not self.TELEGRAM_CHAT_ID:
            missing.append("TELEGRAM_CHAT_ID")
        
        if missing:
            raise ValueError(f"Faltan variables de entorno: {', '.join(missing)}")
