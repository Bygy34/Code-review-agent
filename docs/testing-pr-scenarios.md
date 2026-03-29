# Testing PR Scenarios for AI Review Agent

Этот документ добавляет практичный способ "потрогать" MVP без реального PR в GitHub.

## Важно про ветки

- Все тестовые PR открывать в **`develop`**.
- Ветка **`main`** исключена из тестового процесса.
- Workflow `AI Code Review` срабатывает только для PR, где target branch = `develop`.

## 1) Локальная симуляция плохого PR (Python fixture)

```bash
REVIEW_FILES_PATH=examples/test-pr-fixtures/bad-pr-files.json \
DRY_RUN_OUTPUT=examples/test-pr-fixtures/bad-review-output.md \
python scripts/review_agent.py
```

Ожидаемо: в отчёте будут `blocker` и `low` находки (`password`, `api_key`, `eval`, `exec`, `TODO`).

## 2) Локальная симуляция плохого PR (C#/.NET fixture)

```bash
REVIEW_FILES_PATH=examples/test-pr-fixtures/bad-pr-files-csharp.json \
DRY_RUN_OUTPUT=examples/test-pr-fixtures/bad-review-csharp-output.md \
python scripts/review_agent.py
```

Ожидаемо: в отчёте будут сигналы по `password`, `api_key`, `TODO`.

## 3) Локальная симуляция чистого PR

```bash
REVIEW_FILES_PATH=examples/test-pr-fixtures/clean-pr-files.json \
DRY_RUN_OUTPUT=examples/test-pr-fixtures/clean-review-output.md \
python scripts/review_agent.py
```

Ожидаемо: "No high-signal issues detected".

## 4) Как тестировать на реальном PR

1. Создай ветку `test/ai-review-signal`.
2. Добавь тестовый код (например `examples/csharp-dotnet-test-app/Program.cs`) с триггерами (`TODO`, `password`, `api_key`).
3. Открой PR **в `develop`**.
4. Проверь, что workflow `AI Code Review` запустился и оставил комментарий.

## 5) Выбор runtime

- `REVIEW_AGENT_RUNTIME=python` (по умолчанию)
- `REVIEW_AGENT_RUNTIME=csharp`

Установить можно в GitHub Repository Variables.
