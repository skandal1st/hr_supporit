# Быстрый старт для развертывания HR Desk

## Что было настроено

✅ Конфигурация nginx для домена `hrdesk.teplocentral.local`  
✅ Docker Compose для продакшена  
✅ Скрипт автоматического развертывания  
✅ Документация по синхронизации с SupporIT  
✅ Исправления в коде интеграции  

## Следующие шаги

### 1. Настройка переменных окружения

```bash
cd hr_supporit
cp env.prod.sample .env.prod
nano .env.prod  # или используйте любой редактор
```

**Обязательно укажите:**
- `SUPPORIT_API_URL` - URL API SupporIT (например: `http://localhost:3001/api`)
- `SUPPORIT_TOKEN` - JWT токен для доступа к SupporIT API

**Как получить токен SupporIT:**
```bash
curl -X POST http://localhost:3001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"your_email@example.com","password":"your_password"}'
```

### 2. Развертывание

```bash
# Сделайте скрипт исполняемым (если еще не сделано)
chmod +x scripts/deploy.sh

# Запустите развертывание
./scripts/deploy.sh
```

### 3. Настройка Nginx

```bash
# Скопируйте конфигурацию
sudo cp scripts/nginx-hrdesk.conf /etc/nginx/sites-available/hrdesk

# Создайте симлинк
sudo ln -s /etc/nginx/sites-available/hrdesk /etc/nginx/sites-enabled/

# Проверьте конфигурацию
sudo nginx -t

# Перезагрузите nginx
sudo systemctl reload nginx
```

### 4. Настройка DNS

Убедитесь, что домен `hrdesk.teplocentral.local` указывает на IP вашего сервера.

Для локальной сети добавьте в `/etc/hosts`:
```
192.168.x.x hrdesk.teplocentral.local
```

### 5. Проверка работы

```bash
# Проверка backend
curl http://hrdesk.teplocentral.local/api/health

# Проверка синхронизации с SupporIT
curl -X GET http://hrdesk.teplocentral.local/api/v1/integrations/supporit/health \
  -H "Authorization: Bearer YOUR_HR_DESK_TOKEN"
```

## Полезные команды

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

## Документация

- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Полное руководство по развертыванию
- **[SYNC_SETUP.md](SYNC_SETUP.md)** - Настройка синхронизации с SupporIT
- **[README.md](README.md)** - Общая информация о проекте

## Поддержка

При возникновении проблем:
1. Проверьте логи: `docker compose -f docker-compose.prod.yml logs`
2. Проверьте конфигурацию nginx: `sudo nginx -t`
3. Проверьте доступность портов: `netstat -tulpn | grep -E '8000|8080'`

