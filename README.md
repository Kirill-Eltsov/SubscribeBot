# Telegram Subscription Bot

## Настройка
1. Создайте приватный канал в Telegram.
2. Создайте бота через @BotFather и получите токен.
3. Добавьте бота в канал как администратора.
4. Создайте файл bot_config.py на основе bot_config_example.py и укажите:
   - `BOT_TOKEN` — токен вашего бота
   - `CHANNEL_ID` — ID вашего канала
   - параметры подключения к PostgreSQL
5. Установите зависимости:
   ```
   pip install -r requirements.txt
   ```

6. Запустите бота:
   ```
   python bot.py
   ```

## Важно
- Для добавления в канал бот формирует invite ссылку и присылает ее.
- Для отмены подписки введите sql-команду:  UPDATE subscribers SET subscription = FALSE WHERE id = (айди пользователя).
