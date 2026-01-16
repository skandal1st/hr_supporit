# Настройка синхронизации между HR Desk и SupporIT

## Обзор

HR Desk может синхронизировать данные с системой SupporIT для:
- Получения списка пользователей
- Получения оборудования сотрудников
- Обновления контактной информации пользователей в SupporIT

## Шаг 1: Получение токена доступа SupporIT

### Способ 1: Через веб-интерфейс

1. Войдите в SupporIT через браузер
2. Откройте консоль разработчика (F12)
3. Перейдите в раздел Application → Local Storage или Cookies
4. Найдите токен JWT (обычно в ключе `token` или `authToken`)

### Способ 2: Через API

```bash
# Получение токена через API
curl -X POST http://localhost:3001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your_email@example.com",
    "password": "your_password"
  }'
```

Ответ будет содержать токен:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": { ... }
}
```

### Способ 3: Создание сервисного пользователя

Для продакшена рекомендуется создать отдельного сервисного пользователя в SupporIT:

1. Создайте пользователя в SupporIT с ролью `it_specialist` или `admin`
2. Получите токен для этого пользователя через API
3. Используйте этот токен в настройках HR Desk

## Шаг 2: Настройка переменных окружения

Отредактируйте файл `.env.prod`:

```env
# URL API SupporIT
# Если SupporIT на том же сервере: http://localhost:3001/api
# Если SupporIT на другом сервере: http://supporit.teplocentral.local/api
# Если через nginx: https://supporit.teplocentral.local/api
SUPPORIT_API_URL=http://localhost:3001/api

# JWT токен для аутентификации
SUPPORIT_TOKEN=your_jwt_token_here
```

## Шаг 3: Проверка подключения

После настройки переменных окружения и перезапуска контейнеров проверьте подключение:

```bash
# Health check интеграции
curl -X GET http://hrdesk.teplocentral.local/api/v1/integrations/supporit/health \
  -H "Authorization: Bearer YOUR_HR_DESK_TOKEN"
```

Успешный ответ:
```json
{
  "status": "ok",
  "users_count": 42
}
```

## Использование синхронизации

### Синхронизация пользователей из SupporIT в HR Desk

Эта операция:
- Получает список всех пользователей из SupporIT
- Создает новых сотрудников в HR Desk (если их нет)
- Обновляет существующих сотрудников (имя, телефон)

```bash
curl -X POST http://hrdesk.teplocentral.local/api/v1/integrations/supporit/pull-users \
  -H "Authorization: Bearer YOUR_HR_DESK_TOKEN"
```

Ответ:
```json
{
  "created": 5,
  "updated": 37
}
```

### Отправка контактов из HR Desk в SupporIT

Эта операция обновляет контактную информацию пользователей в SupporIT на основе данных из HR Desk.

```bash
curl -X POST http://hrdesk.teplocentral.local/api/v1/integrations/supporit/push-contacts \
  -H "Authorization: Bearer YOUR_HR_DESK_TOKEN"
```

Ответ:
```json
{
  "updated": 15,
  "skipped": 27,
  "create_missing": false
}
```

### Получение оборудования для сотрудника

Получает список оборудования, закрепленного за сотрудником в SupporIT:

```bash
# По ID сотрудника
curl -X GET "http://hrdesk.teplocentral.local/api/v1/integrations/supporit/123" \
  -H "Authorization: Bearer YOUR_HR_DESK_TOKEN"

# По email (если ID неизвестен)
curl -X GET "http://hrdesk.teplocentral.local/api/v1/integrations/supporit/123?email=user@example.com" \
  -H "Authorization: Bearer YOUR_HR_DESK_TOKEN"
```

## Автоматическая синхронизация

В будущих версиях планируется добавить автоматическую синхронизацию по расписанию. Пока что синхронизацию нужно запускать вручную через API или через интерфейс администратора.

## Устранение неполадок

### Ошибка "Permission denied" или 401

- Проверьте правильность токена SupporIT
- Убедитесь, что токен не истек
- Проверьте, что пользователь имеет необходимые права в SupporIT

### Ошибка "Connection refused" или таймаут

- Проверьте доступность SupporIT API:
  ```bash
  curl http://localhost:3001/api/users \
    -H "Authorization: Bearer YOUR_SUPPORIT_TOKEN"
  ```
- Проверьте правильность URL в `SUPPORIT_API_URL`
- Если SupporIT на другом сервере, убедитесь, что порты открыты

### Пользователи не синхронизируются

- Проверьте логи backend:
  ```bash
  docker compose -f docker-compose.prod.yml logs backend | grep supporit
  ```
- Убедитесь, что в SupporIT есть пользователи с заполненными email
- Проверьте формат данных в SupporIT (поле `full_name` или `fullName`)

### Оборудование не находится

- Убедитесь, что в SupporIT у пользователя есть оборудование
- Проверьте правильность `owner_id` или `email`
- Проверьте логи для деталей ошибки

## Безопасность

⚠️ **Важно:**
- Храните токены в безопасном месте
- Не коммитьте `.env.prod` в git
- Используйте сервисного пользователя с минимальными правами
- Регулярно обновляйте токены
- Используйте HTTPS для API запросов в продакшене

## Примеры использования в коде

### Python (для автоматизации)

```python
import requests

HR_DESK_URL = "http://hrdesk.teplocentral.local/api/v1"
HR_DESK_TOKEN = "your_hr_desk_token"

# Синхронизация пользователей
response = requests.post(
    f"{HR_DESK_URL}/integrations/supporit/pull-users",
    headers={"Authorization": f"Bearer {HR_DESK_TOKEN}"}
)
print(response.json())

# Получение оборудования
response = requests.get(
    f"{HR_DESK_URL}/integrations/supporit/123",
    headers={"Authorization": f"Bearer {HR_DESK_TOKEN}"}
)
print(response.json())
```

### Bash скрипт

```bash
#!/bin/bash

HR_DESK_URL="http://hrdesk.teplocentral.local/api/v1"
HR_DESK_TOKEN="your_hr_desk_token"

# Синхронизация пользователей
curl -X POST "${HR_DESK_URL}/integrations/supporit/pull-users" \
  -H "Authorization: Bearer ${HR_DESK_TOKEN}"

# Отправка контактов
curl -X POST "${HR_DESK_URL}/integrations/supporit/push-contacts" \
  -H "Authorization: Bearer ${HR_DESK_TOKEN}"
```

