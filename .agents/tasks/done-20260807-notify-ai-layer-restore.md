# Restore Notify AI layer

Status: done

## Original request

Вернуть в маленький Notify полезный AI-facing слой: skill, MCP и всё, что
позволяет AI использовать process completion notifications.

## Objective

Make the separate Notify CLI repository self-contained for AI clients again,
without pulling NoticePlace Center implementation into it.

## Business canary

Notify repository contains the skill and stdio MCP launcher; an AI client can
install the package, list tools, and use process completion notification tools.

## Confirmed scope

- `skill/SKILL.md` and translated skill docs.
- `mcp/notify_mcp.py` and stdio npm launcher/install script.
- MCP and skill documentation plus package metadata.

## Explicit exclusions

- No Agent Resume implementation.
- No NoticePlace server, dashboard, or delivery worker code.

## Initial estimate (immutable)

- Optimistic: 20 active minutes
- Likely: 45 active minutes
- Pessimistic: 90 active minutes

## Completion evidence

- Notify is now the canonical local folder, package name, CLI product name, and public repository name: `megamen32/notify`.
- `python -m py_compile mcp/notify_mcp.py`, `node --check` for both launchers, and `./bin/notify --help` passed.
- `npm pack --dry-run` contains the CLI, MCP, skill, multilingual docs, and no NoticePlace server files.
- Commits `df8cb9f` and `a211876` are pushed to `https://github.com/megamen32/notify`.
