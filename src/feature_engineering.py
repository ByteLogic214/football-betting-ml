"""
Ingeniería de features: transforma datos crudos en vectores numéricos
para los modelos de ML.
"""

import numpy as np
from typing import Dict, List, Any, Tuple
from src.config import Config


class FeatureEngineer:
    def __init__(self, config: Config):
        self.config = config
    
    def extract_features(self, match_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Extrae todas las features numéricas de un partido.
        Retorna un diccionario con features por mercado.
        """
        home = match_data["home_recent"]
        away = match_data["away_recent"]
        h2h = match_data["h2h"]
        
        features = {}
        
        # === FORMA RECIENTE ===
        features["home_form_wins"] = home.get("form", "").count("W")
        features["home_form_draws"] = home.get("form", "").count("D")
        features["home_form_losses"] = home.get("form", "").count("L")
        features["away_form_wins"] = away.get("form", "").count("W")
        features["away_form_draws"] = away.get("form", "").count("D")
        features["away_form_losses"] = away.get("form", "").count("L")
        
        # === GOLES ===
        features["home_goals_scored_avg"] = home.get("goals_scored_avg", 0)
        features["home_goals_conceded_avg"] = home.get("goals_conceded_avg", 0)
        features["away_goals_scored_avg"] = away.get("goals_scored_avg", 0)
        features["away_goals_conceded_avg"] = away.get("goals_conceded_avg", 0)
        features["home_goals_scored_std"] = home.get("goals_scored_std", 0)
        features["away_goals_scored_std"] = away.get("goals_scored_std", 0)
        
        # Diferencia de goles
        features["goal_diff_home"] = features["home_goals_scored_avg"] - features["home_goals_conceded_avg"]
        features["goal_diff_away"] = features["away_goals_scored_avg"] - features["away_goals_conceded_avg"]
        features["goal_diff_total"] = features["goal_diff_home"] - features["goal_diff_away"]
        
        # === REMATES AL ARCO ===
        features["home_sot_avg"] = home.get("shots_on_target_avg", 0)
        features["away_sot_avg"] = away.get("shots_on_target_avg", 0)
        features["home_sot_std"] = home.get("shots_on_target_std", 0)
        features["away_sot_std"] = away.get("shots_on_target_std", 0)
        features["home_total_shots_avg"] = home.get("total_shots_avg", 0)
        features["away_total_shots_avg"] = away.get("total_shots_avg", 0)
        
        # Eficiencia de remates
        if features["home_total_shots_avg"] > 0:
            features["home_sot_ratio"] = features["home_sot_avg"] / features["home_total_shots_avg"]
        else:
            features["home_sot_ratio"] = 0
        
        if features["away_total_shots_avg"] > 0:
            features["away_sot_ratio"] = features["away_sot_avg"] / features["away_total_shots_avg"]
        else:
            features["away_sot_ratio"] = 0
        
        # === CORNERS ===
        features["home_corners_avg"] = home.get("corners_avg", 0)
        features["away_corners_avg"] = away.get("corners_avg", 0)
        features["home_corners_std"] = home.get("corners_std", 0)
        features["away_corners_std"] = away.get("corners_std", 0)
        
        # === TARJETAS ===
        features["home_yellow_avg"] = home.get("yellow_cards_avg", 0)
        features["away_yellow_avg"] = away.get("yellow_cards_avg", 0)
        features["home_fouls_avg"] = home.get("fouls_avg", 0)
        features["away_fouls_avg"] = away.get("fouls_avg", 0)
        
        # === SAQUES DE BANDA ===
        features["home_throw_ins_avg"] = home.get("throw_ins_avg", 0)
        features["away_throw_ins_avg"] = away.get("throw_ins_avg", 0)
        
        # === GRANDES OCASIONES ===
        features["home_big_chances_avg"] = home.get("big_chances_avg", 0)
        features["away_big_chances_avg"] = away.get("big_chances_avg", 0)
        
        # === xG ===
        features["home_xg_avg"] = home.get("xg_avg", 0)
        features["away_xg_avg"] = away.get("xg_avg", 0)
        
        # === POSESIÓN ===
        features["home_possession_avg"] = home.get("ball_possession_avg", 0)
        features["away_possession_avg"] = away.get("ball_possession_avg", 0)
        
        # === H2H ===
        features["h2h_home_wins"] = h2h.get("team_a_wins", 0)
        features["h2h_away_wins"] = h2h.get("team_b_wins", 0)
        features["h2h_draws"] = h2h.get("draws", 0)
        features["h2h_home_goals_avg"] = h2h.get("team_a_goals_avg", 0)
        features["h2h_away_goals_avg"] = h2h.get("team_b_goals_avg", 0)
        features["h2h_over_2_5_rate"] = h2h.get("over_2_5_goals", 0) / max(h2h.get("matches_analyzed", 1), 1)
        features["h2h_btts_rate"] = h2h.get("btts_yes", 0) / max(h2h.get("matches_analyzed", 1), 1)
        
        # === BAJAS (IMPACTO OFENSIVO) ===
        home_inj = match_data.get("home_injuries", {})
        away_inj = match_data.get("away_injuries", {})
        
        features["home_missing_attackers"] = len(home_inj.get("missing_attackers", []))
        features["away_missing_attackers"] = len(away_inj.get("missing_attackers", []))
        features["home_missing_midfielders"] = len(home_inj.get("missing_midfielders", []))
        features["away_missing_midfielders"] = len(away_inj.get("missing_midfielders", []))
        
        # Penalización por bajas ofensivas (0-1)
        features["home_injury_penalty"] = min(
            (features["home_missing_attackers"] * 0.25 + 
             features["home_missing_midfielders"] * 0.15), 1.0
        )
        features["away_injury_penalty"] = min(
            (features["away_missing_attackers"] * 0.25 + 
             features["away_missing_midfielders"] * 0.15), 1.0
        )
        
        # === ESTADÍSTICAS DE TEMPORADA ===
        home_season = match_data.get("home_season", {})
        away_season = match_data.get("away_season", {})
        
        features["home_season_position"] = home_season.get("position", 10)
        features["away_season_position"] = away_season.get("position", 10)
        features["home_season_gf"] = home_season.get("goals_for", 0)
        features["away_season_gf"] = away_season.get("goals_for", 0)
        features["home_season_ga"] = home_season.get("goals_against", 0)
        features["away_season_ga"] = away_season.get("goals_against", 0)
        
        # Factor localía
        features["home_advantage"] = 1.0
        
        return features
    
    def get_market_features(self, features: Dict[str, float], 
                           market: str) -> List[float]:
        """
        Selecciona las features relevantes para un mercado específico.
        """
        market_feature_map = {
            "goals": [
                "home_goals_scored_avg", "home_goals_conceded_avg",
                "away_goals_scored_avg", "away_goals_conceded_avg",
                "goal_diff_home", "goal_diff_away", "goal_diff_total",
                "home_xg_avg", "away_xg_avg",
                "h2h_home_goals_avg", "h2h_away_goals_avg",
                "h2h_over_2_5_rate", "h2h_btts_rate",
                "home_injury_penalty", "away_injury_penalty",
                "home_big_chances_avg", "away_big_chances_avg",
                "home_form_wins", "away_form_wins",
                "home_advantage",
            ],
            "shots_on_target": [
                "home_sot_avg", "away_sot_avg",
                "home_sot_std", "away_sot_std",
                "home_total_shots_avg", "away_total_shots_avg",
                "home_sot_ratio", "away_sot_ratio",
                "home_possession_avg", "away_possession_avg",
                "home_xg_avg", "away_xg_avg",
                "home_big_chances_avg", "away_big_chances_avg",
                "home_injury_penalty", "away_injury_penalty",
                "home_form_wins", "away_form_wins",
                "home_advantage",
            ],
            "corners": [
                "home_corners_avg", "away_corners_avg",
                "home_corners_std", "away_corners_std",
                "home_possession_avg", "away_possession_avg",
                "home_total_shots_avg", "away_total_shots_avg",
                "home_sot_avg", "away_sot_avg",
                "home_form_wins", "away_form_wins",
                "home_advantage",
            ],
            "yellow_cards": [
                "home_yellow_avg", "away_yellow_avg",
                "home_fouls_avg", "away_fouls_avg",
                "h2h_home_wins", "h2h_away_wins",
                "home_form_wins", "away_form_wins",
                "home_injury_penalty", "away_injury_penalty",
                "home_advantage",
            ],
            "throw_ins": [
                "home_throw_ins_avg", "away_throw_ins_avg",
                "home_possession_avg", "away_possession_avg",
                "home_total_shots_avg", "away_total_shots_avg",
                "home_form_wins", "away_form_wins",
                "home_advantage",
            ],
            "total_shots": [
                "home_total_shots_avg", "away_total_shots_avg",
                "home_sot_avg", "away_sot_avg",
                "home_possession_avg", "away_possession_avg",
                "home_big_chances_avg", "away_big_chances_avg",
                "home_form_wins", "away_form_wins",
                "home_advantage",
            ],
            "big_chances": [
                "home_big_chances_avg", "away_big_chances_avg",
                "home_xg_avg", "away_xg_avg",
                "home_sot_avg", "away_sot_avg",
                "home_possession_avg", "away_possession_avg",
                "home_injury_penalty", "away_injury_penalty",
                "home_form_wins", "away_form_wins",
                "home_advantage",
            ],
        }
        
        selected = market_feature_map.get(market, list(features.keys()))
        return [features.get(f, 0) for f in selected]
