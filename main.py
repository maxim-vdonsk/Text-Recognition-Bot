import os
import sqlite3
import logging
import cv2
import numpy as np
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext, filters
from PIL import Image
import pytesseract
import fitz
from gtts import gTTS
from g4f.client import AsyncClient

# GPT клиент
g4f_client = AsyncClient()

# Загрузка переменных окружения
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

MAX_PHOTO_SIZE = 10 * 1024 * 1024
MAX_DOCUMENT_SIZE = 50 * 1024 * 1024

def create_db():
    conn = sqlite3.connect("files.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            file_path TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def save_file_to_db(user_id, file_path):
    conn = sqlite3.connect("files.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO files (user_id, file_path) VALUES (?, ?)", (user_id, file_path))
    conn.commit()
    conn.close()

def delete_old_file(user_id):
    conn = sqlite3.connect("files.db")
    cursor = conn.cursor()
    cursor.execute("SELECT file_path FROM files WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,))
    result = cursor.fetchone()
    if result:
        file_path = result[0]
        if os.path.exists(file_path):
            os.remove(file_path)
        cursor.execute("DELETE FROM files WHERE user_id = ?", (user_id,))
        conn.commit()
    conn.close()

async def start(update: Update, context: CallbackContext):
    keyboard = [["Распознать", "Распознать как фотографию"], ["Распознать с помощью ChatGPT"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Отправьте изображение или PDF-файл с текстом.", reply_markup=reply_markup)

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    return "".join([page.get_text("text") for page in doc]).strip()

def convert_pdf_to_images(pdf_path):
    doc = fitz.open(pdf_path)
    images = []
    for page in doc:
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(img)
    return images

async def handle_file(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    delete_old_file(user_id)

    if update.message.document:
        document = update.message.document
        if document.file_size > MAX_DOCUMENT_SIZE:
            await update.message.reply_text("Файл слишком большой.")
            return
        file = await document.get_file()
        os.makedirs("files", exist_ok=True)
        file_ext = document.file_name.split(".")[-1].lower()
        file_path = f"files/{user_id}_file.{file_ext}"
        await file.download_to_drive(file_path)
    elif update.message.photo:
        photo = update.message.photo[-1]
        if photo.file_size > MAX_PHOTO_SIZE:
            await update.message.reply_text("Фото слишком большое.")
            return
        file = await photo.get_file()
        os.makedirs("files", exist_ok=True)
        file_path = f"files/{user_id}_photo.jpg"
        await file.download_to_drive(file_path)
    else:
        await update.message.reply_text("Отправьте изображение или PDF-файл.")
        return

    save_file_to_db(user_id, file_path)

    keyboard = [["Распознать", "Распознать как фотографию"], ["Распознать с помощью ChatGPT"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Файл загружен. Выберите действие:", reply_markup=reply_markup)

def preprocess_image(image):
    gray = cv2.cvtColor(np.array(image), cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_LANCZOS4)
    gray = cv2.medianBlur(gray, 3)
    return Image.fromarray(gray)

async def send_long_message(update: Update, text: str):
    for i in range(0, len(text), 4096):
        await update.message.reply_text(text[i:i+4096])

async def recognize_text_from_file(user_id, as_photo=False):
    conn = sqlite3.connect("files.db")
    cursor = conn.cursor()
    cursor.execute("SELECT file_path FROM files WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,))
    result = cursor.fetchone()
    conn.close()
    if not result:
        return None, "Файл не найден."

    file_path = result[0]
    file_ext = file_path.split(".")[-1].lower()

    try:
        if file_ext == "pdf":
            if as_photo:
                images = convert_pdf_to_images(file_path)
                text = ""
                for img in images:
                    processed = preprocess_image(img)
                    text += pytesseract.image_to_string(processed, lang="rus+eng", config="--oem 3 --psm 6") + "\n"
                return text.strip(), None
            else:
                text = extract_text_from_pdf(file_path)
                if text:
                    return text.strip(), None
                images = convert_pdf_to_images(file_path)
                text = ""
                for img in images:
                    processed = preprocess_image(img)
                    text += pytesseract.image_to_string(processed, lang="rus+eng", config="--oem 3") + "\n"
                return text.strip(), None
        else:
            img = Image.open(file_path)
            processed = preprocess_image(img)
            text = pytesseract.image_to_string(processed, lang="rus+eng", config="--oem 3")
            return text.strip(), None
    except Exception as e:
        logging.error(f"Ошибка OCR: {e}")
        return None, "Ошибка при распознавании."

async def text_to_speech(update: Update, context: CallbackContext, text: str):
    await update.message.reply_text("Перевожу текст в аудио...")
    try:
        tts = gTTS(text, lang="ru")
        path = f"files/audio_{update.message.from_user.id}.mp3"
        tts.save(path)
        with open(path, "rb") as audio:
            await update.message.reply_audio(audio=InputFile(audio))
        os.remove(path)
    except Exception as e:
        logging.error(f"Ошибка TTS: {e}")
        await update.message.reply_text("Ошибка при преобразовании в аудио.")

async def handle_recognition(update: Update, context: CallbackContext):
    text = update.message.text
    user_id = update.message.from_user.id

    if text == "Распознать":
        recognized, error = await recognize_text_from_file(user_id, as_photo=False)
    elif text == "Распознать как фотографию":
        recognized, error = await recognize_text_from_file(user_id, as_photo=True)
    elif text == "Распознать с помощью ChatGPT":
        await update.message.reply_text("Текст распознается...")
        recognized, error = await recognize_text_from_file(user_id, as_photo=False)
        if not error and recognized:
            context.user_data["recognized_text"] = recognized
            keyboard = [["Краткий пересказ", "Перевод на английский"], ["Объясни текст", "Собрать по смыслу с помощью в GPT"]]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
            await update.message.reply_text("Текст распознан. Что сделать с ним?", reply_markup=reply_markup)
        else:
            await update.message.reply_text(error or "Не удалось распознать.")
        return
    elif text in ["Краткий пересказ", "Перевод на английский", "Объясни текст", "Собрать по смыслу с помощью в GPT"]:
        recognized = context.user_data.get("recognized_text")
        if not recognized:
            await update.message.reply_text("Нет текста для обработки.")
            return
        prompts = {
            "Краткий пересказ": f"Сделай краткий пересказ:\n{recognized}",
            "Перевод на английский": f"Переведи на английский:\n{recognized}",
            "Объясни текст": f"Объясни смысл:\n{recognized}",
            "Собрать по смыслу с помощью в GPT": f"Собери текст по смыслу, без каких либо дополнений:\n{recognized}"
        }
        await update.message.reply_text("Текст распознается...")
        try:
            msg = await g4f_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompts[text]}]
            )
            gpt_answer = msg.choices[0].message.content.strip()
            context.user_data["gpt_text"] = gpt_answer
            await send_long_message(update, gpt_answer)
            reply_markup = ReplyKeyboardMarkup([["Перевести в аудио"], ["Назад"]], resize_keyboard=True)
            await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)
        except Exception as e:
            logging.error(f"GPT error: {e}")
            await update.message.reply_text("Ошибка GPT.")
        return
    elif text == "Перевести в аудио":
        gpt_text = context.user_data.get("gpt_text")
        recognized = context.user_data.get("recognized_text")
        final_text = gpt_text or recognized
        if final_text:
            await text_to_speech(update, context, final_text)
        else:
            await update.message.reply_text("Нет текста для озвучивания.")
        return
    elif text == "Назад":
        return await start(update, context)
    else:
        return

    if error:
        await update.message.reply_text(error)
    elif recognized:
        context.user_data["recognized_text"] = recognized
        await send_long_message(update, recognized)
        reply_markup = ReplyKeyboardMarkup([["Перевести в аудио"], ["Назад"]], resize_keyboard=True)
        await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)

def main():
    create_db()
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_file))
    app.add_handler(MessageHandler(filters.TEXT, handle_recognition))
    app.run_polling()

if __name__ == "__main__":
    main()
