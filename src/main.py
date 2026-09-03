"""
Punto de entrada principal del sistema.
Ejecuta el pipeline completo: datos → ML → predicciones → Telegram.
"""

import sys
import traceback
from src.config import Config
from src.predictor import PredictionEngine
from src.telegram_bot import TelegramNotifier


def main():
    print("🚀 Iniciando Football Betting ML System...")
    
    # Cargar configuración
    try:
        config = Config.from_env()
        config.validate()
        print("✅ Configuración cargada correctamente")
    except ValueError as e:
        print(f"❌ Error de configuración: {e}")
        print("   Asegúrate de configurar los secrets en GitHub:")
        print("   STATS_API_KEY, SHARP_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID")
        sys.exit(1)
    
    # Ejecutar predicciones
    try:
        engine = PredictionEngine(config)
        results = engine.run_predictions()
        
        # Enviar a Telegram
        if results.get("top_predictions"):
            print("\n📤 Enviando predicciones a Telegram...")
            notifier = TelegramNotifier(config)
            success = notifier.send_sync(results["top_predictions"])
            
            if success:
                print("✅ Predicciones enviadas exitosamente")
            else:
                print("❌ Error enviando a Telegram")
        else:
            print("\n📭 No hay predicciones que cumplan el criterio de probabilidad")
            
            # Enviar mensaje de "sin predicciones"
            notifier = TelegramNotifier(config)
            notifier.send_sync([])
        
        print("\n🏁 Proceso completado")
        
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        traceback.print_exc()
        
        # Notificar error por Telegram
        try:
            notifier = TelegramNotifier(config)
            asyncio = __import__('asyncio')
            bot = notifier.bot
            
            async def send_error():
                await bot.send_message(
                    chat_id=config.TELEGRAM_CHAT_ID,
                    text=f"❌ <b>Error en Football Betting ML</b>\n\n"
                         f"<code>{str(e)[:500]}</code>\n\n"
                         f"Revisa los logs de GitHub Actions.",
                    parse_mode="HTML"
                )
            asyncio.run(send_error())
        except Exception:
            pass
        
        sys.exit(1)


if __name__ == "__main__":
    main()
