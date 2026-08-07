#!/usr/bin/env node
import { copyFileSync, chmodSync, existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const here = dirname(fileURLToPath(import.meta.url));
const root = resolve(here, "..");
const src = resolve(root, "bin", "notify");
const dst = process.argv[2] || "/usr/local/bin/notify";

if (!existsSync(src)) {
  console.error(`notify-install: source not found: ${src}`);
  process.exit(127);
}

function tryCopy() {
  copyFileSync(src, dst);
  chmodSync(dst, 0o755);
}

try {
  tryCopy();
  console.log(`Installed notify CLI to ${dst}`);
} catch (err) {
  if (dst === "/usr/local/bin/notify") {
    console.error(`Direct install failed: ${err.message}`);
    console.error("Retrying with sudo...");
    const sudo = spawnSync("sudo", ["install", "-m", "0755", src, dst], { stdio: "inherit" });
    process.exit(sudo.status ?? 1);
  }
  console.error(`notify-install failed: ${err.message}`);
  process.exit(1);
}
