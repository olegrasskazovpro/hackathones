from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from inference_sdk import InferenceHTTPClient
from io import BytesIO
import os

# Настройки клиента Inference SDK
client = InferenceHTTPClient(
    api_url="https://detect.roboflow.com",
    api_key="***************************"  # API-ключ Roboflow
)

# Приветственное сообщение
WELCOME_TEXT = (
    "Привет! Наш бот может с точностью в 88.9% определить, к какому архитектурному стилю принадлежит здание на вашем фото."
    "Выберите одну из опций ниже:"
)

# Список архитектурных стилей
STYLES_TEXT = (
    "- Art Nouveau (Модерн)\n"
    "- Baroque (Барокко)\n"
    "- Beaux-Arts (Бозар)\n"
    "- Byzantine (Византийская)\n"
    "- Chicago school (Чикагская архитектурная школа)\n"
    "- Deconstructivism (Деконструктивизм)\n"
    "- Edwardian (Эдвардианская архитектура)\n"
    "- Gothic (Готика)\n"
    "- Palladian (Палладианство)\n"
    "- Postmodern (Постмодернизм)\n"
    "- Romanesque (Романская архитектура)\n"
)

# Список команды проекта
TEAM_TEXT = (
    "Команда Susami:[ ](https://github.com/olegrasskazovpro/hackathones/tree/main/architectural-styles-detection)\n"   
    "- [Олег Рассказов](https://t.me/olegrasskazov)\n"
    "- [Дорохова Екатерина](https://t.me/KatiaDorohova)\n"
    "- [Иван Сойко](https://t.me/FlyZef)\n"
    "- [Никита Гутуев](https://t.me/WizZard21)\n"
    "- [Владимир Гаврилов](https://t.me/SVladimirAG)\n"
    "- [Андрей Максаков](https://t.me/maksakov_a)\n"
)

# Клавиатура для возвращения в меню
def get_menu_keyboard():
    keyboard = [[InlineKeyboardButton("Меню", callback_data="menu")]]
    return InlineKeyboardMarkup(keyboard)

# Обработчик команды /menu
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Кто я и что умею?", callback_data="whoami")],
        [InlineKeyboardButton("Определить стиль по фото", callback_data="detect")],
        [InlineKeyboardButton("Определяемые стили", callback_data="styles")],
        [InlineKeyboardButton("Команда проекта", callback_data="team")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text("Выберите одну из опций:", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text("Выберите одну из опций:", reply_markup=reply_markup)

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await menu(update, context)

# Обработчик нажатий кнопок
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "styles":
        print("Пользователь запросил список стилей.")
        await query.edit_message_text(
            text=f"Бот может определить следующие стили:\n\n{STYLES_TEXT}",
            reply_markup=get_menu_keyboard()
        )
    elif query.data == "detect":
        print("Пользователь выбрал определение стиля по фото.")
        await query.edit_message_text(
            text="Для того, чтобы определить стиль, загрузите изображение или направьте ссылку на него",
            reply_markup=get_menu_keyboard()
        )
    elif query.data == "team":
        print("Пользователь запросил список команды проекта.")
        await query.edit_message_text(
            text=TEAM_TEXT, parse_mode="Markdown",
            reply_markup=get_menu_keyboard()
        )
    elif query.data == "whoami":
        print("Пользователь запросил информацию о боте.")
        await query.edit_message_text(
            text="Я бот, созданный студентами магистратуры МФТИ, который может определить, к какому архитектурному стилю принадлежит здание на вашем фото.",
            reply_markup=get_menu_keyboard()
        )
    elif query.data == "menu":
        await menu(update, context)

# Обработчик фото
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    local_path = "received_image.jpg"  # Имя файла для сохранения изображения
    try:
        print("Фото получено от пользователя.")
        photo = update.message.photo[-1]  # Берем фото максимального размера
        photo_file = await photo.get_file()

        # Сохранение фото в локальный файл
        await photo_file.download_to_drive(local_path)
        print(f"Фото сохранено локально как '{local_path}'.")

        print("Отправляем фото в Inference SDK...")
        result = client.run_workflow(
            workspace_name="mipt4",  # Название рабочего пространства в Roboflow
            workflow_id="telegrambot",  # ID workflow в Roboflow
            images={"image": local_path},  # Передача пути к файлу
            use_cache=True  # Кэширование
        )
        print(f"Результат от Inference SDK: {result}")

        # Обработка результата
        if result and isinstance(result, list) and "predictions" in result[0]:
            predictions_data = result[0]["predictions"]

            # Получение основного стиля из top и confidence
            top_style = predictions_data.get("top", "Неизвестно")
            confidence = predictions_data.get("confidence", 0) * 100

            response_text = f"\U0001F4C8 Определенный стиль: {top_style}\nУверенность: {confidence:.2f}%"
            print(f"Предсказание: {response_text}")
            await update.message.reply_text(response_text, reply_markup=get_menu_keyboard())
        else:
            print("Inference SDK вернул пустое предсказание.")
            await update.message.reply_text(
                "Не удалось определить стиль. Попробуйте другое фото.",
                reply_markup=get_menu_keyboard()
            )
    except Exception as e:
        print(f"Ошибка в обработчике фото: {e}")
        await update.message.reply_text(
            "Произошла ошибка при обработке фото. Попробуйте еще раз.",
            reply_markup=get_menu_keyboard()
        )
    finally:
        # Удаление временного файла
        if os.path.exists(local_path):
            os.remove(local_path)
            print(f"Временный файл '{local_path}' удален.")

# Обработчик текстовых ссылок
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        url = update.message.text
        print(f"Получена текстовая ссылка: {url}")
        if url.startswith("http"):
            print("Отправляем ссылку в Inference SDK...")
            result = client.run_workflow(
                workspace_name="mipt4",  # Название рабочего пространства в Roboflow
                workflow_id="telegrambot",  # ID workflow в Roboflow
                images={"image": url},  # Передача ссылки на изображение
                use_cache=True
            )
            print(f"Результат от Inference SDK: {result}")

            if result and isinstance(result, list) and "predictions" in result[0]:
                predictions_data = result[0]["predictions"]

                # Получение основного стиля из top и confidence
                top_style = predictions_data.get("top", "Неизвестно")
                confidence = predictions_data.get("confidence", 0) * 100

                response_text = f"\U0001F4C8 Определенный стиль: {top_style}\nУверенность: {confidence:.2f}%"
                print(f"Предсказание: {response_text}")
                await update.message.reply_text(response_text, reply_markup=get_menu_keyboard())
            else:
                print("Inference SDK вернул пустое предсказание.")
                await update.message.reply_text(
                    "Не удалось определить стиль. Попробуйте другую ссылку.",
                    reply_markup=get_menu_keyboard()
                )
        else:
            print("Пользователь отправил некорректную ссылку.")
            await update.message.reply_text("Это не похоже на ссылку. Пожалуйста, отправьте корректную ссылку.")
    except Exception as e:
        print(f"Ошибка в обработчике текста: {e}")
        await update.message.reply_text(
            "Произошла ошибка при обработке ссылки. Попробуйте еще раз.",
            reply_markup=get_menu_keyboard()
        )

# Основная функция
def main():
    application = Application.builder().token("*****************************************").build()  # Токен бота Telegram

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Бот запущен и готов к работе.")
    application.run_polling()

if __name__ == "__main__":
    main()