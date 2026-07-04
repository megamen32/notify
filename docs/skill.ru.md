# Статус AI skill

[English](skill.md) | **Русский** | [中文](skill.zh.md)

Skill теперь optional.

Notify MCP встраивает важное поведение прямо в MCP metadata:

- tool descriptions
- JSON schema property descriptions
- return message guidance

Это значит, что MCP-aware clients вроде Codex, OpenCode, VS Code, Claude и похожих agents могут понять long-wait behavior из `tools/list` без отдельного skill file.

## Оставьте skill, если

- ваш runtime плохо показывает MCP tool descriptions модели;
- вам нужен human-readable policy file в shared AI environment;
- вы используете raw CLI fallback без MCP.

## Не используйте skill, если

- client корректно загружает MCP tools;
- вы видите `run_and_notify` и descriptions его параметров в client;
- модель следует встроенному правилу: коротко подождать, затем вернуть `job_id`, `pid` и `log_file` вместо polling.

Текущий skill file остаётся в [`../skill/SKILL.md`](../skill/SKILL.md) как secondary reminder и compatibility fallback.
