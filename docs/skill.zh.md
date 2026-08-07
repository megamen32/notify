# AI skill 状态

[English](skill.md) | [Русский](skill.ru.md) | **中文**

skill 现在是 optional。

Notify MCP 会把重要行为直接嵌入 MCP metadata：

- tool descriptions
- JSON schema property descriptions
- return message guidance

这意味着 Codex、OpenCode、VS Code、Claude 以及类似的 MCP-aware clients 可以直接从 `tools/list` 学习 long-wait behavior，不需要单独的 skill file。

## 什么时候保留 skill

- 你的 runtime 不能清楚地把 MCP tool descriptions 展示给模型；
- 你希望在 shared AI environment 中保留 human-readable policy file；
- 你使用 raw CLI fallback，而不是 MCP。

## 什么时候跳过 skill

- client 能正确加载 MCP tools；
- 你能在 client 中看到 `run_and_notify` 以及它的参数 descriptions；
- 模型遵循内置规则：短暂等待，然后返回 `job_id`、`pid` 和 `log_file`，而不是继续 polling。

当前 skill file 仍保留在 [`../skill/SKILL.md`](../skill/SKILL.md)，作为 secondary reminder 和 compatibility fallback。
