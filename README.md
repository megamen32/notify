# Notify

[Русский](docs/README.ru.md) · [中文](docs/README.zh-CN.md) · [Docs](docs/)

![Notify carries an AI completion signal to a human](assets/hero-notify.png)

> A tiny process watcher that waits for local commands and sends a durable completion notification.

Notify is for agents, CI jobs, migrations, and scripts that should finish in
the background without a polling loop. It watches a PID or command query,
optionally includes a bounded log tail, and reports completion, failure, or
timeout through Notify Center.

## Install

```bash
sudo install -m 0755 bin/notify bin/notify-producer /usr/local/bin/
```

## Start in minutes

1. Create `~/.config/secrets/notifier.env` with `NOTIFY_CENTER_EVENT_URL` and a project-scoped `NOTIFY_CENTER_TOKEN`.
2. Watch a process: `notify -n --pid 12345 --no-log --replace`.
3. For a command query: `notify -n --query 'my-command' --first --hard-timeout 30m`.

AI clients can also install the bundled stdio MCP server. It exposes safe
process completion tools and the human notification skill without bundling the
NoticePlace Center:

```bash
npx -y github:megamen32/notify
```

## Learn more

- [CLI reference](docs/cli.md)
- [MCP server](docs/mcp.md)
- [AI skill](skill/SKILL.md)
- [Русская документация](docs/cli.ru.md)
- [中文文档](docs/cli.zh.md)
- [NoticePlace — delivery center](https://github.com/megamen32/noticeplace)

## License

[MIT](LICENSE)
