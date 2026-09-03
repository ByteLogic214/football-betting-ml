"""
Motor principal de predicciones: orquesta la recolección de datos,
feature engineering y predicciones ML.
"""

import json
from typing import List, Dict, Any
from datetime import datetime
from src.config import Config
from src.api_client import TheStatsAPIClient
from src.sharpapi_client import SharpAPIClient
from src.data_collector import DataCollector
from src.feature_engineering import FeatureEngineer
from src.ml_models import BettingLinePredictor, MarketPrediction


class PredictionEngine:
    def __init__(self, config: Config):
        self.config = config
        self.stats_api = TheStatsAPIClient(config)
        self.sharp_api = SharpAPIClient(config)
        self.collector = DataCollector(self.stats_api, config)
        self.engineer = FeatureEngineer(config)
        self.predictor = BettingLinePredictor()
    
    def run_predictions(self) -> Dict[str, Any]:
        """
        Ejecuta el pipeline completo de predicciones.
        """
        print("=" * 60)
        print("🏆 SISTEMA DE PREDICCIÓN DE APUESTAS DE FÚTBOL")
        print("=" * 60)
        
        # 1. Obtener partidos programados
        print("\n📅 Obteniendo partidos programados...")
        matches = self.stats_api.get_upcoming_matches(days_ahead=2)
        
        if self.config.COMPETITION_FILTER:
            # Filtrar por competición si se especificó
            matches = [m for m in matches 
                       if self.config.COMPETITION_FILTER.lower() in 
                       m.get("competition_id", "").lower()]
        
        print(f"   Encontrados {len(matches)} partidos")
        
        if not matches:
            return {"status": "no_matches", "predictions": []}
        
        # 2. Recolectar datos y generar predicciones
        all_predictions = []
        
        for match in matches[:50]:  # Limitar a 50 partidos para no exceder rate limits
            try:
                match_data = self.collector.collect_match_data(match)
                features = self.engineer.extract_features(match_data)
                predictions = self.predictor.predict_all_markets(features)
                
                # Filtrar por probabilidad mínima
                high_conf = self.predictor.calculate_combined_probability(
                    predictions, min_prob=self.config.MIN_PROBABILITY
                )
                
                # Obtener cuotas de SharpAPI
                sharp_odds = self._get_sharp_odds(match_data)
                
                for pred in high_conf:
                    result = {
                        "match_id": match["id"],
                        "match_date": match.get("utc_date"),
                        "competition": match.get("competition_id"),
                        "home_team": match_data["home_team"]["name"],
                        "away_team": match_data["away_team"]["name"],
                        "market": pred.market,
                        "team_side": pred.team,
                        "predicted_value": pred.predicted_value,
                        "line": pred.line_suggestion,
                        "direction": "OVER" if pred.predicted_value > pred.line_suggestion else "UNDER",
                        "probability": pred.probability,
                        "confidence": pred.confidence,
                        "reasoning": pred.reasoning,
                        "sharp_odds": sharp_odds,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                    all_predictions.append(result)
                    
            except Exception as e:
                print(f"   ⚠️ Error en partido {match.get('id')}: {e}")
                continue
        
        # 3. Seleccionar Top N
        top_predictions = sorted(
            all_predictions,
            key=lambda x: (x["probability"], x["confidence"]),
            reverse=True
        )[:self.config.TOP_N_MATCHES]
        
        # 4. Guardar resultados
        output = {
            "status": "success",
            "generated_at": datetime.utcnow().isoformat(),
            "total_matches_analyzed": len(matches),
            "total_predictions": len(all_predictions),
            "top_predictions": top_predictions,
        }
        
        # Guardar en archivo JSON
        filename = f"predictions_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Predicciones guardadas en: {filename}")
        print(f"   Total predicciones: {len(all_predictions)}")
        print(f"   Top {self.config.TOP_N_MATCHES} seleccionadas")
        
        return output
    
    def _get_sharp_odds(self, match_data: Dict[str, Any]) -> List[Dict]:
        """Obtiene cuotas de SharpAPI para el partido."""
        try:
            home_name = match_data["home_team"]["name"]
            away_name = match_data["away_team"]["name"]
            
            # Mapeo de nombres de competición a códigos SharpAPI
            comp_map = {
                "comp_3039": "EPL",      # Premier League
                "comp_2013": "LaLiga",   # La Liga
                "comp_2002": "Bundesliga", # Bundesliga
                "comp_2014": "SerieA",   # Serie A
                "comp_2015": "Ligue1",   # Ligue 1
                "comp_7": "UCL",         # Champions League
            }
            
            league = comp_map.get(match_data.get("competition_id", ""), "EPL")
            
            odds = self.sharp_api.find_match_odds(home_name, away_name, league)
            
            # Enriquecer con EV si disponible
            if odds:
                for odd in odds:
                    odd["ev_percent"] = odd.get("ev_percent", 0)
                    odd["fair_odds"] = odd.get("fair_odds", {})
            
            return odds
            
        except Exception as e:
            return [{"error": str(e)}]
