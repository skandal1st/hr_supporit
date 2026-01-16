# Руководство по развертыванию HR Desk

## Требования

- Docker и Docker Compose
- Nginx (для проксирования)
- Доступ к серверу с правами sudo

## Быстрая настройка

### 1. Подготовка переменных окружения

Скопируйте пример файла и заполните необходимые переменные:

```bash
cp env.prod.sample .env.prod
nano .env.prod
```

**Обязательные переменные для синхронизации с SupporIT:**

```env
SUPPORIT_API_URL=http://localhost:3001/api
SUPPORIT_TOKEN=your_jwt_token_here
```

**Как получить токен SupporIT:**

1. Войдите в SupporIT через веб-интерфейс
2. Откройте консоль разработчика (F12)
3. В разделе Application/Storage найдите токен в localStorage или cookies
4. Или создайте сервисного пользователя в SupporIT и получите токен через API

**Альтернативный способ получения токена:**

```bash
# Войдите в SupporIT и выполните запрос на /api/auth/login
curl -X POST http://localhost:3001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"your_email@example.com","password":"your_password"}'
```

Ответ будет содержать токен в поле `token`.

### 2. Развертывание через Docker

```bash
# Запуск развертывания
./scripts/deploy.sh

# Или вручную:
docker compose -f docker-compose.prod.yml up -d --build
```

### 3. Настройка Nginx

```bash
# Копирование конфигурации
sudo cp scripts/nginx-hrdesk.conf /etc/nginx/sites-available/hrdesk

# Создание симлинка
sudo ln -s /etc/nginx/sites-available/hrdesk /etc/nginx/sites-enabled/

# Проверка конфигурации
sudo nginx -t

# Перезагрузка nginx
sudo systemctl reload nginx
```

### 4. Настройка DNS

Убедитесь, что домен `hrdesk.teplocentral.local` указывает на IP адрес вашего сервера.

Для локальной сети можно добавить запись в `/etc/hosts`:

```
192.168.x.x hrdesk.teplocentral.local
```

## Проверка работы

### Проверка доступности сервисов

```bash
# Backend
curl http://localhost:8000/health

# Frontend
curl http://localhost:8080

# Через домен
curl http://hrdesk.teplocentral.local/health
```

### Проверка синхронизации с SupporIT

```bash
# Health check интеграции
curl -X GET http://hrdesk.teplocentral.local/api/v1/integrations/supporit/health \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Синхронизация данных

### Ручная синхронизация пользователей из SupporIT

```bash
curl -X POST http://hrdesk.teplocentral.local/api/v1/integrations/supporit/pull-users \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Отправка контактов в SupporIT

```bash
curl -X POST http://hrdesk.teplocentral.local/api/v1/integrations/supporit/push-contacts \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Получение оборудования для сотрудника

```bash
curl -X GET "http://hrdesk.teplocentral.local/api/v1/integrations/supporit/123?email=user@example.com" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Управление контейнерами

```bash
# Просмотр логов
docker compose -f docker-compose.prod.yml logs -f

# Остановка
docker compose -f docker-compose.prod.yml down

# Перезапуск
docker compose -f docker-compose.prod.yml restart

# Обновление
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

## Устранение неполадок

### Backend не запускается

```bash
# Проверка логов
docker compose -f docker-compose.prod.yml logs backend

# Проверка переменных окружения
docker compose -f docker-compose.prod.yml exec backend env | grep SUPPORIT
```

### Frontend не доступен

```bash
# Проверка логов
docker compose -f docker-compose.prod.yml logs frontend

# Проверка портов
netstat -tulpn | grep 8080
```

### Проблемы с синхронизацией

1. Проверьте доступность SupporIT API:
   ```bash
   curl http://localhost:3001/api/users \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

2. Проверьте правильность токена в `.env.prod`

3. Проверьте логи backend:
   ```bash
   docker compose -f docker-compose.prod.yml logs backend | grep supporit
   ```

### Nginx не проксирует запросы

1. Проверьте конфигурацию:
   ```bash
   sudo nginx -t
   ```

2. Проверьте логи nginx:
   ```bash
   sudo tail -f /var/log/nginx/hrdesk-error.log
   ```

3. Убедитесь, что контейнеры запущены:
   ```bash
   docker compose -f docker-compose.prod.yml ps
   ```

## Безопасность

### Настройка SSL (рекомендуется)

1. Получите SSL сертификат (Let's Encrypt или внутренний CA)

2. Раскомментируйте секцию SSL в `scripts/nginx-hrdesk.conf`

3. Укажите пути к сертификатам

4. Раскомментируйте редирект с HTTP на HTTPS

### Ограничение доступа

Можно настроить ограничение доступа по IP в nginx:

```nginx
location / {
    allow 192.168.1.0/24;
    deny all;
    # ... остальная конфигурация
}
```

## Мониторинг

### Health checks

- Backend: `http://hrdesk.teplocentral.local/api/health`
- Frontend: `http://hrdesk.teplocentral.local/`

### Логи

- Backend: `docker compose -f docker-compose.prod.yml logs backend`
- Frontend: `docker compose -f docker-compose.prod.yml logs frontend`
- Nginx: `/var/log/nginx/hrdesk-access.log` и `/var/log/nginx/hrdesk-error.log`

