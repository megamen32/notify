# Notify MCP

[English](README.md) | [Русский](README.ru.md) | **中文**

<p align="center">
  <img src="assets/hero.svg" alt="Notify MCP 在长时间等待期间节省智能体 token" width="100%">
</p>

**不要再让 AI 智能体花钱盯着终端发呆。**

Notify MCP 让 Codex 和其他代码智能体启动长时间、非交互式任务，只等待一个很短的受限窗口，然后带着 `job_id`、`pid` 和 `log_file` 返回控制权。进程继续在后台运行，`/usr/local/bin/notify` 负责监控，Telegram 会在任务完成或达到 hard timeout 时通知你。

对于持续一小时的构建、迁移、测试套件、备份和部署，相比让智能体一直轮询日志直到命令结束，这可以减少 **90%+** 的等待/轮询 token 消耗。

## 为什么智能体需要它

- **Codex long-wait mode：** 启动任务，最多等待 180 秒，然后停止消耗 token。
- **没有 polling loop：** MCP 工具 schema 会告诉模型在 `alive=true` 时返回。
- **Telegram completion：** 成功、失败、日志和 hard-timeout 都在聊天之外通知。
- **Self-describing MCP：** 使用规则内置在 `tools/list` 里；支持 MCP 的客户端不需要 skill。
- **PTY-safe 分工：** Notify MCP 用于非交互任务；`pty-mcp` 用于 prompts、TUI、编辑器或 keystrokes。

## 30 秒 MCP 安装

对 MCP 客户端来说，最简单的方式是 `npx`：

```bash
npx -y github:megamen32/notify
```

这个命令会启动 stdio MCP server。包里已经包含 Bash watcher，并且 launcher 会自动设置 `NOTIFY_BIN`，所以 MCP server 不需要手动 clone 也能运行。

如果要使用 Telegram 通知，请为运行 MCP 客户端的用户创建 secrets：

```bash
mkdir -p ~/.config/secrets
cat > ~/.config/secrets/notifier.env <<'ENV'
TELEGRAM_BOT_TOKEN=123456:telegram-bot-token
TELEGRAM_CHAT_ID=123456789
ENV
chmod 600 ~/.config/secrets/notifier.env
```

还想安装 raw CLI？

```bash
npm exec -y --package github:megamen32/notify -- notify-install
# 或者从 Releases 下载 notify-mcp-v*.tar.gz
```

## 添加到 Codex

```bash
codex mcp add notify -- npx -y github:megamen32/notify
codex mcp list
```

或者编辑 `~/.codex/config.toml` / `.codex/config.toml`：

```toml
[mcp_servers.notify]
command = "npx"
args = ["-y", "github:megamen32/notify"]
```

## 添加到 OpenCode

把下面内容加入 `~/.config/opencode/opencode.jsonc` 或项目的 `opencode.jsonc`：

```jsonc
{
  "mcp": {
    "notify": {
      "type": "local",
      "command": ["npx", "-y", "github:megamen32/notify"],
      "enabled": true
    }
  }
}
```

## 添加到 VS Code

在 workspace 中创建 `.vscode/mcp.json`，或者使用 **MCP: Open User Configuration**：

```json
{
  "servers": {
    "notify": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "github:megamen32/notify"]
    }
  }
}
```

然后运行 **MCP: List Servers** 并启动 `notify`。

## 智能体会看到什么

MCP server 会自己把规则告诉模型：

```text
对于预计超过 3 分钟的非交互任务，
使用 run_and_notify，并设置 log_mode="tail"、wait_seconds <= 180、
hard_timeout="30m"、replace=true。

如果 alive=true/state="running"，停止等待并报告 job_id、
pid 和 log_file。除非用户明确要求，不要继续 polling。
交互式/TUI/prompt 命令请使用 pty-mcp。
```

## 可下载的 release assets

每个 GitHub release 都包含：

- `notify-mcp-vX.Y.Z.tar.gz` — 带 `install.sh` 的 portable bundle
- `notify-mcp-vX.Y.Z.zip` — zip 格式的同一 bundle
- `notify-mcp-X.Y.Z.tgz` — npm package tarball
- `SHA256SUMS` — 校验和

## 文档

- [MCP server](docs/mcp.zh.md) — tools、schemas、智能体行为、client configs。
- [CLI tool](docs/cli.zh.md) — `/usr/local/bin/notify` 用法、Telegram secrets、logs。
- [AI skill](docs/skill.zh.md) — 如果客户端不能很好显示 MCP tool descriptions，可作为 optional fallback。

## 还需要 skill 吗？

通常**不需要**。对于 Codex、OpenCode、VS Code、Claude 和其他 MCP-aware 客户端，重要说明已经直接内置在 MCP tool descriptions 里。只有当某个 runtime 不能可靠显示 MCP schema descriptions 时，才把 skill 作为 fallback 保留。

## License

MIT
