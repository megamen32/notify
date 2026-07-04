# AI skill status

**Languages:** English | [Русский](skill.ru.md) | [中文](skill.zh.md)

The skill is now optional.

Notify MCP embeds the important behavior directly in MCP metadata:

- tool descriptions
- JSON schema property descriptions
- return message guidance

That means MCP-aware clients such as Codex, OpenCode, VS Code, Claude, and similar agents can learn the long-wait behavior from `tools/list` without a separate skill file.

## Keep the skill when

- your runtime does not expose MCP tool descriptions clearly to the model;
- you want a human-readable policy file in a shared AI environment;
- you use the raw CLI fallback without MCP.

## Skip the skill when

- the client loads MCP tools correctly;
- you can see `run_and_notify` and its parameter descriptions in the client;
- the model follows the embedded rule: wait briefly, then return `job_id`, `pid`, and `log_file` instead of polling.

The current skill file remains in [`../skill/SKILL.md`](../skill/SKILL.md) as a secondary reminder and compatibility fallback.
