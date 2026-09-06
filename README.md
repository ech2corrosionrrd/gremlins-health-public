# 🌲 GREMLINS HEALTH 2.0 — Move-to-Earn & Proof-of-Adventure

> Telegram Mini App • бекенд на FastAPI • античит-рушій телеметрії • Solana Anchor

> 🇺🇦 **Мова розробки — українська.** Документація, коментарі, коміти, issues та
> PR ведуться українською; ідентифікатори в коді лишаються англійськими.
> Деталі — [`CONTRIBUTING.md`](CONTRIBUTING.md).


---

## Стан реалізації

Концептуальні документи описують продукт цілком. Ця таблиця описує **код у
цьому репозиторії**. Вона навмисне різка, щоб ніхто не планував роботу під
можливості, яких не існує.

| Ділянка | Стан | Примітки |
|---|---|---|
| Бекенд FastAPI | ✅ Працює | Авторизація, активності, гремліни, маркетплейс, квести |
| Античит-рушій | ✅ Працює | Варіативність каденсу, швидкість, вертикальна швидкість |
| Еволюція та біоми | ✅ Працює | Крива рівнів, тіри рідкості, похідні трейти |
| Запобіжники економіки | ✅ Працює | Ідемпотентність, перетини вікон, денні ліміти |
| Міграції БД | ✅ Працює | Alembic; `create_all` лише в розробці |
| Telegram Mini App | ✅ Працює | React + Vite, 5 мов, живий API-клієнт |
| Автентифікація через initData | ✅ Працює | HMAC перевіряється на сервері |
| Гаманець Solana | ⚠️ **Без доказу власності** | Адреса записується зі слів клієнта; `signMessage` немає |
| Anchor-програма | ⚠️ **Не скомпільовано** | Джерела виправлені, `anchor build` не запускався |
| Мінт cNFT | ❌ **Симуляція** | `MockSolanaService` — Solana не задіяна |
| Генерація AI-артворку | ❌ **Симуляція** | `MockAIRenderService` — модель не запускається |
| Атестація пристрою | ❌ Немає | Перевіряється довжина токена, не підпис |
| H3 «туман війни» | ❌ Немає | Повертає порожній список тайлів |
| Розрахунки в маркетплейсі | ❌ Немає | Лістинг — це рядок у БД; купівлі немає |
| AR-камера | ❌ Немає | Фото знімається справжнє, «AI-обробка» підмінює його стоком |

Усе, позначене ❌, повертає URL на `example.invalid` або `is_onchain: false` —
щоб симульований результат неможливо було сплутати зі справжнім.

---

## Швидкий старт (Windows)

Подвійний клік або запуск із термінала в корені репозиторію:

| Команда | Що робить |
|---|---|
| `start.bat` | Міграції, далі API та Telegram-бот |
| `start.bat web` | Те саме плюс dev-сервер Mini App (тільки локально) |
| `start.bat tunnel` | Те саме плюс тунель Cloudflare — **це потрібно Telegram** |
| `start.bat api` / `start.bat bot` | Лише один сервіс |
| `start.bat fast` | Пропустити міграції |
| `stop.bat` | Зупинити все |
| `stop.bat force` | Разом із дочірніми процесами (reload-воркери) |
| `stop.bat tunnel` | Зупинити лише тунель |
| `status.bat` | Що запущено, плюс проба `/health` |
| `restart.bat` | Стоп, потім старт |

Логи — в `logs\`, PID-и — в `.run\` (обидві теки в `.gitignore`). Скрипт чіпає
**тільки** процеси цього каталогу, тож dev-сервери інших проєктів на цій
машині в безпеці.

Бот не запускається з поясненням, коли `TELEGRAM_BOT_TOKEN` порожній —
інакше процес стартував би й одразу помирав.

Реалізація — `scripts/service.ps1`; `.bat`-файли є тонкими обгортками.


### Публічна адреса

Telegram відкриває Mini App лише через HTTPS, тож dev-сервер має бути
доступний по TLS. Підійде будь-який тунель — Cloudflare Tunnel, ngrok або
власний реверс-проксі. Вкажіть його в `TELEGRAM_WEBAPP_URL` і додайте хост у
`server.allowedHosts` у `vite.config.ts`, інакше Vite на кожен запит
відповідатиме «Blocked request. This host is not allowed.»

Vite проксує `/api` на бекенд, тож застосунок і API живуть на одному origin
за одним тунелем і CORS-преflight не виникає.

---

## Запуск вручну

### Бекенд

```bash
cd backend
python -m pip install -r requirements-dev.txt

