"""
Основной файл Telegram-бота для озвучивания текста через ElevenLabs
"""
import logging
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from voice import ElevenLabsTTS
from config import TELEGRAM_BOT_TOKEN, MAX_TEXT_LENGTH, AVAILABLE_VOICES, DEFAULT_VOICE_ID

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class TelegramTTSBot:
    """Класс Telegram-бота для Text-to-Speech"""
    
    # Определение команд бота
    BOT_COMMANDS = [
        BotCommand("start", "Начать работу с ботом"),
        BotCommand("help", "Показать справку по использованию"),
        BotCommand("voice", "Выбрать голос для озвучивания"),
        BotCommand("status", "Проверить статус API и текущий голос"),
    ]
    
    def __init__(self):
        pass
    
    async def setup_commands(self, application: Application):
        """
        Устанавливает команды бота и проверяет их актуальность
        
        Args:
            application: Экземпляр Application бота
        """
        try:
            bot = application.bot
            
            # Получаем текущие команды бота
            current_commands = await bot.get_my_commands()
            
            # Проверяем, нужно ли обновить команды
            needs_update = False
            
            # Если команд нет вообще (первый запуск)
            if not current_commands:
                needs_update = True
                logger.info("Команды бота не установлены, выполняется первичная установка")
            elif len(current_commands) != len(self.BOT_COMMANDS):
                needs_update = True
                logger.info(f"Количество команд изменилось: было {len(current_commands)}, должно быть {len(self.BOT_COMMANDS)}")
            else:
                # Сравниваем команды по именам и описаниям (порядок не важен)
                current_dict = {cmd.command: cmd.description for cmd in current_commands}
                expected_dict = {cmd.command: cmd.description for cmd in self.BOT_COMMANDS}
                
                # Проверяем, что все ожидаемые команды присутствуют и совпадают
                if current_dict != expected_dict:
                    needs_update = True
                    logger.info("Обнаружены изменения в командах бота")
                    logger.debug(f"Текущие команды: {current_dict}")
                    logger.debug(f"Ожидаемые команды: {expected_dict}")
                    
                    # Логируем различия
                    missing = set(expected_dict.keys()) - set(current_dict.keys())
                    extra = set(current_dict.keys()) - set(expected_dict.keys())
                    changed = {k for k in expected_dict.keys() if k in current_dict and current_dict[k] != expected_dict[k]}
                    
                    if missing:
                        logger.info(f"Отсутствующие команды: {missing}")
                    if extra:
                        logger.info(f"Лишние команды: {extra}")
                    if changed:
                        logger.info(f"Измененные команды: {changed}")
            
            # Обновляем команды, если нужно
            if needs_update:
                await bot.set_my_commands(self.BOT_COMMANDS)
                logger.info(f"✅ Команды бота успешно обновлены: {[cmd.command for cmd in self.BOT_COMMANDS]}")
            else:
                logger.info("✅ Команды бота актуальны, обновление не требуется")
                
        except Exception as e:
            logger.error(f"❌ Ошибка при установке команд бота: {e}")
            # Не прерываем запуск бота, если не удалось установить команды
    
    def get_tts_instance(self, context: ContextTypes.DEFAULT_TYPE) -> ElevenLabsTTS:
        """Получает или создает экземпляр TTS с выбранным голосом пользователя"""
        voice_id = context.user_data.get("voice_id", DEFAULT_VOICE_ID)
        # Создаем новый экземпляр с нужным голосом каждый раз
        return ElevenLabsTTS(voice_id=voice_id)
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        # Инициализация данных пользователя
        context.user_data["user_id"] = update.effective_user.id
        context.user_data["voice_id"] = DEFAULT_VOICE_ID
        
        # Определяем текущий голос по умолчанию
        current_voice = None
        for key, voice_info in AVAILABLE_VOICES.items():
            if voice_info["id"] == DEFAULT_VOICE_ID:
                current_voice = voice_info
                break
        
        if current_voice is None:
            current_voice = list(AVAILABLE_VOICES.values())[0]
        
        welcome_message = (
            "🎙️ Привет! Я бот для озвучивания текста на русском языке.\n\n"
            "📝 Просто отправь мне текст на русском, и я преобразую его в речь с помощью ElevenLabs.\n"
            f"🎤 Текущий голос: {current_voice['name']} - {current_voice['description']}\n"
            f"⚠️ Максимальная длина текста: {MAX_TEXT_LENGTH} символов.\n\n"
            "Используй команду /voice для выбора голоса\n"
            "Используй команду /help для получения дополнительной информации."
        )
        await update.message.reply_text(welcome_message)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        help_message = (
            "📖 Справка по использованию бота:\n\n"
            "🔹 Команды:\n"
            "/start - Начать работу с ботом\n"
            "/help - Показать эту справку\n"
            "/voice - Выбрать голос для озвучивания\n"
            "/status - Проверить статус API\n\n"
            "💡 Как использовать:\n"
            "1. Выбери голос командой /voice (все голоса говорят на русском)\n"
            "2. Отправь мне любой текст на русском языке\n"
            "3. Я преобразую его в речь выбранным женским голосом\n"
            "4. Получишь аудиофайл с озвучкой\n"
            "5. Файл также сохранится локально на сервере\n\n"
            f"⚠️ Ограничения: максимум {MAX_TEXT_LENGTH} символов за раз\n"
            "🇷🇺 Все голоса поддерживают русский язык"
        )
        await update.message.reply_text(help_message)
    
    async def voice_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /voice - выбор голоса"""
        keyboard = []
        row = []
        
        for i, (key, voice_info) in enumerate(AVAILABLE_VOICES.items()):
            # Создаем кнопки по 2 в ряд
            button_text = f"{voice_info['name']}\n{voice_info['description']}"
            row.append(InlineKeyboardButton(button_text, callback_data=f"voice_{key}"))
            
            if len(row) == 2 or i == len(AVAILABLE_VOICES) - 1:
                keyboard.append(row)
                row = []
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        current_voice_id = context.user_data.get("voice_id", DEFAULT_VOICE_ID)
        current_voice_key = None
        for key, voice_info in AVAILABLE_VOICES.items():
            if voice_info["id"] == current_voice_id:
                current_voice_key = key
                break
        
        if current_voice_key:
            current_voice = AVAILABLE_VOICES[current_voice_key]
            message = (
                f"🎤 Выбери голос для озвучивания на русском языке:\n\n"
                f"Текущий голос: **{current_voice['name']}** - {current_voice['description']}\n\n"
                f"Доступно {len(AVAILABLE_VOICES)} женских голосов с разными тонами (все говорят на русском):"
            )
        else:
            message = f"🎤 Выбери голос для озвучивания на русском языке:\n\nДоступно {len(AVAILABLE_VOICES)} женских голосов с разными тонами (все говорят на русском):"
        
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode="Markdown")
    
    async def voice_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик выбора голоса через inline кнопки"""
        query = update.callback_query
        await query.answer()
        
        voice_key = query.data.replace("voice_", "")
        
        if voice_key not in AVAILABLE_VOICES:
            await query.edit_message_text("❌ Ошибка: выбранный голос не найден.")
            return
        
        selected_voice = AVAILABLE_VOICES[voice_key]
        context.user_data["voice_id"] = selected_voice["id"]
        
        success_message = (
            f"✅ Голос изменен!\n\n"
            f"🎤 Выбранный голос: **{selected_voice['name']}**\n"
            f"📝 Описание: {selected_voice['description']}\n\n"
            f"Теперь все тексты будут озвучиваться этим голосом."
        )
        
        await query.edit_message_text(success_message, parse_mode="Markdown")
        logger.info(f"Пользователь {update.effective_user.id} выбрал голос: {selected_voice['name']}")
    
    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /status - проверка статуса API"""
        try:
            tts = self.get_tts_instance(context)
            is_valid = tts.is_valid_api_key()
            if is_valid:
                current_voice_id = context.user_data.get("voice_id", DEFAULT_VOICE_ID)
                current_voice = None
                for voice_info in AVAILABLE_VOICES.values():
                    if voice_info["id"] == current_voice_id:
                        current_voice = voice_info
                        break
                
                voice_info_text = f"\n🎤 Текущий голос: {current_voice['name']}" if current_voice else ""
                status_message = (
                    f"✅ API ключ ElevenLabs валиден. Бот готов к работе!{voice_info_text}\n\n"
                    "💡 Если возникают ошибки при генерации, проверьте:\n"
                    "• Лимиты вашего тарифа на elevenlabs.io\n"
                    "• Статус аккаунта (не заблокирован ли Free Tier)"
                )
            else:
                status_message = (
                    "❌ Проблема с API ключом ElevenLabs.\n\n"
                    "🔧 Что проверить:\n"
                    "• Правильность ELEVENLABS_API_KEY в файле .env\n"
                    "• Действительность API ключа на сайте elevenlabs.io\n"
                    "• Статус аккаунта (не заблокирован ли из-за необычной активности)"
                )
        except Exception as e:
            status_message = f"⚠️ Ошибка при проверке статуса: {str(e)}"
        
        await update.message.reply_text(status_message)
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        user_text = update.message.text
        
        # Проверка длины текста
        if len(user_text) > MAX_TEXT_LENGTH:
            await update.message.reply_text(
                f"❌ Текст слишком длинный! Максимум {MAX_TEXT_LENGTH} символов.\n"
                f"Ваш текст: {len(user_text)} символов."
            )
            return
        
        # Отправка сообщения о начале обработки
        processing_message = await update.message.reply_text(
            "⏳ Обрабатываю ваш текст... Это может занять несколько секунд."
        )
        
        try:
            # Получаем экземпляр TTS с выбранным голосом пользователя
            tts = self.get_tts_instance(context)
            
            # Генерация аудио
            audio_path = tts.generate_speech(user_text)
            
            # Получаем информацию о текущем голосе для caption
            current_voice_id = context.user_data.get("voice_id", DEFAULT_VOICE_ID)
            current_voice_name = "Unknown"
            for voice_info in AVAILABLE_VOICES.values():
                if voice_info["id"] == current_voice_id:
                    current_voice_name = voice_info["name"]
                    break
            
            # Отправка аудиофайла пользователю
            with open(audio_path, "rb") as audio_file:
                await update.message.reply_voice(
                    voice=audio_file,
                    caption=f"🎵 Ваш текст озвучен голосом {current_voice_name}!\n📁 Файл: {audio_path.name}"
                )
            
            # Удаление сообщения о обработке
            await processing_message.delete()
            
            logger.info(f"Успешно обработан текст от пользователя {update.effective_user.id}")
            
        except Exception as e:
            error_message = f"❌ Ошибка при генерации аудио: {str(e)}"
            await processing_message.edit_text(error_message)
            logger.error(f"Ошибка при обработке текста: {e}")
    
    def run(self):
        """Запуск бота"""
        # Проверка токена уже выполняется в config.py при загрузке
        
        # Callback для установки команд после инициализации
        async def post_init(application: Application):
            await self.setup_commands(application)
        
        # Создание приложения с post_init callback
        application = (
            Application.builder()
            .token(TELEGRAM_BOT_TOKEN)
            .post_init(post_init)
            .build()
        )
        
        # Регистрация обработчиков
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("voice", self.voice_selection))
        application.add_handler(CommandHandler("status", self.status))
        application.add_handler(CallbackQueryHandler(self.voice_callback, pattern="^voice_"))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
        
        # Запуск бота
        logger.info("Бот запущен и готов к работе!")
        application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    bot = TelegramTTSBot()
    bot.run()

