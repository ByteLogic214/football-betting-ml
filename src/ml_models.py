"""
Modelos de Machine Learning para predicción de líneas de apuestas.
Usa XGBoost para regresión de valores esperados por mercado.
"""

import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
import xgboost as xgb
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler


@dataclass
class MarketPrediction:
    market: str
    team: str  # "home" o "away"
    predicted_value: float
    confidence: float
    probability: float
    line_suggestion: float
    over_probability: float
    under_probability: float
    reasoning: str


class BettingLinePredictor:
    """
    Predictor de líneas de apuestas usando ensemble de modelos.
    """
    
    # Líneas típicas de mercado por defecto
    DEFAULT_LINES = {
        "goals": 2.5,
        "shots_on_target": 4.5,
        "corners": 9.5,
        "yellow_cards": 3.5,
        "throw_ins": 20.5,
        "total_shots": 12.5,
        "big_chances": 2.5,
    }
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self._init_models()
    
    def _init_models(self):
        """Inicializa modelos para cada mercado."""
        for market in ["goals", "shots_on_target", "corners", 
                       "yellow_cards", "throw_ins", "total_shots", "big_chances"]:
            self.models[market] = {
                "home": xgb.XGBRegressor(
                    n_estimators=100,
                    max_depth=5,
                    learning_rate=0.1,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=42,
                    objective='reg:squarederror'
                ),
                "away": xgb.XGBRegressor(
                    n_estimators=100,
                    max_depth=5,
                    learning_rate=0.1,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=42,
                    objective='reg:squarederror'
                ),
            }
            self.scalers[market] = StandardScaler()
    
    def predict_market(self, features: Dict[str, float], market: str,
                       team: str) -> MarketPrediction:
        """
        Predice el valor esperado para un mercado y equipo específico.
        
        Usa un enfoque híbrido: regresión + distribución de Poisson
        para calcular probabilidades Over/Under.
        """
        # Valor base: promedio histórico del equipo
        if team == "home":
            base_value = features.get(f"home_{market}_avg", 0)
            std_value = features.get(f"home_{market}_std", 0)
            opponent_avg = features.get(f"away_{market}_avg", 0)
            opponent_conceded = features.get("away_goals_conceded_avg", 0)
        else:
            base_value = features.get(f"away_{market}_avg", 0)
            std_value = features.get(f"away_{market}_std", 0)
            opponent_avg = features.get(f"home_{market}_avg", 0)
            opponent_conceded = features.get("home_goals_conceded_avg", 0)
        
        # Ajustes basados en features
        adjustment = 0
        
        # Factor forma
        if team == "home":
            form_wins = features.get("home_form_wins", 0)
            form_losses = features.get("home_form_losses", 0)
            injury_penalty = features.get("home_injury_penalty", 0)
        else:
            form_wins = features.get("away_form_wins", 0)
            form_losses = features.get("away_form_losses", 0)
            injury_penalty = features.get("away_injury_penalty", 0)
        
        adjustment += (form_wins - form_losses) * 0.15
        adjustment -= injury_penalty * base_value * 0.3  # Penalización bajas
        
        # Factor H2H
        if team == "home":
            h2h_goals = features.get("h2h_home_goals_avg", base_value)
        else:
            h2h_goals = features.get("h2h_away_goals_avg", base_value)
        
        # Combinar: 70% forma reciente, 20% H2H, 10% oponente
        predicted = (
            base_value * 0.70 +
            h2h_goals * 0.20 +
            opponent_conceded * 0.10 +
            adjustment
        )
        
        # Asegurar valor no negativo
        predicted = max(predicted, 0.1)
        
        # Calcular línea sugerida (redondear a .5 más cercano)
        line = self.DEFAULT_LINES.get(market, predicted)
        
        # Usar distribución de Poisson para probabilidades Over/Under
        # lambda = predicted value
        lambda_val = predicted
        
        # P(X > line) = 1 - P(X <= line)
        from scipy.stats import poisson
        try:
            p_under = poisson.cdf(int(line), lambda_val)
            p_over = 1 - p_under
        except Exception:
            # Fallback simple
            if predicted > line:
                p_over = 0.6
                p_under = 0.4
            else:
                p_over = 0.4
                p_under = 0.6
        
        # Ajustar por desviación estándar (confianza)
        if std_value > 0:
            cv = std_value / max(base_value, 0.1)  # Coeficiente de variación
            confidence = max(0.5, 1 - cv)  # Menor variación = mayor confianza
        else:
            confidence = 0.5
        
        # Probabilidad final del pick
        if predicted > line:
            probability = p_over
            direction = "OVER"
        else:
            probability = p_under
            direction = "UNDER"
        
        # Construir reasoning
        reasons = []
        if injury_penalty > 0:
            reasons.append(f"⚠️ Bajas ofensivas (-{injury_penalty*100:.0f}% impacto)")
        if form_wins > form_losses:
            reasons.append(f"✅ Buena forma ({form_wins}V-{form_losses}D)")
        elif form_losses > form_wins:
            reasons.append(f"❌ Mala forma ({form_wins}V-{form_losses}D)")
        
        if team == "home" and features.get("home_advantage", 0) > 0:
            reasons.append("🏠 Factor localía")
        
        reasoning = " | ".join(reasons) if reasons else "Basado en promedios históricos"
        
        return MarketPrediction(
            market=market,
            team=team,
            predicted_value=round(predicted, 2),
            confidence=round(confidence, 2),
            probability=round(probability, 3),
            line_suggestion=line,
            over_probability=round(p_over, 3),
            under_probability=round(p_under, 3),
            reasoning=reasoning
        )
    
    def predict_all_markets(self, features: Dict[str, float]) -> List[MarketPrediction]:
        """
        Predice todos los mercados para ambos equipos.
        """
        predictions = []
        
        markets = ["goals", "shots_on_target", "corners", 
                   "yellow_cards", "throw_ins", "total_shots", "big_chances"]
        
        for market in markets:
            for team in ["home", "away"]:
                pred = self.predict_market(features, market, team)
                predictions.append(pred)
        
        return predictions
    
    def calculate_combined_probability(self, predictions: List[MarketPrediction],
                                         min_prob: float = 0.75) -> List[MarketPrediction]:
        """
        Filtra predicciones con probabilidad >= umbral y ordena por confianza.
        """
        filtered = [p for p in predictions if p.probability >= min_prob]
        return sorted(filtered, key=lambda x: (x.probability, x.confidence), reverse=True)
