# HR-IT Lifecycle Manager

Минимальный каркас MVP для управления жизненным циклом сотрудников (HR + IT).

## Что реализовано
- Backend API (FastAPI): сотрудники, отделы, должности, HR-заявки, телефонная книга, дни рождения, оргструктура, аудит, интеграции (mock).
- Frontend SPA (React): страницы телефонной книги, дней рождения, оргструктуры, HR-панели, аудита.
- RBAC через JWT, bootstrap-пользователь.

## Быстрый старт (backend)
Требуется Python 3.11/3.12 (на 3.14 `pydantic-core` собирается из исходников и может зависнуть).
```bash
cd /home/skandal1st/projects/HR_desk/backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Запуск через Docker
```bash
cd /home/skandal1st/projects/HR_desk
docker compose up --build
```
Откройте `http://localhost:8080` (API проксируется через nginx на `/api/*`).
Файл базы SQLite будет лежать в `backend/data/hr_desk.db`.

## Прод‑развертывание

Подробное руководство: **[DEPLOYMENT.md](DEPLOYMENT.md)**

### Быстрый старт

```bash
cd hr_supporit
cp env.prod.sample .env.prod
# Отредактируйте .env.prod и укажите настройки синхронизации с SupporIT
./scripts/deploy.sh
```

### Настройка домена hrdesk.teplocentral.local

1. Настройте nginx (см. [DEPLOYMENT.md](DEPLOYMENT.md)):
   ```bash
   sudo cp scripts/nginx-hrdesk.conf /etc/nginx/sites-available/hrdesk
   sudo ln -s /etc/nginx/sites-available/hrdesk /etc/nginx/sites-enabled/
   sudo systemctl reload nginx
   ```
2. Убедитесь, что домен указывает на IP сервера

## Синхронизация с SupporIT

HR Desk может синхронизировать данные с системой SupporIT. Подробная инструкция по настройке: **[SYNC_SETUP.md](SYNC_SETUP.md)**

### Быстрая настройка

1. Получите JWT токен из SupporIT (см. [SYNC_SETUP.md](SYNC_SETUP.md))
2. Настройте переменные в `.env.prod`:
   ```
   SUPPORIT_API_URL=http://localhost:3001/api
   SUPPORIT_TOKEN=your_jwt_token_here
   ```
3. Проверьте подключение: `GET /api/v1/integrations/supporit/health`

### Доступные операции синхронизации

- `GET /api/v1/integrations/supporit/health` — проверка соединения
- `POST /api/v1/integrations/supporit/pull-users` — подтянуть пользователей из SupporIT в HR
- `POST /api/v1/integrations/supporit/push-contacts` — обновить контакты в SupporIT из HR
- `GET /api/v1/integrations/supporit/{employee_id}` — получить оборудование сотрудника

## Интеграция Active Directory
```
AD_SERVER=ldaps://ad.example.com
AD_USER=CN=svc-hr,OU=Service,DC=example,DC=com
AD_PASSWORD=secret
AD_BASE_DN=OU=Users,DC=example,DC=com
AD_DOMAIN=example.com
AD_USE_SSL=true
```
Ручная синхронизация: `POST /api/v1/integrations/ad/pull-users`.

## Интеграция Mailcow
```
MAILCOW_API_URL=https://mail.example.com
MAILCOW_API_KEY=api_key
```
Ящики создаются/блокируются при приёме/увольнении.

## Интеграция 1С ЗУП
```
ZUP_API_URL=https://1c.example.com/odata/employees
ZUP_USERNAME=user
ZUP_PASSWORD=pass
```
Ручная синхронизация: `POST /api/v1/integrations/zup/pull-users`.

## Автоматическая обработка заявок
HR backend раз в минуту проверяет заявки с датой выхода/увольнения и автоматически:
- создаёт учётные записи при приёме,
- блокирует учётные записи при увольнении.

## Тестовый администратор
По умолчанию создаётся администратор:
- email: `utkin@teplocentral.org`
- пароль: `23solomon7`
Отключить можно через `SEED_ADMIN_ENABLED=false`.

## Быстрый старт (frontend)
```bash
cd /home/skandal1st/projects/HR_desk/frontend
npm install
npm run dev
```

## Первичный доступ
Создайте первого пользователя:
```bash
curl -X POST http://localhost:8000/api/v1/auth/bootstrap \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin123","role":"hr"}'
```

После этого войдите через UI или получите токен `/auth/login`.
