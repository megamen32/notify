# Process completion notification with notify

Use this skill when you start, supervise, or wait for a long-running Linux command and the user may want a Telegram notification when it finishes.

## Tool

`/usr/local/bin/notify` watches an existing process and sends Telegram messages through the user's configured bot.

## Required non-interactive pattern for AI agents

Never call plain `notify` from an AI agent. Always use the non-interactive flags so the command cannot open `fzf` or block on stdin:

```bash
/usr/local/bin/notify --non-interactive --pid "$PID" --no-log --replace
```

Equivalent short form:

```bash
/usr/local/bin/notify -n --pid "$PID" --no-log --replace
```

## Typical workflow

Start a long command in background, capture its PID, then attach notify:

```bash
long_running_command > /tmp/job.log 2>&1 &
PID=$!
/usr/local/bin/notify -n --pid "$PID" --log-tail /tmp/job.log --replace
```

Use `--log-live /path/to/log` only when the user explicitly wants Telegram messages for new log lines. Prefer `--log-tail` for lower noise.

## Process selection rules

Prefer `--pid` over `--query` because it is deterministic.

If PID is not available, use:

```bash
/usr/local/bin/notify -n --query "unique command substring" --no-log --replace
```

If the query can match more than one process, do not use `--first` unless the user explicitly accepts "first matching process" behavior. Without `--first`, non-interactive mode fails and prints the matching process list.

## Flags

- `-n`, `--non-interactive`: disable prompts, `fzf`, and stdin reads.
- `--pid PID`: watch an exact PID.
- `--query TEXT`: find a process by command substring.
- `--first`: with `--query`, take the first match instead of failing on multiple matches.
- `--no-log`: do not attach log handling.
- `--log-tail FILE`: send the final tail of a log after the process exits.
- `--log-live FILE`: forward new log lines while the process runs.
- `--replace`: replace an existing watcher for the same PID.
- `--test`: send a Telegram test message.

## Safety notes

Do not expose `~/.config/secrets/notifier.env` in logs or repository files. It contains `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`.

When using this on shared servers, run `notify` as the same user that owns the Telegram secrets and has permission to inspect the target process.
