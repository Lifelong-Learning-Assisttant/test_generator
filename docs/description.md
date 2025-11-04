
# 0) Цель MVP (очень коротко)

* Вход: один или несколько **Markdown**-файлов с учебным материалом (медицинская тематика).
* Выход 1: **сгенерированный тест** (по умолчанию — single choice / multiple choice).
* Выход 2: **оценка ответов** по ключам (автопроверка).
* Всё как **два API-модуля**: `/generate` и `/grade`, со Swagger, с тестами «сначала тест — потом код».

---

# 1) Техстек и принципы

* **Python + FastAPI** (Swagger/OpenAPI из коробки), **uvicorn**.
* **Tests-first**: `pytest` (юнит/интеграция) → затем **BDD** (`behave`) на сценарии «как юзер».
* Разворачивание без БД (файлы на диске).
* Лёгкий **RAG** (опционально): разбивка Markdown на чанки + эмбеддинги OpenAI → подбор контекста при генерации.
* Ключи/настройки: `.env` (`OPENAI_API_KEY`, при нужде `OPENAI_BASE`).
* Авто-коммит прогресса в GitHub после значимых шагов (скрипт).

---

# 2) Структура репо

```
/app
  /api
    generate.py        # эндпоинт /generate
    grade.py           # эндпоинт /grade
    health.py
  /core
    md_ingest.py       # парсер Markdown -> разделы/чанки
    chunker.py         # разбиение и метаданные
    retriever.py       # простой поиск + (опц.) эмбеддинги
    qgen.py            # генерация вопросов (MCQ/SCQ) по контексту
    grader.py          # проверка ответов по ключам
    schemas.py         # Pydantic-модели
    config.py          # парсинг YAML-конфига
  /services
    openai_client.py   # обёртка OpenAI (chat + embeddings)
    autocommit.py      # авто-коммит в GitHub
  /templates
    prompts.md         # промпт-шаблоны генерации
  /examples
    config.example.yaml
    sample_med.md
    sample_exam.json
/tests
  /unit                # pytest юнит-тесты (красные -> зелёные)
  /integration
  /bdd
    /features          # behave *.feature
      generate_questions.feature
      grade_answers.feature
    /steps             # step definitions
.env.example
README.md
pyproject.toml / requirements.txt
```

---

# 3) Конфиг (дефолты + можно переопределять)

```yaml
# /examples/config.example.yaml
input:
  files:
    - "examples/sample_med.md"   # список Markdown-файлов
  language: "ru"

generation:
  total_questions: 20
  types:                   # какие типы включать
    single_choice: 0.7     # доли
    multiple_choice: 0.3
  difficulty: "mixed"      # easy|medium|hard|mixed
  seed: 42
  rag:
    enabled: true
    chunk_size: 800        # символов
    chunk_overlap: 150
    top_k: 3               # сколько чанков в контекст
    embeddings: "openai:text-embedding-3-small"

sources:
  include_headings: ["Диагностика", "Тактика ведения"]  # можно ограничить разделы
  exclude_headings: []

grading:
  # на будущее: веса за сложность и т.п.
  partial_credit_for_multiple_choice: true

export:
  dir: "out"
  format: "json"           # json|csv
```

Если конфиг не передан — берём дефолты.

---

# 4) Схемы данных (Pydantic / OpenAPI)

```json
// Question
{
  "id": "q-001",
  "type": "single_choice",            // single_choice | multiple_choice
  "stem": "Какой признак характерен для ...?",
  "options": ["A", "B", "C", "D"],
  "correct": [2],                     // индексы правильных (для single_choice — один)
  "source_refs": [
    {"file":"sample_med.md","heading":"Диагностика","start":1020,"end":1320}
  ],
  "meta": {"difficulty":"medium","tags":["акушерство"]}
}

// Exam (результат генерации)
{
  "exam_id":"ex-123",
  "questions":[ /* Question[] */ ],
  "config_used":{ /* нормализованный YAML */ }
}

// GradeRequest
{
  "exam_id":"ex-123",
  "answers":[ {"question_id":"q-001","choice":[2]} ]
}

// GradeResponse
{
  "exam_id":"ex-123",
  "summary":{"total":20,"correct":16,"score_percent":80.0},
  "per_question":[
    {"question_id":"q-001","is_correct":true,"expected":[2],"given":[2]}
  ]
}
```

---

# 5) API (контракт)

* `POST /api/generate`

  * Body: `{ "config_yaml": "<yaml-string>" }` **или** `{ "config": { ... } }`
    (если пусто — дефолты; файлы берутся из `config.input.files`)
  * Ответ: `Exam` (см. выше) + файл `out/exam_{exam_id}.json`
* `POST /api/grade`

  * Body: `GradeRequest` (можно, не зная `exam_id`, прислать `{ "questions":[...], "answers":[...] }`)
  * Ответ: `GradeResponse`
* `GET /health` → `{status:"ok"}`
* Swagger: `/docs`, OpenAPI JSON: `/openapi.json`

---

# 6) Поведение генератора (минимум)

