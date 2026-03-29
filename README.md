# AI Code Review Agent MVP

Базовый MVP для автоматического AI-код-ревью в GitHub Pull Request.

## Что делает MVP

- Запускается на событиях PR (`opened`, `synchronize`, `reopened`).
- Собирает список изменённых файлов через GitHub API.
- Формирует короткий review summary (пока rule-based эвристика, чтобы MVP был рабочим без внешних зависимостей).
- Публикует комментарий в PR через `GITHUB_TOKEN`.

## Структура

- `.github/workflows/ai-code-review.yml` — GitHub Actions workflow.
- `scripts/review_agent.py` — основной скрипт агента.
- `config/review-rules.yaml` — пример правил/политик ревью.
- `prompts/review_prompt.md` — шаблон prompt для будущего LLM-режима.

## Быстрый запуск

1. Добавьте файлы в репозиторий.
2. Убедитесь, что у workflow есть права `pull-requests: write`.
3. Откройте/обновите PR — агент оставит summary-комментарий.

## Дальнейшее развитие

- Подключить LLM API и анализ диффа по строкам.
- Добавить confidence score и severity (blocker/high/medium/low).
- Добавить suppressions (`ai-review: ignore`) и сбор метрик точности.
