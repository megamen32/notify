# Notificly

[English](../README.md) · **Русский** · [中文](README.zh-CN.md)

Notificly — маленький CLI-наблюдатель за локальным процессом. Он ждёт
завершения команды, не требует держать агента в polling-цикле и отправляет
итоговое уведомление через Notify Center.

## Установка

```bash
sudo install -m 0755 bin/notify bin/notify-producer /usr/local/bin/
```

Создайте `~/.config/secrets/notifier.env` с URL Center и project-scoped token.

Подробности: [CLI guide](cli.ru.md).
