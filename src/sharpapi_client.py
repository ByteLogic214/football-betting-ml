"""
Cliente para SharpAPI - obtiene cuotas en tiempo real de múltiples sportsbooks.
"""

import requests
import time
from typing import List, Dict, Any, Optional
from src.config import Config


class SharpAPIClient:
    def __init__(self, config: Config):
        self.base_url = config.SHARP_API_BASE
        self.api_key = config.SHARP_API_KEY
        self.headers = {"X-API-Key": self.api_key}
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def _get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Hace una petición GET a SharpAPI."""
        url = f"{self.base_url}{endpoint}"
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, params=params, timeout=30)
                
                if response.status_code == 429:
                    wait_time = (attempt + 1) * 2
                    time.sleep(wait_time)
                    continue
                
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    return {"data": []}  # Fallback silencioso
                time.sleep((attempt + 1) * 2)
        
        return {"data": []}
    
    def get_soccer_odds(self, league: str = "EPL", 
                        market_type: Optional[str] = None) -> List[Dict]:
        """
        Obtiene cuotas de fútbol/soccer.
        Ligas disponibles: EPL, LaLiga, SerieA, Bundesliga, Ligue1, UCL, MLS
        """
        params = {"league": league}
        if market_type:
            params["market"] = market_type
        
        data = self._get("/odds", params)
        return data.get("data", [])
    
    def get_event_odds(self, event_id: str) -> List[Dict]:
        """Obtiene cuotas específicas de un evento."""
        params = {"event_id": event_id}
        data = self._get("/odds", params)
        return data.get("data", [])
    
    def get_fair_odds(self, league: str = "EPL") -> List[Dict]:
        """Obtiene cuotas justas (no-vig) calculadas por SharpAPI."""
        params = {"league": league, "include_fair": "true"}
        data = self._get("/odds", params)
        return data.get("data", [])
    
    def find_match_odds(self, home_team: str, away_team: str, 
                        league: str = "EPL") -> List[Dict]:
        """
        Busca cuotas para un partido específico por nombre de equipos.
        """
        all_odds = self.get_soccer_odds(league)
        
        matched = []
        home_lower = home_team.lower()
        away_lower = away_team.lower()
        
        for odd in all_odds:
            odd_home = odd.get("home_team", "").lower()
            odd_away = odd.get("away_team", "").lower()
            
            # Matching flexible por substrings
            if (home_lower in odd_home or odd_home in home_lower or
                any(word in odd_home for word in home_lower.split())) and \
               (away_lower in odd_away or odd_away in away_lower or
                any(word in odd_away for word in away_lower.split())):
                matched.append(odd)
        
        return matched
    
    def get_ev_opportunities(self, league: str = "EPL", 
                             min_ev: float = 2.0) -> List[Dict]:
        """
        Obtiene oportunidades +EV detectadas por SharpAPI.
        Requiere plan Pro ($229/mo) o superior.
        """
        params = {
            "league": league,
            "min_ev": min_ev,
            "include_ev": "true",
        }
        data = self._get("/odds", params)
        return data.get("data", [])
    
    def get_arbitrage_opportunities(self, league: str = "EPL") -> List[Dict]:
        """
        Obtiene oportunidades de arbitraje.
        Requiere plan Hobby ($79/mo) o superior.
        """
        params = {
            "league": league,
            "include_arb": "true",
        }
        data = self._get("/odds", params)
        return data.get("data", [])
