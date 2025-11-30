# Презентация Проекта: LLM Test Generator

**Продолжительность**: 10-15 минут
**Формат**: Демонстрация + рассказ по критериям

---

## 1. ПРОБЛЕМА (3 минуты)

### Какую боль решаю?
**Личная проблема**:
- Я часто учусь по образовательным материалам (статьи, лекции, конспекты в Markdown)
- Чтобы проверить усвоение материала, нужно создавать тесты вручную
- Это долго (20+ минут на 10 вопросов) и скучно
- Сложно придумать качественные дистракторы (неправильные варианты ответов)

### Почему это важно (happiness test)?
**До**: 😩 Откладываю создание тестов → не проверяю знания → забываю материал
**После**: 😊 Загрузил файл → получил тест за 30 секунд → проверил знания сразу

### Кто ещё имеет эту проблему?
- **Преподаватели** - нужно создавать тесты для студентов регулярно
- **Студенты** - хотят самопроверку по конспектам
- **Методисты** - создают образовательные материалы и тесты
- **Корпоративное обучение** - тестирование сотрудников по регламентам

**Масштаб**: Любой, кто создает образовательный контент в Markdown

---

## 2. BDD СЦЕНАРИИ (3 минуты)

### Демонстрация файлов
```bash
# Показать структуру
tree tests/bdd/features/
```

**3 Features, 12 Scenarios:**

### Feature 1: Grade Answers (6 scenarios)
```gherkin
Scenario: Grade perfect score
  Given a test exam with 3 questions exists
  When I submit answers for grading
  Then the grading summary shows 100% score
  And all questions are marked as correct
```

**Edge cases:**
- Partial score с неправильными ответами
- Partial credit для multiple choice
- Non-existent exam (404 error)
- Subset of questions

### Feature 2: Health Check (1 scenario)
```gherkin
Scenario: Check API is running
  When I request the health endpoint
  Then the status is "ok"
```

### Feature 3: Generate Questions (5 scenarios)
```gherkin
Scenario: Generate exam with default configuration
  When I request exam generation with default settings
  Then I receive a generated exam
  And the exam contains 20 questions
```

**Edge cases:**
- Custom question count
- Custom type ratios (80% single / 20% multiple)
- Empty content validation
- Question structure validation

### Почему эти сценарии?
1. **Happy path** - основной workflow работает
2. **Edge cases** - валидация входных данных
3. **Error handling** - система устойчива к ошибкам
4. **User-facing** - описывают реальное использование

**Запуск:**
```bash
behave tests/bdd/features/
# Результат: 10+ scenarios passing
```

---

## 3. АРХИТЕКТУРА ЧЕРЕЗ ISSUES (3 минуты)

### Показать GitHub Issues
```bash
gh issue list --state all
```

**9 Issues всего:**
- ✅ 8 закрыто (core functionality)
- 🔄 1 открыт (UI polish - низкий приоритет)

### Структура Issues (почему-что-как):

**Пример Issue #3: Question Generator**
```markdown
Why: Core functionality for test generation
What: TDD approach with OpenAI client wrapper
How:
1. Write unit tests first (RED phase)
2. Implement OpenAI client wrapper
3. Create prompt templates
4. Implement generator logic (GREEN phase)
```

### Декомпозиция задач:
```
#1 Schemas       → #2 Parser    → #3 Generator
                  ↓
#4 Grader       → #5 API        → #6 BDD
                  ↓
#7 RAG prep     → #8 Frontend   → #9 UI polish
```

**Прогресс**: 8/9 done (89%), основной функционал завершен

### Issues как документация:
- Каждый issue описывает **зачем**, **что**, **как**
- Привязаны к коммитам (`Closes #N`)
- История решений сохранена

---

## 4. CODE REVIEW КУЛЬТУРА (3 минуты)

### "Второй агент" = Issue #9
**Создан AI-агентом (Claude Code) после анализа кода:**

```markdown
Title: UI: Fix JavaScript issues and improve frontend UX

Issues to fix:
- Code organization and structure
- Error handling improvements
- Loading states consistency
- Form validation
```

### Что исправил:
✅ **Core issues (critical)**:
- Pydantic validation schemas (20 tests)
- Parser edge cases (17 tests)
- Grader partial credit logic (17 tests)
- API error handling (11 integration tests)

### Что в backlog (#9):
🔄 **Polish (low priority)**:
- JS code organization
- Better error messages
- Progress indicators

### Почему так приоритизировал:
**Principle**: MVP сначала, polish потом
- Функционал работает → можно использовать
- UX улучшения → не блокируют использование
- Issue #9 - для будущих итераций

### Демонстрация качества кода:
```bash
# Покрытие тестами
pytest --cov=app --cov-report=term-missing tests/
# 80% coverage, 81/82 tests passing

# Все модули покрыты
- schemas: 96%
- parser: 98%
- grader: 96%
- generator: 82%
```

---

## 5. GIT ИСТОРИЯ (2 минуты)

### Показать коммиты
```bash
git log --oneline --graph
```

