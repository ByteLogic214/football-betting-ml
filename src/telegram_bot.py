"""
Bot de Telegram para enviar predicciones formateadas.
"""

import asyncio
from typing import List, Dict, Any
from telegram import Bot
from src.config import Config


class TelegramNotifier:
    def __init__(self, config: Config):
        self.bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
        self.chat_id = config.TELEGRAM_CHAT_ID
    
    def _format_prediction(self, pred: Dict[str, Any], rank: int) -> str:
        """Formatea una predicción individual para Telegram."""
        team = pred["home_team"] if pred["team_side"] == "home" else pred["away_team"]
        opponent = pred["away_team"] if pred["team_side"] == "home" else pred["home_team"]
        
        # Emojis según mercado
        market_emojis = {
            "goals": "⚽",
            "shots_on_target": "🎯",
            "corners": "🚩",
            "yellow_cards": "🟨",
            "throw_ins": "↗️",
            "total_shots": "💥",
            "big_chances": "⭐",
        }
        emoji = market_emojis.get(pred["market"], "📊")
        
        # Probabilidad con barra visual
        prob = pred["probability"] * 100
        bar = "█" * int(prob / 10) + "░" * (10 - int(prob / 10))
        
        msg = f"""
{emoji} <b>#{rank} {pred['home_team']} vs {pred['away_team']}</b>

📍 <b>Mercado:</b> {pred['market'].upper()} - {team} ({pred['team_side']})
📈 <b>Predicción:</b> {pred['predicted_value']} {pred['direction']} {pred['line']}
🎯 <b>Probabilidad:</b> {prob:.1f}% {bar}
🔒 <b>Confianza:</b> {pred['confidence']*100:.0f}%

💡 <b>Razones:</b> {pred['reasoning']}
"""
        
        # Añadir cuotas de SharpAPI si disponibles
        sharp_odds = pred.get("sharp_odds", [])
        if sharp_odds and not any("error" in str(o) for o in sharp_odds):
            msg += "\n💰 <b>Cuotas disponibles:</b>\n"
            for odd in sharp_odds[:3]:
                book = odd.get("sportsbook", "N/A")
                decimal = odd.get("odds_decimal", "N/A")
                ev = odd.get("ev_percent", 0)
                ev_str = f" (+{ev:.1f}% EV)" if ev > 0 else ""
                msg += f"   • {book}: @{decimal}{ev_str}\n"
        
        msg += f"\n⏰ {pred['match_date'][:10] if pred.get('match_date') else 'Próximamente'}\n"
        msg += "─" * 30
        
        return msg
    
    async def send_predictions(self, predictions: List[Dict[str, Any]]) -> bool:
        """
        Envía las predicciones Top 10 a Telegram.
        """
        if not predictions:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text="📭 No hay predicciones con probabilidad ≥75% para hoy."
            )
            return True
        
        # Header
        header = f"""
🏆 <b>PREDICCIONES TOP {len(predictions)} - FÚTBOL</b>
📅 {__import__('datetime').datetime.utcnow().strftime('%d/%m/%Y')}
🎯 Filtro: Probabilidad ≥75%

{"=" * 40}
"""
        await self.bot.send_message(
            chat_id=self.chat_id,
            text=header,
            parse_mode="HTML"
        )
        
        # Enviar cada predicción
        for i, pred in enumerate(predictions, 1):
            try:
                msg = self._format_prediction(pred, i)
                await self.bot.send_message(
                    chat_id=self.chat_id,
                    text=msg,
                    parse_mode="HTML",
                    disable_web_page_preview=True
                )
                await asyncio.sleep(0.5)  # Evitar rate limiting
            except Exception as e:
                print(f"Error enviando predicción {i}: {e}")
        
        # Footer con disclaimer
        footer = """
⚠️ <b>DISCLAIMER:</b>
Este sistema usa Machine Learning con datos históricos.
Las predicciones NO garantizan resultados.
Apuesta con responsabilidad y nunca más de lo que puedas perder.

🤖 Generado por Football Betting ML System
"""
        await self.bot.send_message(
            chat_id=self.chat_id,
            text=footer,
            parse_mode="HTML"
        )
        
        return True
    
    def send_sync(self, predictions: List[Dict[str, Any]]) -> bool:
        """Wrapper síncrono para enviar predicciones."""
        return asyncio.run(self.send_predictions(predictions))
