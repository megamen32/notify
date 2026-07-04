# notify

`notify` is a small Bash utility for watching a Linux process and sending Telegram messages when it starts watching, streams optional log lines, and when the process exits.

It is useful for long-running scripts, AI agents, cron jobs, SSH sessions, and server maintenance tasks.

## Features

- Watch by PID or by command substring.
- Sends Telegram notifications through `sendMessage`.
- Optional live log forwarding or final log tail.
- Safe non-interactive mode for AI agents and automation.
- Per-PID watcher lock with `--replace` support.
- Process identity check through `/proc/<pid>/stat` start id to reduce PID reuse mistakes.

## Install

```bash
sudo install -m 0755 -o root -g root bin/notify /usr/local/bin/notify
```

Create secrets for the user that will run `notify`:

```bash
mkdir -p ~/.config/secrets
cat > ~/.config/secrets/notifier.env <<'ENV'
TELEGRAM_BOT_TOKEN=123456:telegram-bot-token
TELEGRAM_CHAT_ID=123456789
# optional:
# TELEGRAM_PROXY_URL=socks5h://127.0.0.1:1080
# TELEGRAM_TIMEOUT_MS=3500
ENV
chmod 600 ~/.config/secrets/notifier.env
```

## Usage

Interactive:

```bash
notify
notify sync_sessions
notify 12345
```

Automation / AI-safe:

```bash
notify --non-interactive --pid 12345 --no-log --replace
notify -n --query sync_sessions --first --no-log --replace
notify -n --pid 12345 --log-tail /tmp/job.log --replace
notify -n --pid 12345 --log-live /tmp/job.log --replace
```

`--non-interactive` / `-n` disables prompts, `fzf`, and `read`. If a query matches multiple processes, `notify` fails with a list unless `--first` is passed.

## AI skill

The skill lives in [`skill/SKILL.md`](skill/SKILL.md). Copy it into the skill directory of the AI runtime you use, or keep the repo checked out and point the runtime to this folder.
