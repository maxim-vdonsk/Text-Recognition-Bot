# Text Recognition Bot

Этот проект представляет собой Telegram-бота для распознавания текста из изображений и PDF-файлов. Бот поддерживает преобразование текста в аудио, а также взаимодействие с GPT для обработки текста.

## Возможности

- Распознавание текста из изображений и PDF-файлов.
- Преобразование текста в аудио с помощью Google Text-to-Speech (gTTS).
- Интеграция с GPT для обработки текста (перевод, краткий пересказ, объяснение смысла и т.д.).
- Хранение загруженных файлов в базе данных SQLite.
- Удаление старых файлов для экономии места.

## Установка

### 1. Клонирование репозитория

```bash
git clone https://github.com/your-username/text-recognition-bot.git
cd text-recognition-bot
```

### 2. Установка зависимостей

Убедитесь, что у вас установлен Python версии 3.8 или выше. Затем установите зависимости:

```bash
pip install -r requirements.txt
```

### 3. Настройка переменных окружения

Создайте файл `.env` в корне проекта и добавьте в него ваш токен Telegram-бота:

```
TELEGRAM_BOT_TOKEN=ваш_токен_бота
```

### 4. Установка Tesseract OCR

Для работы с OCR необходимо установить Tesseract. Инструкции для установки:

- **Ubuntu/Debian**:
  ```bash
  sudo apt update
  sudo apt install tesseract-ocr
  ```
- **Windows**:
  Скачайте и установите Tesseract с [официального сайта](https://github.com/tesseract-ocr/tesseract).

- **MacOS**:
  ```bash
  brew install tesseract
  ```

### 5. Установка дополнительных библиотек

Для работы с PDF-файлами используется библиотека `PyMuPDF` (fitz). Убедитесь, что она установлена через `requirements.txt`.

### 6. Запуск бота

Создайте базу данных SQLite и запустите бота:

```bash
python main.py
```

## Использование

1. Запустите бота в Telegram.
2. Отправьте изображение или PDF-файл.
3. Выберите действие из предложенного меню:
   - Распознать текст.
   - Распознать текст как фотографию.
   - Распознать текст с помощью GPT.
4. Дополнительно можно преобразовать текст в аудио.

## Зависимости

- Python 3.8+
- [python-telegram-bot](https://python-telegram-bot.org/)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- [PyMuPDF](https://pymupdf.readthedocs.io/)
- [gTTS](https://gtts.readthedocs.io/)
- [dotenv](https://pypi.org/project/python-dotenv/)
- [OpenCV](https://opencv.org/)
- [NumPy](https://numpy.org/)

Все зависимости указаны в файле `requirements.txt`.

## Файл `requirements.txt`

```plaintext
python-telegram-bot==20.3
python-dotenv==1.0.0
pytesseract==0.3.10
opencv-python==4.8.0.74
numpy==1.23.5
Pillow==10.0.0
PyMuPDF==1.22.5
gTTS==2.3.2
```

## Структура проекта

```
text-recognition-bot/
│
├── main.py               # Основной файл с кодом бота
├── requirements.txt      # Список зависимостей
├── .env                  # Переменные окружения
├── files/                # Папка для хранения загруженных файлов
└── README.md             # Описание проекта
```

## Лицензия

Этот проект распространяется под лицензией MIT. Подробнее см. в файле LICENSE.

---
