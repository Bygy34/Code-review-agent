# Testing PR Scenarios for AI Review Agent

Этот документ добавляет практичный способ "потрогать" MVP без реального PR в GitHub.

## 1) Локальная симуляция плохого PR

```bash
REVIEW_FILES_PATH=examples/test-pr-fixtures/bad-pr-files.json \
DRY_RUN_OUTPUT=examples/test-pr-fixtures/bad-review-output.md \
python scripts/review_agent.py
```

Ожидаемо: в отчёте будут `blocker` и `low` находки (`password`, `api_key`, `eval`, `exec`, `TODO`).

## 2) Локальная симуляция чистого PR

```bash
REVIEW_FILES_PATH=examples/test-pr-fixtures/clean-pr-files.json \
DRY_RUN_OUTPUT=examples/test-pr-fixtures/clean-review-output.md \
python scripts/review_agent.py
```

Ожидаемо: "No high-signal issues detected".

## 3) Как тестировать на реальном PR

1. Создай ветку `test/ai-review-signal`.
2. Добавь тестовый код с одним-двумя триггерами (`TODO`, `eval`), закоммить.
3. Открой PR в `main`.
4. Проверь, что workflow `AI Code Review` запустился и оставил комментарий.

## 4) Выбор runtime

- `REVIEW_AGENT_RUNTIME=python` (по умолчанию)
- `REVIEW_AGENT_RUNTIME=csharp`

Установить можно в GitHub Repository Variables.
