# Notificly

[English](../README.md) · [Русский](README.ru.md) · **中文**

Notificly 是一个轻量的本地进程 watcher。它等待命令结束，不需要 agent
持续轮询，并通过 Notify Center 发送最终通知。

## 安装

```bash
sudo install -m 0755 bin/notify bin/notify-producer /usr/local/bin/
```

在 `~/.config/secrets/notifier.env` 中配置 Center URL 和项目 token。

详细说明见 [CLI guide](cli.zh.md)。