cp .env.example .env
# SECRET_KEY обов'язковий — без нього застосунок не стартує:
python -c "import secrets; print(secrets.token_urlsafe(48))"

python -m alembic upgrade head       # створити схему
python -m app.seed                   # демо-квести та рейд-бос (необов'язково)
python -m uvicorn app.main:app --reload --port 8000
```

- Swagger UI: <http://localhost:8000/docs> (вимкнено, якщо `ENVIRONMENT != development`)
- Health: <http://localhost:8000/health>

### Тести

```bash
cd backend && python -m pytest          # 57 тестів
```

`tests/test_security.py` містить регресії на **кожен** обхід автентифікації та
економіки з `SECURITY.md`. Червоний тест там — блокер релізу.

### Telegram Mini App

```bash
cd apps/telegram-mini-app
npm install
cp .env.example .env.development
npm run dev
```

У звичайному браузері застосунок працює в **demo-режимі** — про це прямо каже
банер, а стан лежить у `localStorage`. Усередині Telegram він автентифікується
підписаним `initData`, і джерелом правди стає сервер.

### Docker

```bash
cp .env.example .env                 # SECRET_KEY, POSTGRES_PASSWORD, ...
docker compose up --build
```

Назовні відкритий лише фронтенд (порт `80`). Postgres, Redis і API доступні
тільки у внутрішній мережі; nginx проксує `/api` на бекенд, тож застосунок
same-origin і преflight не робить.

### Програма Solana

```bash
cd contracts
anchor build
anchor deploy --provider.cluster devnet
```

Program ID: `A9oXQuqhwkycQKPRAHTrqBYZ8v985PagPmcQvEWtSmEX`
(ключова пара в `target/deploy/gremlins_health-keypair.json`, у `.gitignore`).

> Програму **не компілювали** — Rust-тулчейну на машині не було.
> Запустіть `anchor build`, перш ніж на неї покладатись.

`initialize_config` треба виконати один раз, щоб зареєструвати ключ
бекенд-оракула. `evolve_gremlin` і `record_adventure` вимагають його підпису,
тож клієнт не може сам нарахувати собі рівні чи кроки.

---

## Багатомовність застосунку

Локаль визначається автоматично з Telegram: 🇬🇧 English (типова),
🇺🇦 Українська, 🇵🇱 Polski, 🇩🇪 Deutsch, 🇪🇸 Español. Російська не підтримується.

Це **мова продукту**, і вона не збігається з мовою розробки —
див. [`CONTRIBUTING.md`](CONTRIBUTING.md).

---

## Структура репозиторію

```
gremlin-game_nft/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py                  # залежність автентифікації (без запасного юзера)
│   │   │   └── v1/endpoints/            # auth, users, gremlins, activities, marketplace, quests
│   │   ├── core/
│   │   │   ├── config.py                # налаштування; відхиляє слабкі секрети та "*" у CORS
│   │   │   ├── security.py              # PBKDF2 600k, версіоновані хеші, JWT
│   │   │   ├── telegram_auth.py         # перевірка HMAC для initData
│   │   │   ├── rate_limit.py            # Redis + локальне ковзне вікно
│   │   │   └── database.py              # асинхронний двигун SQLAlchemy 2.0
│   │   ├── models/                      # ORM-моделі на Mapped[]
│   │   ├── schemas/                     # Pydantic v2
│   │   ├── services/
│   │   │   ├── anticheat_service.py     # справжній
│   │   │   ├── evolution_service.py     # справжній
│   │   │   ├── mock_ai_render_service.py    # СИМУЛЯЦІЯ
│   │   │   └── mock_solana_service.py       # СИМУЛЯЦІЯ
│   │   └── seed.py                      # демо-дані, тільки явним запуском
│   ├── migrations/                      # Alembic
│   └── tests/                           # 57 тестів, разом із регресіями безпеки
├── contracts/                           # Anchor-програма (за підписом оракула)
├── apps/telegram-mini-app/
│   └── src/
│       ├── lib/api.ts                   # типізований клієнт API
│       ├── hooks/useGameState.ts        # стан live/demo
│       └── components/
├── deploy/                              # nginx + systemd (не root, TLS)
├── scripts/service.ps1                  # запуск/зупинка для .bat-файлів
├── start.bat  stop.bat  status.bat  restart.bat
├── docker-compose.yml
├── CONTRIBUTING.md                      # конвенції, зокрема мова розробки
└── SECURITY.md
```

---


---
*Gremlins Health Community • 2026*