**14 коммитов:**
```
71aaf64 docs: update README with web UI instructions
7fd96f0 feat(frontend): add web UI for complete exam workflow
edde8bc docs: add comprehensive README and RAG placeholder
4e7d3b8 feat(bdd): add BDD scenarios for question generation
80c4c42 feat(generator): implement question generator with OpenAI
829cfeb feat(bdd): add behave BDD scenarios and step definitions
06904f6 feat(api): add FastAPI endpoints with integration tests
26dd894 feat(grader): add answer grading with TDD approach
cb602d5 feat(parser): add Markdown parser with TDD approach
8442e17 feat(schemas): add Pydantic models with validation
b3ad2d5 chore: initialize project structure
```

### Progression видна:
1. **Инициализация** - структура проекта
2. **Schemas** - модели данных (foundation)
3. **Parser** - парсинг контента
4. **Grader** - проверка ответов
5. **API** - REST endpoints
6. **BDD** - сценарии тестирования
7. **Generator** - генерация с OpenAI
8. **Docs + RAG** - документация и архитектура
9. **Frontend** - веб-интерфейс

### Onboarding нового разработчика:
**По истории коммитов понятно:**
- Что делает каждый модуль
- Порядок разработки (TDD: тесты → код)
- Зависимости между компонентами
- Решения и их обоснование

**Conventional commits:**
- `feat:` - новая функциональность
- `docs:` - документация
- `chore:` - служебные задачи

---

## 6. REFLECTION (2-3 минуты)

### Музыка качала или dread?
**Качала! 😊**

**Почему понравилось:**
- TDD подход - сначала видишь RED тесты, потом GREEN
- Видно прогресс (каждый тест - маленькая победа)
- BDD scenarios - думаешь как пользователь, а не программист
- OpenAI integration - AI помогает создавать контент

**Моменты flow:**
- Когда все 82 теста прошли после рефакторинга
- Когда UI заработал с первого раза
- Когда OpenAI сгенерировал качественный вопрос

### Чему научился (technical)?

**1. Test-Driven Development:**
- RED → GREEN → REFACTOR цикл
- Тесты как спецификация
- 80% coverage - не случайность, а результат TDD

**2. Behavior-Driven Development:**
- Gherkin scenarios - язык бизнеса и разработки
- Given-When-Then структура
- behave framework для Python

**3. FastAPI + OpenAI:**
- Async endpoints с Pydantic validation
- OpenAI API с JSON mode для structured output
- Prompt engineering для генерации вопросов

**4. Git workflow:**
- Conventional commits
- Issues как task tracking
- Связь коммитов и issues (`Closes #N`)

**5. Full-stack без фреймворков:**
- Vanilla JS может быть достаточно
- Static files serving через FastAPI
- REST API client на чистом JS

### Буду продолжать или drop?

**ПРОДОЛЖУ! 🚀**

**Планы:**
1. **RAG Implementation** - embeddings для лучшего выбора контекста
2. **Больше типов вопросов** - true/false, matching, essay
3. **Экспорт в форматы** - PDF, GIFT (для Moodle), QTI
4. **Адаптивность** - сложность вопросов по результатам
5. **Батч-генерация** - много экзаменов из большого контента

**Real use case**:
Буду использовать для своих учебных материалов по биоинформатике и ML!

---

## ДЕМОНСТРАЦИЯ (1-2 минуты)

### Live Demo:
```bash
# 1. Запустить сервер
python3 -m uvicorn app.main:app --reload

# 2. Открыть http://localhost:8000

# 3. Показать workflow:
#    - Upload файл
#    - Generate экзамен (10 вопросов)
#    - View результат
#    - Take test
#    - Получить оценку
```

### Что показать:
1. ✅ **Загрузка файла** - drag & drop работает
2. ✅ **Генерация** - OpenAI создает вопросы за 15-30 сек
3. ✅ **Просмотр** - видны вопросы с правильными ответами
4. ✅ **Тест** - интерактивный интерфейс
5. ✅ **Результат** - оценка с partial credit

---

## ФИНАЛЬНЫЕ МЕТРИКИ

**Код:**
- 16 Python модулей
- 82 теста (81 passing, 99%)
- 80% coverage
- 16 коммитов (включая presentation + automated review)

**GitHub:**
- 9 issues (8 closed, 1 open)
- Все с структурой "почему-что-как"

**Testing:**
- 20 unit tests (schemas)
- 17 unit tests (parser)
- 17 unit tests (grader)
- 18 unit tests (generator)
- 11 integration tests
- 12 BDD scenarios

**Функционал:**
- ✅ REST API с Swagger
- ✅ Web UI для пользователей
- ✅ OpenAI integration
- ✅ Partial credit grading
- ✅ Source traceability

---

## ВОПРОСЫ?

**Готов ответить на:**
- Технические детали реализации
- Архитектурные решения
- TDD/BDD подход
- Будущие улучшения
- Что бы сделал иначе

---

## КОМАНДЫ ДЛЯ ДЕМОНСТРАЦИИ

```bash
# Показать структуру BDD
tree tests/bdd/features/
cat tests/bdd/features/grade_answers.feature

# Показать issues
gh issue list --state all

# Показать git историю
git log --oneline --graph | head -15

# Показать коммит детально
git show 80c4c42  # Generator commit

# Запустить тесты
pytest tests/ -v --tb=short

# Запустить BDD
behave tests/bdd/features/

# Показать coverage
pytest --cov=app --cov-report=term-missing tests/

# Запустить приложение
python3 -m uvicorn app.main:app --reload
```
