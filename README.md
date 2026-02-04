# Podcats AI

Минимальный сервис для генерации подкаста из текстового файла. Внутри используется репозиторий [open-notebook](https://github.com/lfnovo/open-notebook) как источник промптов для структуры подкаста.

## Как работает
1. Вы загружаете `.txt` файл.
2. Сервис строит краткий план, формирует диалог «Ведущий/Гость» и генерирует MP3 с озвучкой.
3. Для контекста используются шаблоны из `vendor/open-notebook/prompts/podcast`.

## Запуск

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Откройте `http://localhost:8000` и загрузите файл.

## Примечания
- Аудио сохраняется в `output/podcast.mp3`.
- Если нужен другой голос или язык, можно расширить модуль `app/podcast.py`.