1. Парсим Markdown: заголовки → разделы, абзацы, списки, таблицы (как текст).
2. Режем на чанки (см. конфиг).
3. Если `rag.enabled`: считаем эмбеддинги, для каждого вопроса подбираем `top_k` чанков.
4. Генерим **single/multiple choice** (по долям), с 3–5 вариантами, один/несколько правильных.
5. К каждому вопросу сохраняем `source_refs` (из каких чанков тянули факты).
6. Опционально вычищаем дубликаты, проверяем answerability (короткий автопромпт «есть ли однозначный ответ в контексте?»).

---

# 7) Поведение проверяющего модуля (минимум)

* Для `single_choice`/`multiple_choice` сверяем индексы.
* Считаем **partial credit** для multiple choice (настраиваемо).
* Возвращаем **сводку** и **пер-вопрос** результаты, чтобы можно было отрисовать отчёт.

---

# 8) Tests-first (TDD → BDD)

* **Юнит-тесты (pytest)** — пишем до реализации:

  * `test_md_ingest.py`: корректно разбираем заголовки/абзацы.
  * `test_chunker.py`: размеры/пересечения.
  * `test_qgen.py`: при фиксированном seed выдаёт детерминированные структуры; есть правильное число опций; нет пустых вариантов; есть `source_refs`.
  * `test_grader.py`: верная проверка single/multiple; partial credit.
  * `test_config.py`: парсинг YAML, дефолты.
* **Интеграционные**: `POST /generate` + `POST /grade` на `examples/sample_med.md`.
* **BDD (behave)** — после базовых юнитов:

  * `generate_questions.feature` — «Как автор, загружаю материалы и получаю 20 вопросов нужных типов».
  * `grade_answers.feature` — «Как преподаватель, отправляю ответы и получаю сводку 80%».
* CI: запуск `pytest` + `behave`, порог покрытия (например, 80%).

---

# 9) Авто-коммит в GitHub

* Скрипт `/app/services/autocommit.py`:

  * Коммитит изменённые файлы с сообщением вида:
    `feat(generate): exam ex-123 (20q)` или `test(bdd): pass grade scenario`
  * Берёт `GIT_USER`, `GIT_EMAIL` из `.env`; пушит по `GITHUB_TOKEN` (или через SSH ключ).
* Вызовы:

  * после успешного `POST /generate` → коммит файла `out/exam_{id}.json` + `config_used`.
  * после успешного `POST /grade` → коммит `out/grade_{id}.json`.

---

# 10) Пример Markdown (медицина, учебный)

```markdown
# Гестационная гипертензия и преэклампсия

## Определения
- **Гестационная гипертензия**: артериальное давление ≥140/90 мм рт. ст. после 20-й недели беременности без признаков протеинурии.
- **Преэклампсия**: гипертензия после 20-й недели в сочетании с протеинурией **или** признаками поражения органов-мишеней.

## Факторы риска
- Первая беременность, многоплодие, ожирение (ИМТ ≥30), возраст матери <18 или >40, семейный анамнез преэклампсии, хроническая гипертензия.

## Диагностика
- Измерение АД в покое в двух повторениях с интервалом ≥4 часа.
- Протеинурия: ≥300 мг/сут **или** отношение белок/креатинин мочи ≥0.3.
- Оценка органных проявлений: тромбоцитопения, повышение АЛТ/АСТ, головная боль, нарушения зрения, отёк лёгких.

## Тактика ведения (общие принципы)
- Мониторинг АД и симптомов, лабораторный контроль.
- Антигипертензивная терапия при АД ≥160/110.
- Рассмотрение родоразрешения при ухудшении состояния матери/плода или при сроке ≥37 недель.
```

---

# 11) Сценарий BDD (пример)

```gherkin
Feature: Генерация тестов из Markdown
  Scenario: Автор загружает материалы и получает 20 вопросов
    Given конфиг с файлом "examples/sample_med.md" и total_questions 20
    When я вызываю API /generate
    Then я получаю 20 вопросов
    And не менее 1 вопроса имеет type "multiple_choice"
    And у каждого вопроса есть хотя бы 3 варианта и source_refs

Feature: Проверка ответов
  Scenario: Преподаватель отправляет ответы и видит результат
    Given есть exam ex-123
    And есть ответы с 16 правильными
    When я вызываю API /grade
    Then в summary.score_percent >= 80
```

---

# 12) Мини-план работ (в днях)

1. **Тесты (юнит) красными** + каркас схем/эндпоинтов — 2 дн.
2. Парсер Markdown + чанкер + тесты в зелёный — 2 дн.
3. Базовый генератор MCQ/SCQ (без RAG) + тесты — 3 дн.
4. Лёгкий RAG (эмбеддинги, top-k) + дедуп — 2 дн.
5. Грейдер (single/multiple + partial) + интеграционные тесты — 2 дн.
6. BDD сценарии + доводка API/Swagger — 2 дн.
7. Авто-коммиты + README/пример конфигов — 1 дн.

(Можно двигать, если нужна супер-минималка — пункты 4 и 7 позже.)

---

# 13) Что отдать на выходе

* Работающий сервер (`/generate`, `/grade`, `/docs`) + примеры.
* `examples/sample_med.md`, `examples/config.example.yaml`, `out/exam_*.json`.
* Тесты (pytest + behave), CI-скрипт, автокоммит.
* README с «как запустить» (локально + Docker, если надо).

Если захочешь — могу сразу сгенерить скелет репозитория (дерево папок, файлы-заглушки под тесты и примеры), чтобы дев стартанул с нуля без потерь времени.

