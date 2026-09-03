"""
Cliente para TheStatsAPI - obtiene datos de partidos, estadísticas y alineaciones.
"""

import requests
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from src.config import Config


class TheStatsAPIClient:
    def __init__(self, config: Config):
        self.base_url = config.STATS_API_BASE
        self.api_key = config.STATS_API_KEY
        self.headers = {"Authorization": f"Bearer {self.api_key}"}
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def _get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Hace una petición GET con manejo de rate limiting."""
        url = f"{self.base_url}{endpoint}"
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, params=params, timeout=30)
                
                if response.status_code == 429:  # Rate limited
                    wait_time = (attempt + 1) * 2
                    time.sleep(wait_time)
                    continue
                
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise
                time.sleep((attempt + 1) * 2)
        
        return {}
    
    def get_upcoming_matches(self, days_ahead: int = 3, 
                             competition_id: Optional[str] = None) -> List[Dict]:
        """Obtiene partidos programados en los próximos días."""
        date_from = datetime.utcnow().strftime("%Y-%m-%d")
        date_to = (datetime.utcnow() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
        
        all_matches = []
        page = 1
        
        while True:
            params = {
                "date_from": date_from,
                "date_to": date_to,
                "status": "scheduled",
                "per_page": 100,
                "page": page,
            }
            
            if competition_id:
                params["competition_id"] = competition_id
            
            data = self._get("/football/matches", params)
            matches = data.get("data", [])
            
            if not matches:
                break
            
            all_matches.extend(matches)
            
            meta = data.get("meta", {})
            if page >= meta.get("total_pages", 1):
                break
            
            page += 1
            time.sleep(0.5)  # Rate limiting
        
        return all_matches
    
    def get_team_last_matches(self, team_id: str, season_id: str, 
                              limit: int = 5) -> List[Dict]:
        """Obtiene los últimos N partidos terminados de un equipo."""
        date_to = datetime.utcnow().strftime("%Y-%m-%d")
        date_from = (datetime.utcnow() - timedelta(days=90)).strftime("%Y-%m-%d")
        
        params = {
            "team_id": team_id,
            "status": "finished",
            "date_from": date_from,
            "date_to": date_to,
            "per_page": limit,
            "page": 1,
        }
        
        data = self._get("/football/matches", params)
        return data.get("data", [])
    
    def get_match_stats(self, match_id: str) -> Dict[str, Any]:
        """Obtiene estadísticas detalladas de un partido."""
        return self._get(f"/football/matches/{match_id}/stats")
    
    def get_match_details(self, match_id: str) -> Dict[str, Any]:
        """Obtiene detalles de un partido."""
        return self._get(f"/football/matches/{match_id}")
    
    def get_team_players(self, team_id: str) -> List[Dict]:
        """Obtiene la plantilla completa de un equipo."""
        data = self._get(f"/football/teams/{team_id}/players")
        return data.get("data", [])
    
    def get_match_lineups(self, match_id: str) -> Dict[str, Any]:
        """Obtiene alineaciones de un partido."""
        try:
            return self._get(f"/football/matches/{match_id}/lineups")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return {"data": {"confirmed": False}}
            raise
    
    def get_match_odds(self, match_id: str) -> Dict[str, Any]:
        """Obtiene cuotas de un partido desde TheStatsAPI."""
        try:
            return self._get(f"/football/matches/{match_id}/odds")
        except requests.exceptions.HTTPError:
            return {}
    
    def get_team_stats(self, team_id: str, season_id: str) -> Dict[str, Any]:
        """Obtiene estadísticas de temporada de un equipo."""
        return self._get(f"/football/teams/{team_id}/stats", {"season_id": season_id})
    
    def get_h2h_matches(self, team_a_id: str, team_b_id: str, 
                        limit: int = 5) -> List[Dict]:
        """Obtiene partidos H2H entre dos equipos."""
        # Obtener partidos de team_a y filtrar por team_b
        date_from = (datetime.utcnow() - timedelta(days=730)).strftime("%Y-%m-%d")
        date_to = datetime.utcnow().strftime("%Y-%m-%d")
        
        params = {
            "team_id": team_a_id,
            "status": "finished",
            "date_from": date_from,
            "date_to": date_to,
            "per_page": 50,
            "page": 1,
        }
        
        data = self._get("/football/matches", params)
        all_matches = data.get("data", [])
        
        # Filtrar partidos donde juga el equipo B
        h2h = [
            m for m in all_matches 
            if m["home_team"]["id"] == team_b_id or m["away_team"]["id"] == team_b_id
        ]
        
        return h2h[:limit]
