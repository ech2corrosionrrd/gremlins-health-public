# Розгортання

Є два підтримані шляхи. Оберіть один.

- **Docker Compose** — рекомендований. Один хост, усе зв'язано.
- **systemd + nginx на хості** — для наявних Postgres/Redis або жорсткішого
  контролю.

Перед будь-яким із них: прочитайте [`../SECURITY.md`](../SECURITY.md) і
**відкличте витеклий токен Telegram-бота**.

---

## Перед стартом

- [ ] Токен бота відкликано та перевидано через @BotFather
- [ ] Згенеровано новий `SECRET_KEY` — `python3 -c "import secrets; print(secrets.token_urlsafe(48))"`
- [ ] `.env` створено з `.env.example`, `chmod 600`, власник — сервісний користувач
- [ ] `.env` **не** відстежується git'ом — `git check-ignore -v .env` має дати збіг
- [ ] `BACKEND_CORS_ORIGINS` містить ваш реальний домен і жодної `*`
- [ ] A-запис DNS вказує на сервер
- [ ] `ENVIRONMENT=production` (це вимикає `/docs` і вмикає перевірки конфігурації)

Застосунок відмовляється стартувати в проді, якщо `DATABASE_URL` усе ще
вказує на SQLite, якщо в `BACKEND_CORS_ORIGINS` є `localhost` або якщо
`SECRET_KEY` дорівнює дефолтній заглушці. Це навмисно — виправте конфігурацію,
не обходьте перевірку.

---

## Шлях A — Docker Compose

```bash
git clone <repo> /var/www/gremlins-health
cd /var/www/gremlins-health

cp .env.example .env
chmod 600 .env
$EDITOR .env            # SECRET_KEY, POSTGRES_PASSWORD, TELEGRAM_BOT_TOKEN, домен

docker compose up -d --build
docker compose exec backend python -m alembic upgrade head
docker compose exec backend python -m app.seed      # демо-контент, необов'язково
```

Назовні відкрито лише порт 80, і то контейнером фронтенду. Postgres, Redis і
API живуть у внутрішній мережі та ззовні недосяжні.

### TLS

Compose віддає звичайний HTTP. Термінуйте TLS хостовим nginx попереду або
поставте реверс-проксі на кшталт Caddy чи Traefik. Telegram вимагає HTTPS для
Mini App у проді.

### Експлуатація

```bash
docker compose logs -f backend
docker compose ps
docker compose exec timescaledb pg_dump -U gremlins gremlins_health > backup.sql
docker compose pull && docker compose up -d --build   # оновлення
```

---

## Шлях B — systemd + nginx на хості

```bash
sudo bash deploy/setup_hetzner.sh     # пакети, фаєрвол, сервісний акаунт
```

Далі:

```bash
sudo -u gremlins git clone <repo> /var/www/gremlins-health
cd /var/www/gremlins-health/backend

sudo -u gremlins python3 -m venv .venv
sudo -u gremlins .venv/bin/pip install -r requirements.txt

sudo -u gremlins cp .env.example .env
sudo $EDITOR .env
sudo chmod 600 .env && sudo chown gremlins:gremlins .env

sudo -u gremlins .venv/bin/python -m alembic upgrade head
```

Зібрати фронтенд:

```bash
cd ../apps/telegram-mini-app
npm ci
VITE_API_URL=/api npm run build       # same-origin; nginx проксує /api
```

Встановити юніти:

```bash
sudo cp deploy/gremlins-api.service deploy/gremlins-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now gremlins-api gremlins-bot
sudo systemctl status gremlins-api
```

nginx і TLS:

```bash
sudo cp deploy/nginx.conf /etc/nginx/sites-available/gremlins
sudo sed -i 's/your-domain.example/ВАШ_РЕАЛЬНИЙ_ДОМЕН/g' /etc/nginx/sites-available/gremlins
sudo ln -sf /etc/nginx/sites-available/gremlins /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx

sudo certbot --nginx -d ВАШ_РЕАЛЬНИЙ_ДОМЕН
```

Для цього шляху в `.env` має бути `TRUSTED_PROXY_COUNT=1` — один хоп nginx.
Без цього rate limiter бачить усі запити як `127.0.0.1` і душить усіх
користувачів одним спільним бакетом.

---

## Налаштування Telegram

У @BotFather:

- `/setmenubutton` → ваш бот → `https://ВАШ_ДОМЕН` → підпис кнопки
- `/setdomain` → ваш бот → `ВАШ_ДОМЕН`

`TELEGRAM_WEBAPP_URL` у `.env` має збігатися точно, разом зі схемою.

---

## Перевірка після розгортання

```bash
curl -s https://ВАШ_ДОМЕН/healthz | jq

# Має бути 401. Якщо будь-який повертає дані — зупиніться й розберіться.
curl -s -o /dev/null -w '%{http_code}\n' https://ВАШ_ДОМЕН/api/v1/users/me
curl -s -o /dev/null -w '%{http_code}\n' -X POST https://ВАШ_ДОМЕН/api/v1/activities/sync \
     -H 'Content-Type: application/json' -d '{}'

# У проді має бути 404 — docs вимкнені.
curl -s -o /dev/null -w '%{http_code}\n' https://ВАШ_ДОМЕН/docs
```

Далі проженіть набір тестів безпеки на розгорнутому коміті:

```bash
cd backend && python -m pytest tests/test_security.py -v
```

---

## Резервні копії

Тут нічого не автоматизовано. Як мінімум — щонічний `pg_dump` у сховище поза
хостом:

```bash
0 3 * * * docker compose -f /var/www/gremlins-health/docker-compose.yml exec -T \
  timescaledb pg_dump -U gremlins gremlins_health | gzip > /backups/gremlins-$(date +\%F).sql.gz
```

Перевірте відновлення до того, як воно знадобиться.
