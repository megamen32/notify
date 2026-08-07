# Notify CLI

The small process watcher extracted from Notify Center. It waits for a local
process to finish (or reaches a bounded timeout), optionally includes a safe
log tail/live stream, and sends a durable completion notification through
`notify-producer`.

This repository intentionally contains only the CLI watcher and its shell
producer. The full notification center, operator dashboard, adapters, topics,
and escalation policy live in [megamen32/notify](https://github.com/megamen32/notify).

## Install

```bash
sudo install -m 0755 bin/notify /usr/local/bin/notify
sudo install -m 0755 bin/notify-producer /usr/local/bin/notify-producer
```

Configure the producer endpoint and project-scoped token in the secrets file
used by the watcher:

```bash
install -d -m 700 ~/.config/secrets
cat > ~/.config/secrets/notifier.env <<'ENV'
NOTIFY_CENTER_EVENT_URL=https://notify.bezrabotnyi.com/v1/events
NOTIFY_CENTER_TOKEN=project-scoped-token
ENV
chmod 600 ~/.config/secrets/notifier.env
```

Then watch a PID or command query:

```bash
notify --non-interactive --pid 12345 --no-log --replace
notify -n --query 'my-command' --first --log-tail /tmp/job.log --hard-timeout 30m
```

See [`docs/cli.md`](docs/cli.md) for the complete option reference.

## License

[MIT](LICENSE)
