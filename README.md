# AI Code Review Agent MVP

Базовый MVP для автоматического AI-код-ревью в GitHub Pull Request.

## Что делает MVP

- Запускается на событиях PR (`opened`, `synchronize`, `reopened`) при target branch = `develop`.
- Собирает список изменённых файлов через GitHub API.
- Формирует короткий review summary (пока rule-based эвристика, чтобы MVP был рабочим без внешних зависимостей).
- Публикует комментарий в PR через `GITHUB_TOKEN`.
- Поддерживает 2 runtime: **Python** (по умолчанию) и **C#/.NET 8**.
- Поддерживает локальный **fixture dry-run**, чтобы тестировать логику без реального PR.

## Структура

- `.github/workflows/ai-code-review.yml` — GitHub Actions workflow (только PR в `develop`).
- `scripts/review_agent.py` — Python-агент (stdlib-only).
- `scripts/csharp/ReviewAgent.csproj` + `scripts/csharp/Program.cs` — C#-агент.
- `examples/csharp-dotnet-test-app/` — тестовый C#/.NET код для PR-проверок.
- `examples/test-pr-fixtures/` — тестовые PR-фикстуры для dry-run.
- `docs/testing-pr-scenarios.md` — как проверять агент локально и в реальном PR.
- `config/review-rules.yaml` — пример правил/политик ревью.
- `prompts/review_prompt.md` — шаблон prompt для будущего LLM-режима.


## Политика веток

- Все новые PR открываем **в `develop`**.
- Текущие и будущие тестовые PR также переводим на base branch `develop`.
- `main` пока не используется для тестовых прогонов.
- CI workflow `Enforce develop as PR base` блокирует PR с base branch != `develop`.
- Каждый PR создаём из **новой отдельной ветки** (не переиспользуем старую).

## Быстрый запуск

1. Добавьте файлы в репозиторий.
2. Убедитесь, что у workflow есть права `pull-requests: write`.
3. (Опционально) для переключения runtime создайте Repository Variable:
   - `REVIEW_AGENT_RUNTIME=python` (default), или
   - `REVIEW_AGENT_RUNTIME=csharp`.
4. Откройте/обновите PR в `develop` — агент оставит summary-комментарий.

## Локальный dry-run (без GitHub PR)

```bash
REVIEW_FILES_PATH=examples/test-pr-fixtures/bad-pr-files.json \
DRY_RUN_OUTPUT=review-output.md \
python scripts/review_agent.py
```

## Дальнейшее развитие

- Подключить LLM API и анализ диффа по строкам.
- Добавить confidence score и severity (blocker/high/medium/low).
- Добавить suppressions (`ai-review: ignore`) и сбор метрик точности.
