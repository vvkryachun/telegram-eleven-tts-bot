"""
Конфигурационный файл для Telegram-бота с ElevenLabs TTS
Все секреты загружаются из .env файла
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()

# Telegram Bot API
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не найден в .env файле! Создайте .env файл и добавьте TELEGRAM_BOT_TOKEN=your_token")

# ElevenLabs API
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
if not ELEVENLABS_API_KEY:
    raise ValueError("ELEVENLABS_API_KEY не найден в .env файле! Создайте .env файл и добавьте ELEVENLABS_API_KEY=your_key")

ELEVENLABS_API_URL = "https://api.elevenlabs.io/v1/text-to-speech"

# Доступные женские голоса с разными тонами (все говорят на русском языке)
# Все голоса используют мультиязычную модель eleven_multilingual_v2, которая отлично поддерживает русский язык
# Формат: {"id": "voice_id", "name": "Название", "description": "Описание тона"}
AVAILABLE_VOICES = {
    "bella": {
        "id": "EXAVITQu4vr4xnSDxMaL",
        "name": "Bella",
        "description": "Мягкий, спокойный, умиротворяющий (русский)"
    },
    "rachel": {
        "id": "21m00Tcm4TlvDq8ikWAM",
        "name": "Rachel",
        "description": "Профессиональный, нейтральный, четкий (русский)"
    },
    "domi": {
        "id": "AZnzlk1XvdvUeBnXmlld",
        "name": "Domi",
        "description": "Энергичный, молодой, динамичный (русский)"
    },
    "elli": {
        "id": "MF3mGyEYCl7XYWbV9V6O",
        "name": "Elli",
        "description": "Дружелюбный, теплый, приветливый (русский)"
    },
    "dorothy": {
        "id": "ThT5KcBeYPX3keUQqHPh",
        "name": "Dorothy",
        "description": "Зрелый, уверенный, авторитетный (русский)"
    },
    "charlotte": {
        "id": "XB0fDUnXU5powFXDhCwa",
        "name": "Charlotte",
        "description": "Элегантный, утонченный (русский)"
    },
    "alice": {
        "id": "Xb7hH8MSUJpSbSDYk0k2",
        "name": "Alice",
        "description": "Нежный, мягкий, деликатный (русский)"
    }
}

# Голос по умолчанию
DEFAULT_VOICE_ID = AVAILABLE_VOICES["bella"]["id"]
# Опционально: можно указать голос по умолчанию в .env
FEMALE_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", DEFAULT_VOICE_ID)

# Настройки генерации речи
# Оптимизированы для русского языка и естественного звучания
VOICE_SETTINGS = {
    "stability": 0.5,          # Стабильность голоса (0.0-1.0)
    "similarity_boost": 0.75,   # Схожесть с оригинальным голосом (0.0-1.0)
    "style": 0.0,              # Стиль произношения (0.0-1.0)
    "use_speaker_boost": True   # Улучшение качества голоса
}

# Модель для генерации речи (поддерживает русский язык)
TTS_MODEL = "eleven_multilingual_v2"  # Мультиязычная модель с поддержкой русского

# Путь для сохранения аудиофайлов
AUDIO_DIR = Path("audio")
AUDIO_DIR.mkdir(exist_ok=True)

# Максимальная длина текста (символов)
MAX_TEXT_LENGTH = 5000

