# Notify MCP

<p align="center">
  <img src="assets/hero.svg" alt="Notify MCP saves agent tokens during long waits" width="100%">
</p>

**Stop paying your AI agent to stare at a terminal.**

Notify MCP lets Codex and other coding agents start long, non-interactive jobs, wait for a short bounded window, then return control with a `job_id`, `pid`, and `log_file`. The process keeps running in the background, `/usr/local/bin/notify` watches it, and Telegram tells you when it finishes or hits a hard timeout.

For hour-long builds, migrations, test suites, backups, and deployments, this can cut waiting/polling token usage by **90%+** compared with an agent that keeps checking logs until the command exits.

## Why agents use it

- **Codex long-wait mode:** launch the job, wait up to 180 seconds, then stop burning tokens.
- **No polling loop:** the MCP tool schema tells the model to return when `alive=true`.
- **Telegram completion:** success, failure, logs, and hard-timeout alerts arrive outside the chat.
- **Self-describing MCP:** usage rules are embedded in `tools/list`; no skill is required for MCP-aware clients.
- **PTY-safe split:** use Notify MCP for non-interactive jobs; use `pty-mcp` for prompts, TUIs, editors, or keystrokes.

## 60-second install

```bash
git clone https://github.com/megamen32/notify ~/.local/share/notify
sudo install -m 0755 ~/.local/share/notify/bin/notify /usr/local/bin/notify
mkdir -p ~/.config/secrets
cat > ~/.config/secrets/notifier.env <<'ENV'
TELEGRAM_BOT_TOKEN=123456:telegram-bot-token
TELEGRAM_CHAT_ID=123456789
ENV
chmod 600 ~/.config/secrets/notifier.env
```

Test the CLI:

```bash
sleep 10 & notify --non-interactive --pid $! --no-log --replace --hard-timeout 30m
```

## Add to Codex

```bash
codex mcp add notify -- /usr/bin/python3 ~/.local/share/notify/mcp/notify_mcp.py
codex mcp list
```

Or edit `~/.codex/config.toml` / `.codex/config.toml`:

```toml
[mcp_servers.notify]
command = "/usr/bin/python3"
args = ["/home/YOU/.local/share/notify/mcp/notify_mcp.py"]
```

## Add to OpenCode

Add this to `~/.config/opencode/opencode.jsonc` or your project `opencode.jsonc`:

```jsonc
{
  "mcp": {
    "notify": {
      "type": "local",
      "command": [
        "/usr/bin/python3",
        "/home/YOU/.local/share/notify/mcp/notify_mcp.py"
      ],
      "enabled": true
    }
  }
}
```

## Add to VS Code

Create `.vscode/mcp.json` in the workspace, or use **MCP: Open User Configuration**:

```json
{
  "servers": {
    "notify": {
      "type": "stdio",
      "command": "/usr/bin/python3",
      "args": ["/home/YOU/.local/share/notify/mcp/notify_mcp.py"]
    }
  }
}
```

Then run **MCP: List Servers** and start `notify`.

## What the agent sees

The MCP server itself teaches the model the rule:

```text
For non-interactive jobs expected to take more than 3 minutes,
use run_and_notify with log_mode="tail", wait_seconds <= 180,
hard_timeout="30m", replace=true.

If alive=true/state="running", stop waiting and report job_id,
pid, and log_file. Do not keep polling unless explicitly asked.
Use pty-mcp for interactive/TUI/prompt commands.
```

## Docs

- [MCP server](docs/mcp.md) — tools, schemas, agent behavior, client configs.
- [CLI tool](docs/cli.md) — `/usr/local/bin/notify` usage, Telegram secrets, logs.
- [AI skill](docs/skill.md) — optional fallback for clients that do not expose MCP tool descriptions well.

## Do I still need the skill?

Usually **no**. For Codex, OpenCode, VS Code, Claude, and other MCP-aware clients, the important instructions are now embedded directly in the MCP tool descriptions. Keep the skill only as a fallback for runtimes that do not surface MCP schema descriptions reliably.

## License

MIT
