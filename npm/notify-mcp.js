#!/usr/bin/env node
import { spawn } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { existsSync } from "node:fs";

const here = dirname(fileURLToPath(import.meta.url));
const root = resolve(here, "..");
const mcp = resolve(root, "mcp", "notify_mcp.py");
const bundledNotify = resolve(root, "bin", "notify");

if (!existsSync(mcp)) {
  console.error(`notify-mcp: MCP server not found: ${mcp}`);
  process.exit(127);
}

const python = process.env.PYTHON || process.env.PYTHON3 || "python3";
const env = { ...process.env };
if (!env.NOTIFY_BIN && existsSync(bundledNotify)) {
  env.NOTIFY_BIN = bundledNotify;
}

const child = spawn(python, [mcp, ...process.argv.slice(2)], {
  stdio: "inherit",
  env,
});

child.on("error", (err) => {
  console.error(`notify-mcp: failed to start ${python}: ${err.message}`);
  console.error("Install Python 3 or set PYTHON=/path/to/python3.");
  process.exit(127);
});

child.on("exit", (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
  } else {
    process.exit(code ?? 0);
  }
});
