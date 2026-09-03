# 🏆 Football Betting ML System

Sistema de Machine Learning para proyección de mercados de apuestas de fútbol.

## 📋 Características

- ✅ **Últimos 5 partidos** por equipo con estadísticas detalladas
- ✅ **H2H** (cara a cara) entre equipos
- ✅ **Bajas ofensivas** detectadas por alineaciones
- ✅ **Líneas individuales** por equipo: remates al arco, corners, goles, tarjetas, saques de banda
- ✅ **Probabilidad ≥75%** - Top 10 partidos
- ✅ **Cuotas en tiempo real** desde SharpAPI
- ✅ **Envío a Telegram** con formato profesional
- ✅ **Ejecución desde móvil** vía GitHub Actions

## 🚀 Configuración

### 1. Crear repositorio en GitHub
Copia todos los archivos a tu repo.

### 2. Configurar Secrets en GitHub
Ve a **Settings → Secrets and variables → Actions** y añade:

| Secret | Descripción | Dónde obtener |
|--------|-------------|---------------|
| `STATS_API_KEY` | API de estadísticas | https://api.thestatsapi.com |
| `SHARP_API_KEY` | API de cuotas | https://sharpapi.io/es/dashboard |
| `TELEGRAM_BOT_TOKEN` | Bot de Telegram | @BotFather |
| `TELEGRAM_CHAT_ID` | Tu chat ID | @userinfobot |

### 3. Ejecutar desde móvil
1. Abre la app de GitHub en tu móvil
2. Ve a tu repositorio → Actions
3. Toca **"Football Betting Predictions"**
4. Toca **"Run workflow"** ▶️

### 4. Automático
El workflow se ejecuta todos los días a las 8:00 AM UTC.

## 📊 Mercados Analizados

| Mercado | Línea típica | Métricas usadas |
|---------|-------------|-----------------|
| Goles | 2.5 | xG, forma, bajas |
| Remates al arco | 4.5 | Total shots, posesión, xG |
| Corners | 9.5 | Posesión, remates, forma |
| Tarjetas amarillas | 3.5 | Faltas, forma, H2H |
| Saques de banda | 20.5 | Posesión, total shots |
| Total remates | 12.5 | Posesión, grandes ocasiones |
| Grandes ocasiones | 2.5 | xG, remates al arco |

## 🔧 Personalización

Edita `src/config.py` para ajustar:
- `MIN_PROBABILITY`: Umbral de probabilidad (default: 0.75)
- `TOP_N_MATCHES`: Número de picks a enviar (default: 10)
- `RECENT_MATCHES_COUNT`: Partidos históricos (default: 5)

## ⚠️ Disclaimer

Este sistema es para fines educativos. Las predicciones de ML no garantizan resultados. Apuesta con responsabilidad.
