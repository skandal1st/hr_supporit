# Интеграция с 1С ЗУП

## Обзор

HR Desk поддерживает двустороннюю интеграцию с 1С ЗУП:

1. **Синхронизация данных** — подтягивание сотрудников, отделов, должностей из ЗУП
2. **Webhook** — автоматическое создание HR-заявок при приёме/увольнении в ЗУП

## Настройка

### 1. Переменные окружения

Добавьте в `.env.prod`:

```env
# URL OData сервиса 1С ЗУП
ZUP_API_URL=http://1c-server/zup/odata/standard.odata

# Логин и пароль для доступа к OData API
ZUP_USERNAME=odata_user
ZUP_PASSWORD=odata_password

# Секретный токен для webhook (опционально)
ZUP_WEBHOOK_TOKEN=your-secret-token-here
```

### 2. Настройка 1С ЗУП

#### Публикация OData сервиса

1. Откройте конфигуратор 1С ЗУП
2. Перейдите в **Администрирование → Публикация на веб-сервере**
3. Включите **OData** для нужных справочников:
   - `Catalog_Сотрудники`
   - `Catalog_ПодразделенияОрганизаций`
   - `Catalog_Должности`

#### Создание пользователя для API

1. Создайте пользователя с правами на чтение справочников
2. Используйте его логин/пароль в настройках HR Desk

### 3. Перезапуск после настройки

```bash
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d
```

## Синхронизация данных

### Полная синхронизация

Синхронизирует отделы → должности → сотрудников (в правильном порядке):

```bash
curl -X POST http://hrdesk.teplocentral.local/api/v1/zup/sync/all \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Ответ:
```json
{
  "departments": {"created": 15, "updated": 0, "errors": 0},
  "positions": {"created": 42, "updated": 0, "errors": 0},
  "employees": {"created": 152, "updated": 0, "errors": 0}
}
```

### Отдельная синхронизация

```bash
# Только отделы
curl -X POST http://hrdesk.teplocentral.local/api/v1/zup/sync/departments \
  -H "Authorization: Bearer YOUR_TOKEN"

# Только должности
curl -X POST http://hrdesk.teplocentral.local/api/v1/zup/sync/positions \
  -H "Authorization: Bearer YOUR_TOKEN"

# Только сотрудники
curl -X POST http://hrdesk.teplocentral.local/api/v1/zup/sync/employees \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Синхронизируемые поля

#### Сотрудники
- ФИО
- Дата рождения
- Телефон
- Email
- Отдел (по external_id)
- Должность (по external_id)
- Статус (активен/уволен)

#### Отделы
- Название
- Родительский отдел

#### Должности
- Название

## Webhook для событий

### Настройка в 1С

В 1С ЗУП настройте HTTP-сервис или обработку, которая при проведении документов:
- **Приём на работу** → отправляет POST запрос на `/api/v1/zup/webhook`
- **Увольнение** → отправляет POST запрос на `/api/v1/zup/webhook`

### Формат запроса

**URL:** `POST http://hrdesk.teplocentral.local/api/v1/zup/webhook`

**Headers:**
```
Content-Type: application/json
X-ZUP-Token: your-secret-token-here  # если настроен ZUP_WEBHOOK_TOKEN
```

#### Приём на работу

```json
{
  "event_type": "hire",
  "data": {
    "employee_id": "12345-guid-from-1c",
    "full_name": "Иванов Иван Иванович",
    "department": "Отдел продаж",
    "position": "Менеджер по продажам",
    "effective_date": "2024-01-15",
    "needs_it_equipment": true
  }
}
```

#### Увольнение

```json
{
  "event_type": "fire",
  "data": {
    "employee_id": "12345-guid-from-1c",
    "effective_date": "2024-02-01"
  }
}
```

### Ответ

```json
{
  "status": "ok",
  "event": "hire",
  "result": {
    "employee_id": 123,
    "hr_request_id": 456,
    "supporit_ticket_created": true
  }
}
```

### Что происходит при получении события

#### При приёме (hire):
1. Создаётся/обновляется сотрудник в HR Desk
2. Создаётся HR-заявка типа "hire"
3. Автоматически создаётся тикет в SupporIT с информацией для онбординга

#### При увольнении (fire):
1. Находится сотрудник по external_id
2. Создаётся HR-заявка типа "fire"
3. Автоматически создаётся тикет в SupporIT с информацией для оффбординга

## Альтернативные endpoints

