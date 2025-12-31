"""
Модуль для работы с ElevenLabs Text-to-Speech API
"""
import requests
import json
import logging
from pathlib import Path
from datetime import datetime
from config import (
    ELEVENLABS_API_KEY,
    ELEVENLABS_API_URL,
    FEMALE_VOICE_ID,
    DEFAULT_VOICE_ID,
    VOICE_SETTINGS,
    TTS_MODEL,
    AUDIO_DIR
)

logger = logging.getLogger(__name__)


class ElevenLabsTTS:
    """Класс для генерации речи через ElevenLabs API"""
    
    def __init__(self, voice_id: str = None):
        self.api_key = ELEVENLABS_API_KEY
        self.voice_id = voice_id or DEFAULT_VOICE_ID
        self.api_url = f"{ELEVENLABS_API_URL}/{self.voice_id}"
        self.headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }
    
    def set_voice(self, voice_id: str):
        """Устанавливает ID голоса для генерации"""
        self.voice_id = voice_id
        self.api_url = f"{ELEVENLABS_API_URL}/{self.voice_id}"
    
    def generate_speech(self, text: str) -> Path:
        """
        Генерирует аудиофайл из текста на русском языке
        
        Args:
            text: Текст для озвучивания (поддерживается русский язык)
            
        Returns:
            Path: Путь к сохраненному аудиофайлу
            
        Raises:
            Exception: При ошибке API или сохранения файла
        """
        try:
            # Подготовка данных для запроса
            # Модель eleven_multilingual_v2 автоматически определяет язык (включая русский)
            data = {
                "text": text,
                "model_id": TTS_MODEL,  # Мультиязычная модель с поддержкой русского
                "voice_settings": VOICE_SETTINGS
            }
            
            logger.info(f"Отправка запроса в ElevenLabs API для текста длиной {len(text)} символов (русский язык), голос ID: {self.voice_id}")
            
            # Отправка запроса
            response = requests.post(
                self.api_url,
                json=data,
                headers=self.headers,
                timeout=30
            )
            
            # Проверка статуса ответа
            response.raise_for_status()
            
            # Генерация имени файла
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"voice_{timestamp}.mp3"
            filepath = AUDIO_DIR / filename
            
            # Сохранение аудиофайла
            with open(filepath, "wb") as f:
                f.write(response.content)
            
            logger.info(f"Аудиофайл успешно сохранен: {filepath}")
            return filepath
            
        except requests.exceptions.HTTPError as e:
            # Обработка HTTP ошибок с детальным сообщением
            error_message = "Ошибка при обращении к ElevenLabs API"
            
            if hasattr(e, 'response') and e.response is not None:
                status_code = e.response.status_code
                try:
                    error_data = e.response.json()
                    detail = error_data.get('detail', {})
                    
                    if isinstance(detail, dict):
                        api_message = detail.get('message', '')
                        api_status = detail.get('status', '')
                        
                        if 'unusual_activity' in api_status.lower() or 'free tier' in api_message.lower():
                            error_message = (
                                "⚠️ Проблема с аккаунтом ElevenLabs:\n"
                                "Обнаружена необычная активность или бесплатный тариф заблокирован.\n"
                                "Проверьте ваш аккаунт на сайте elevenlabs.io"
                            )
                        elif status_code == 401:
                            error_message = (
                                "🔑 Ошибка авторизации:\n"
                                "Неверный API ключ ElevenLabs.\n"
                                "Проверьте ELEVENLABS_API_KEY в файле .env"
                            )
                        elif status_code == 403:
                            error_message = (
                                "🚫 Доступ запрещен (403):\n"
                                "Ваш API ключ не имеет доступа к этому ресурсу.\n\n"
                                "Возможные причины:\n"
                                "• Аккаунт заблокирован или ограничен\n"
                                "• Исчерпан лимит бесплатного тарифа\n"
                                "• Проблемы с регионом/IP адресом\n"
                                "• Требуется платная подписка\n\n"
                                "Проверьте статус аккаунта на elevenlabs.io"
                            )
                        elif status_code == 429:
                            error_message = (
                                "⏱️ Превышен лимит запросов:\n"
                                "Слишком много запросов к API.\n"
                                "Подождите немного и попробуйте снова"
                            )
                        else:
                            error_message = f"Ошибка API (код {status_code}): {api_message}"
                    else:
                        error_message = f"Ошибка API: {str(detail)}"
                        
                except (json.JSONDecodeError, KeyError, AttributeError):
                    # Если не удалось распарсить JSON, используем текст ответа
                    error_text = e.response.text[:200] if hasattr(e.response, 'text') else str(e)
                    logger.error(f"Ответ API (не JSON): {error_text}")
                    if status_code == 401:
                        error_message = "🔑 Ошибка авторизации: проверьте API ключ в .env файле"
                    elif status_code == 403:
                        error_message = (
                            "🚫 Доступ запрещен (403):\n"
                            "Проверьте статус аккаунта на elevenlabs.io\n"
                            "Возможно, требуется платная подписка или аккаунт заблокирован"
                        )
                    elif status_code == 429:
                        error_message = "⏱️ Превышен лимит запросов. Подождите и попробуйте снова"
                    else:
                        error_message = f"Ошибка API (код {status_code})"
            
            # Логируем детали ошибки для отладки
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Ошибка при запросе к ElevenLabs API (код {e.response.status_code}): {e}")
                if hasattr(e.response, 'text'):
                    logger.error(f"Полный ответ API: {e.response.text}")
            else:
                logger.error(f"Ошибка при запросе к ElevenLabs API: {e}")
            raise Exception(error_message)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка сети при запросе к ElevenLabs API: {e}")
            raise Exception("🌐 Ошибка сети: не удалось подключиться к ElevenLabs API. Проверьте интернет-соединение.")
            
        except Exception as e:
            logger.error(f"Неожиданная ошибка при генерации речи: {e}")
            raise Exception(f"❌ Неожиданная ошибка: {str(e)}")
    
    def is_valid_api_key(self) -> bool:
        """
        Проверяет валидность API ключа
        
        Returns:
            bool: True если ключ валиден
        """
        try:
            # Простой запрос для проверки ключа
            response = requests.get(
                "https://api.elevenlabs.io/v1/user",
                headers={"xi-api-key": self.api_key},
                timeout=10
            )
            
            if response.status_code == 200:
                return True
            elif response.status_code == 401:
                logger.warning("API ключ ElevenLabs недействителен (401)")
                return False
            else:
                logger.warning(f"Неожиданный статус при проверке API ключа: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            logger.warning(f"Ошибка при проверке API ключа: {e}")
            return False
        except Exception as e:
            logger.warning(f"Неожиданная ошибка при проверке API ключа: {e}")
            return False

