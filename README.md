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

`--hard-timeout 30m` limits how long the background watcher follows a still-running process. It sends a timeout notification and stops watching; use `0` to disable the limit. Supported forms: seconds (`1800`), `30m`, `1h`, `500ms`.

## AI skill

The skill lives in [`skill/SKILL.md`](skill/SKILL.md). Copy it into the skill directory of the AI runtime you use, or keep the repo checked out and point the runtime to this folder.

## MCP server for AI agents

This repo also includes a small stdio MCP server: `mcp/notify_mcp.py`.

The most useful tool is `run_and_notify`: it starts a shell command detached in the background, stores logs under `~/.local/state/notify-mcp/jobs/<job_id>/`, attaches `/usr/local/bin/notify`, and returns immediately.

Example MCP tool arguments:

```json
{
  "command": "python3 long_job.py",
  "cwd": "/home/roomhacker/project",
  "log_mode": "tail",
  "replace": true,
  "wait_seconds": 180,
  "hard_timeout": "30m"
}
```

For AI agents, the rule is: if a command is expected to take more than 3 minutes, call `run_and_notify`, wait at most `wait_seconds` (normally <=180), and if the process is still alive return the `job_id`, `pid`, and `log_file` instead of polling. Telegram gets completion or hard-timeout notifications.

Returned fields include `job_id`, `pid`, `log_file`, `status_file`, `alive`, and `status`. Use `job_status` or `job_tail` only for small bounded checks. Telegram gets the completion message, so the AI does not need to keep polling or dump long logs into the chat.

Available MCP tools:

- `run_and_notify` — start a new detached command and notify on completion.
- `attach_pid` — attach notification to an existing PID.
- `attach_query` — attach by process substring, non-interactive and deterministic.
- `job_status` — small metadata/status check.
- `job_tail` — bounded log tail.
- `list_jobs` — recent jobs without log dumps.
- `kill_job` — signal a job process group.

Local GPTAdmin install example:

```bash
sudo gptadmin mcp add notify --install --status \
  --cwd /home/roomhacker/notify \
  -- /usr/bin/python3 /home/roomhacker/notify/mcp/notify_mcp.py
```