Если настройка webhook в 1С затруднена, можно использовать отдельные endpoints:

```bash
# Приём на работу
curl -X POST http://hrdesk.teplocentral.local/api/v1/zup/event/hire \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "employee_id": "12345-guid",
    "full_name": "Иванов Иван Иванович",
    "department": "Отдел продаж",
    "position": "Менеджер",
    "effective_date": "2024-01-15",
    "needs_it_equipment": true
  }'

# Увольнение
curl -X POST http://hrdesk.teplocentral.local/api/v1/zup/event/fire \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "employee_id": "12345-guid",
    "effective_date": "2024-02-01"
  }'
```

## Пример кода для 1С

### Отправка webhook из 1С

```bsl
Процедура ОтправитьСобытиеВHRDesk(ТипСобытия, ДанныеСотрудника)
    
    HTTPСоединение = Новый HTTPСоединение("hrdesk.teplocentral.local");
    
    Заголовки = Новый Соответствие;
    Заголовки.Вставить("Content-Type", "application/json");
    Заголовки.Вставить("X-ZUP-Token", "your-secret-token");
    
    Данные = Новый Структура;
    Данные.Вставить("event_type", ТипСобытия);
    Данные.Вставить("data", ДанныеСотрудника);
    
    ЗаписьJSON = Новый ЗаписьJSON;
    ЗаписьJSON.УстановитьСтроку();
    ЗаписатьJSON(ЗаписьJSON, Данные);
    ТелоЗапроса = ЗаписьJSON.Закрыть();
    
    HTTPЗапрос = Новый HTTPЗапрос("/api/v1/zup/webhook", Заголовки);
    HTTPЗапрос.УстановитьТелоИзСтроки(ТелоЗапроса);
    
    Попытка
        Ответ = HTTPСоединение.ВызватьHTTPМетод("POST", HTTPЗапрос);
        Если Ответ.КодСостояния <> 200 Тогда
            // Обработка ошибки
        КонецЕсли;
    Исключение
        // Логирование ошибки
    КонецПопытки;
    
КонецПроцедуры
```

### Вызов при проведении документа "Приём на работу"

```bsl
Процедура ПриПроведении(Отказ)
    
    ДанныеСотрудника = Новый Структура;
    ДанныеСотрудника.Вставить("employee_id", Строка(Сотрудник.УникальныйИдентификатор()));
    ДанныеСотрудника.Вставить("full_name", Сотрудник.Наименование);
    ДанныеСотрудника.Вставить("department", Подразделение.Наименование);
    ДанныеСотрудника.Вставить("position", Должность.Наименование);
    ДанныеСотрудника.Вставить("effective_date", Формат(ДатаПриема, "ДФ=yyyy-MM-dd"));
    ДанныеСотрудника.Вставить("needs_it_equipment", Истина);
    
    ОтправитьСобытиеВHRDesk("hire", ДанныеСотрудника);
    
КонецПроцедуры
```

## Устранение неполадок

### Ошибка "ZUP_API_URL не настроен"

Убедитесь, что в `.env.prod` указан URL:
```env
ZUP_API_URL=http://1c-server/zup/odata/standard.odata
```

### Синхронизация возвращает 0 записей

1. Проверьте доступность OData:
   ```bash
   curl -u user:password "http://1c-server/zup/odata/standard.odata/Catalog_Сотрудники?\$format=json"
   ```

2. Проверьте права пользователя в 1С

3. Проверьте, опубликован ли OData сервис

### Webhook возвращает 401

Проверьте заголовок `X-ZUP-Token` и значение `ZUP_WEBHOOK_TOKEN` в `.env.prod`

### Тикет не создаётся в SupporIT

1. Проверьте настройки `SUPPORIT_API_URL` и `SUPPORIT_TOKEN`
2. Проверьте логи: `docker compose -f docker-compose.prod.yml logs backend`

## Автоматизация

### Cron для регулярной синхронизации

Добавьте в crontab:

```bash
# Синхронизация каждый час
0 * * * * curl -X POST http://hrdesk.teplocentral.local/api/v1/zup/sync/all -H "Authorization: Bearer YOUR_TOKEN" >> /var/log/hrdesk-zup-sync.log 2>&1
```

### Systemd timer

Создайте `/etc/systemd/system/hrdesk-zup-sync.timer`:

```ini
[Unit]
Description=HR Desk ZUP Sync Timer

[Timer]
OnCalendar=hourly
Persistent=true

[Install]
WantedBy=timers.target
```
