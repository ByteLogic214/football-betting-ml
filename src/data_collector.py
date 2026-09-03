"""
Recolector de datos: obtiene y estructura toda la información necesaria
para las predicciones (últimos 5 partidos, H2H, estadísticas, bajas).
"""

from typing import Dict, List, Any, Tuple
from collections import defaultdict
from src.api_client import TheStatsAPIClient
from src.config import Config


class DataCollector:
    def __init__(self, api_client: TheStatsAPIClient, config: Config):
        self.api = api_client
        self.config = config
    
    def collect_team_recent_stats(self, team_id: str, season_id: str) -> Dict[str, Any]:
        """
        Recolecta estadísticas de los últimos N partidos de un equipo.
        Retorna métricas agregadas por mercado.
        """
        matches = self.api.get_team_last_matches(team_id, season_id, 
                                                  self.config.RECENT_MATCHES_COUNT)
        
        if not matches:
            return {}
        
        stats_summary = {
            "matches_analyzed": len(matches),
            "goals_scored": [],
            "goals_conceded": [],
            "shots_on_target": [],
            "total_shots": [],
            "corners": [],
            "yellow_cards": [],
            "fouls": [],
            "throw_ins": [],
            "big_chances": [],
            "ball_possession": [],
            "xg": [],
            "points": [],
            "form": "",
        }
        
        form_sequence = []
        
        for match in matches:
            match_id = match["id"]
            is_home = match["home_team"]["id"] == team_id
            
            # Obtener estadísticas del partido
            try:
                stats = self.api.get_match_stats(match_id)
                data = stats.get("data", {})
            except Exception:
                continue
            
            # Goles
            score = match.get("score", {})
            if is_home:
                goals_for = score.get("home", 0) or 0
                goals_against = score.get("away", 0) or 0
            else:
                goals_for = score.get("away", 0) or 0
                goals_against = score.get("home", 0) or 0
            
            stats_summary["goals_scored"].append(goals_for)
            stats_summary["goals_conceded"].append(goals_against)
            
            # Resultado para forma
            if goals_for > goals_against:
                form_sequence.append("W")
            elif goals_for < goals_against:
                form_sequence.append("L")
            else:
                form_sequence.append("D")
            
            # Estadísticas detalladas
            overview = data.get("overview", {})
            
            # Remates al arco
            sot = overview.get("shots_on_target", {})
            if sot and sot.get("all"):
                val = sot["all"]["home"] if is_home else sot["all"]["away"]
                if val is not None:
                    stats_summary["shots_on_target"].append(val)
            
            # Total remates
            ts = overview.get("total_shots", {})
            if ts and ts.get("all"):
                val = ts["all"]["home"] if is_home else ts["all"]["away"]
                if val is not None:
                    stats_summary["total_shots"].append(val)
            
            # Corners
            ck = overview.get("corner_kicks", {})
            if ck and ck.get("all"):
                val = ck["all"]["home"] if is_home else ck["all"]["away"]
                if val is not None:
                    stats_summary["corners"].append(val)
            
            # Tarjetas amarillas
            yc = overview.get("yellow_cards", {})
            if yc and yc.get("all"):
                val = yc["all"]["home"] if is_home else yc["all"]["away"]
                if val is not None:
                    stats_summary["yellow_cards"].append(val)
            
            # Faltas
            fouls = overview.get("fouls", {})
            if fouls and fouls.get("all"):
                val = fouls["all"]["home"] if is_home else fouls["all"]["away"]
                if val is not None:
                    stats_summary["fouls"].append(val)
            
            # Saques de banda (throw_ins)
            ti = data.get("passes", {}).get("throw_ins", {})
            if ti and ti.get("all"):
                val = ti["all"]["home"] if is_home else ti["all"]["away"]
                if val is not None:
                    stats_summary["throw_ins"].append(val)
            
            # Grandes ocasiones
            bc = overview.get("big_chances", {})
            if bc and bc.get("all"):
                val = bc["all"]["home"] if is_home else bc["all"]["away"]
                if val is not None:
                    stats_summary["big_chances"].append(val)
            
            # Posesión
            bp = overview.get("ball_possession", {})
            if bp and bp.get("all"):
                val = bp["all"]["home"] if is_home else bp["all"]["away"]
                if val is not None:
                    stats_summary["ball_possession"].append(val)
            
            # xG
            xg = overview.get("expected_goals", {})
            if xg and xg.get("all"):
                val = xg["all"]["home"] if is_home else xg["all"]["away"]
                if val is not None:
                    stats_summary["xg"].append(val)
        
        stats_summary["form"] = "".join(form_sequence)
        
        # Calcular promedios
        for key in ["goals_scored", "goals_conceded", "shots_on_target", 
                    "total_shots", "corners", "yellow_cards", "fouls",
                    "throw_ins", "big_chances", "ball_possession", "xg"]:
            values = stats_summary[key]
            if values:
                stats_summary[f"{key}_avg"] = round(sum(values) / len(values), 2)
                stats_summary[f"{key}_std"] = self._calc_std(values)
            else:
                stats_summary[f"{key}_avg"] = 0
                stats_summary[f"{key}_std"] = 0
        
        return stats_summary
    
    def _calc_std(self, values: List[float]) -> float:
        """Calcula desviación estándar."""
        if len(values) < 2:
            return 0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return round(variance ** 0.5, 2)
    
    def collect_h2h_stats(self, team_a_id: str, team_b_id: str) -> Dict[str, Any]:
        """
        Recolecta estadísticas de partidos H2H entre dos equipos.
        """
        h2h_matches = self.api.get_h2h_matches(team_a_id, team_b_id, limit=5)
        
        if not h2h_matches:
            return {"matches_analyzed": 0}
        
        stats = {
            "matches_analyzed": len(h2h_matches),
            "team_a_wins": 0,
            "team_b_wins": 0,
            "draws": 0,
            "team_a_goals": [],
            "team_b_goals": [],
            "team_a_shots_on_target": [],
            "team_b_shots_on_target": [],
            "team_a_corners": [],
            "team_b_corners": [],
            "team_a_yellow_cards": [],
            "team_b_yellow_cards": [],
            "over_2_5_goals": 0,
            "btts_yes": 0,
        }
        
        for match in h2h_matches:
            score = match.get("score", {})
            home_goals = score.get("home", 0) or 0
            away_goals = score.get("away", 0) or 0
            total_goals = home_goals + away_goals
            
            # Identificar quién era local/visitante
            is_a_home = match["home_team"]["id"] == team_a_id
            
            if is_a_home:
                team_a_g = home_goals
                team_b_g = away_goals
            else:
                team_a_g = away_goals
                team_b_g = home_goals
            
            stats["team_a_goals"].append(team_a_g)
            stats["team_b_goals"].append(team_b_g)
            
            if team_a_g > team_b_g:
                stats["team_a_wins"] += 1
            elif team_a_g < team_b_g:
                stats["team_b_wins"] += 1
            else:
                stats["draws"] += 1
            
            if total_goals > 2.5:
                stats["over_2_5_goals"] += 1
            
            if home_goals > 0 and away_goals > 0:
                stats["btts_yes"] += 1
            
            # Estadísticas detalladas si disponibles
            try:
                match_stats = self.api.get_match_stats(match["id"])
                overview = match_stats.get("data", {}).get("overview", {})
                
                sot = overview.get("shots_on_target", {})
                if sot and sot.get("all"):
                    if is_a_home:
                        stats["team_a_shots_on_target"].append(sot["all"]["home"])
                        stats["team_b_shots_on_target"].append(sot["all"]["away"])
                    else:
                        stats["team_a_shots_on_target"].append(sot["all"]["away"])
                        stats["team_b_shots_on_target"].append(sot["all"]["home"])
                
                ck = overview.get("corner_kicks", {})
                if ck and ck.get("all"):
                    if is_a_home:
                        stats["team_a_corners"].append(ck["all"]["home"])
                        stats["team_b_corners"].append(ck["all"]["away"])
                    else:
                        stats["team_a_corners"].append(ck["all"]["away"])
                        stats["team_b_corners"].append(ck["all"]["home"])
                
                yc = overview.get("yellow_cards", {})
                if yc and yc.get("all"):
                    if is_a_home:
                        stats["team_a_yellow_cards"].append(yc["all"]["home"])
                        stats["team_b_yellow_cards"].append(yc["all"]["away"])
                    else:
                        stats["team_a_yellow_cards"].append(yc["all"]["away"])
                        stats["team_b_yellow_cards"].append(yc["all"]["home"])
                        
            except Exception:
                pass
        
        # Calcular promedios H2H
        for team in ["team_a", "team_b"]:
            for metric in ["goals", "shots_on_target", "corners", "yellow_cards"]:
                key = f"{team}_{metric}"
                values = stats[key]
                if values:
                    stats[f"{key}_avg"] = round(sum(values) / len(values), 2)
                else:
                    stats[f"{key}_avg"] = 0
        
        return stats
    
    def check_injuries(self, team_id: str, match_id: str) -> Dict[str, Any]:
        """
        Detecta bajas importantes comparando alineación confirmada vs plantilla.
        Identifica jugadores ofensivos clave ausentes.
        """
        try:
            lineups = self.api.get_match_lineups(match_id)
            lineup_data = lineups.get("data", {})
            
            if not lineup_data.get("confirmed", False):
                return {
                    "confirmed": False,
                    "missing_attackers": [],
                    "missing_players": [],
                    "warning_level": "unknown"
                }
            
            # Obtener plantilla completa
            squad = self.api.get_team_players(team_id)
            squad_ids = {p["id"] for p in squad}
            
            # Identificar qué equipo somos en el partido
            match_details = self.api.get_match_details(match_id)
            home_team_id = match_details.get("data", {}).get("home_team", {}).get("id")
            is_home = home_team_id == team_id
            
            team_key = "home" if is_home else "away"
            team_lineup = lineup_data.get(team_key, {})
            starting_xi = team_lineup.get("starting_xi", [])
            starting_ids = {p["id"] for p in starting_xi if p.get("id")}
            
            # Jugadores de la plantilla que NO están en el XI inicial
            missing_from_squad = squad_ids - starting_ids
            
            # Clasificar por posición (ataque = F, M)
            missing_attackers = []
            missing_midfielders = []
            missing_defenders = []
            
            for player in squad:
                if player["id"] in missing_from_squad:
                    pos = player.get("position", "")
                    player_info = {
                        "id": player["id"],
                        "name": player["name"],
                        "position": pos,
                        "jersey_number": player.get("current_team", {}).get("jersey_number")
                    }
                    
                    if pos == "F":
                        missing_attackers.append(player_info)
                    elif pos == "M":
                        missing_midfielders.append(player_info)
                    elif pos == "D":
                        missing_defenders.append(player_info)
            
            # Nivel de alerta basado en bajas ofensivas
            warning_level = "low"
            if len(missing_attackers) >= 2:
                warning_level = "high"
            elif len(missing_attackers) >= 1 or len(missing_midfielders) >= 2:
                warning_level = "medium"
            
            return {
                "confirmed": True,
                "missing_attackers": missing_attackers,
                "missing_midfielders": missing_midfielders,
                "missing_defenders": missing_defenders,
                "warning_level": warning_level,
                "total_missing": len(missing_from_squad),
            }
            
        except Exception as e:
            return {
                "confirmed": False,
                "missing_attackers": [],
                "missing_players": [],
                "warning_level": "error",
                "error": str(e)
            }
    
    def get_team_season_stats(self, team_id: str, season_id: str) -> Dict[str, Any]:
        """Obtiene estadísticas de temporada de un equipo."""
        try:
            stats = self.api.get_team_stats(team_id, season_id)
            return stats.get("data", {})
        except Exception:
            return {}
    
    def collect_match_data(self, match: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recolecta toda la información necesaria para un partido específico.
        """
        home_team = match["home_team"]
        away_team = match["away_team"]
        season_id = match.get("season_id", "")
        
        print(f"📊 Recolectando datos: {home_team['name']} vs {away_team['name']}")
        
        # Estadísticas recientes de cada equipo
        home_recent = self.collect_team_recent_stats(home_team["id"], season_id)
        away_recent = self.collect_team_recent_stats(away_team["id"], season_id)
        
        # Estadísticas H2H
        h2h = self.collect_h2h_stats(home_team["id"], away_team["id"])
        
        # Bajas
        home_injuries = self.check_injuries(home_team["id"], match["id"])
        away_injuries = self.check_injuries(away_team["id"], match["id"])
        
        # Estadísticas de temporada
        home_season = self.get_team_season_stats(home_team["id"], season_id)
        away_season = self.get_team_season_stats(away_team["id"], season_id)
        
        # Cuotas desde TheStatsAPI
        odds_stats = self.api.get_match_odds(match["id"])
        
        return {
            "match_id": match["id"],
            "match_date": match.get("utc_date"),
            "competition_id": match.get("competition_id"),
            "home_team": {
                "id": home_team["id"],
                "name": home_team["name"],
            },
            "away_team": {
                "id": away_team["id"],
                "name": away_team["name"],
            },
            "home_recent": home_recent,
            "away_recent": away_recent,
            "h2h": h2h,
            "home_injuries": home_injuries,
            "away_injuries": away_injuries,
            "home_season": home_season,
            "away_season": away_season,
            "odds": odds_stats,
        }
