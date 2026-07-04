#!/usr/bin/env python3
"""Minimal stdio MCP server for /usr/local/bin/notify.

Designed for AI agents: start long jobs, attach Telegram completion notification,
and return immediately instead of keeping the chat/tool call blocked.
"""
from __future__ import annotations

import json
import os
import shlex
import signal
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SERVER_NAME = "notify-mcp"
SERVER_VERSION = "1.0.0"
NOTIFY_BIN = Path(os.environ.get("NOTIFY_BIN", "/usr/local/bin/notify"))
STATE_DIR = Path(os.environ.get("NOTIFY_MCP_STATE_DIR", "~/.local/state/notify-mcp")).expanduser()
JOBS_DIR = STATE_DIR / "jobs"
MAX_TAIL_BYTES = int(os.environ.get("NOTIFY_MCP_MAX_TAIL_BYTES", "20000"))


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_duration_seconds(value: Any, default: int = 0) -> int:
    if value is None or value == "":
        return default
    if isinstance(value, (int, float)):
        return max(0, int(value))
    text = str(value).strip().lower()
    if not text:
        return default
    units = (("ms", 1 / 1000), ("s", 1), ("m", 60), ("h", 3600))
    for suffix, mult in units:
        if text.endswith(suffix):
            num = text[: -len(suffix)].strip()
            try:
                seconds = float(num) * mult
            except ValueError as e:
                raise ValueError(f"invalid duration: {value!r}") from e
            return max(0, int(seconds + 0.999))
    try:
        return max(0, int(float(text)))
    except ValueError as e:
        raise ValueError(f"invalid duration: {value!r}") from e


def ensure_dirs() -> None:
    JOBS_DIR.mkdir(parents=True, exist_ok=True)


def json_write(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))
    os.replace(tmp, path)


def json_read(path: Path, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text())
    except Exception:
        return dict(default or {})


def is_pid_alive(pid: int) -> bool:
    proc_stat = Path(f"/proc/{pid}/stat")
    try:
        if proc_stat.exists():
            parts = proc_stat.read_text(errors="replace").split()
            if len(parts) >= 3 and parts[2] == "Z":
                return False
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except Exception:
        return False


def tail_file(path: Path, max_bytes: int = MAX_TAIL_BYTES) -> str:
    if not path.exists() or not path.is_file():
        return ""
    size = path.stat().st_size
    with path.open("rb") as f:
        if size > max_bytes:
            f.seek(-max_bytes, os.SEEK_END)
        data = f.read(max_bytes)
    return data.decode("utf-8", errors="replace")


def run_quick(args: List[str], cwd: Optional[str] = None, timeout: int = 15) -> Dict[str, Any]:
    p = subprocess.run(args, cwd=cwd, text=True, capture_output=True, timeout=timeout)
    return {
        "returncode": p.returncode,
        "stdout": p.stdout[-12000:],
        "stderr": p.stderr[-12000:],
        "argv": args,
    }


def notify_args_for(pid: Optional[int] = None, query: Optional[str] = None, log_mode: str = "none", log_file: Optional[str] = None, replace: bool = True, first: bool = False, hard_timeout: Any = None) -> List[str]:
    if not NOTIFY_BIN.exists():
        raise FileNotFoundError(f"notify binary not found: {NOTIFY_BIN}")
    args = [str(NOTIFY_BIN), "--non-interactive"]
    if pid is not None:
        args += ["--pid", str(pid)]
    elif query:
        args += ["--query", query]
        if first:
            args.append("--first")
    else:
        raise ValueError("pid or query is required")

    if log_mode == "none":
        args.append("--no-log")
    elif log_mode in ("tail", "live"):
        if not log_file:
            raise ValueError(f"log_file is required for log_mode={log_mode}")
        args += [f"--log-{log_mode}", log_file]
    else:
        raise ValueError("log_mode must be one of: none, tail, live")

    if hard_timeout not in (None, "", 0, "0"):
        args += ["--hard-timeout", str(hard_timeout)]

    if replace:
        args.append("--replace")
    return args


def tool_attach_pid(args: Dict[str, Any]) -> Dict[str, Any]:
    pid = int(args.get("pid") or 0)
    if pid <= 0:
        raise ValueError("pid must be a positive integer")
    log_mode = str(args.get("log_mode") or "none")
    log_file = args.get("log_file")
    replace = bool(args.get("replace", True))
    hard_timeout = args.get("hard_timeout", "30m")
    result = run_quick(notify_args_for(pid=pid, log_mode=log_mode, log_file=log_file, replace=replace, hard_timeout=hard_timeout))
    return {"ok": result["returncode"] == 0, "pid": pid, "notify": result}


def tool_attach_query(args: Dict[str, Any]) -> Dict[str, Any]:
    query = str(args.get("query") or "").strip()
    if not query:
        raise ValueError("query is required")
    log_mode = str(args.get("log_mode") or "none")
    log_file = args.get("log_file")
    replace = bool(args.get("replace", True))
    first = bool(args.get("first", False))
    hard_timeout = args.get("hard_timeout", "30m")
    result = run_quick(notify_args_for(query=query, log_mode=log_mode, log_file=log_file, replace=replace, first=first, hard_timeout=hard_timeout))
    return {"ok": result["returncode"] == 0, "query": query, "notify": result}


def shell_quote_env(value: str) -> str:
    return shlex.quote(value)


def tool_run_and_notify(args: Dict[str, Any]) -> Dict[str, Any]:
    command = str(args.get("command") or "").strip()
    if not command:
        raise ValueError("command is required")
    cwd = str(args.get("cwd") or os.getcwd())
    cwd_path = Path(cwd).expanduser().resolve()
    if not cwd_path.exists() or not cwd_path.is_dir():
        raise FileNotFoundError(f"cwd not found or not a directory: {cwd_path}")

    log_mode = str(args.get("log_mode") or "tail")
    if log_mode not in ("none", "tail", "live"):
        raise ValueError("log_mode must be one of: none, tail, live")
    replace = bool(args.get("replace", True))
    hard_timeout = args.get("hard_timeout", "30m")
    hard_timeout_seconds = parse_duration_seconds(hard_timeout, default=1800)
    wait_seconds = min(parse_duration_seconds(args.get("wait_seconds", 0), default=0), hard_timeout_seconds or 10**9)
    note = str(args.get("note") or "")

    job_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    job_dir = JOBS_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=False)
    log_file = job_dir / "job.log"
    status_file = job_dir / "status.json"
    runner = job_dir / "runner.sh"

    meta: Dict[str, Any] = {
        "job_id": job_id,
        "command": command,
        "cwd": str(cwd_path),
        "log_file": str(log_file),
        "status_file": str(status_file),
        "created_at": now_iso(),
        "note": note,
        "hard_timeout": hard_timeout,
        "hard_timeout_seconds": hard_timeout_seconds,
        "wait_seconds": wait_seconds,
        "state": "starting",
    }
    json_write(job_dir / "meta.json", meta)

    runner.write_text(f"""#!/usr/bin/env bash
set +e
cd {shell_quote_env(str(cwd_path))}
cat > {shell_quote_env(str(status_file))} <<'STATUS_JSON_EOF'
{{"job_id": {json.dumps(job_id)}, "state": "running", "started_at": {json.dumps(now_iso())}}}
STATUS_JSON_EOF
(
  echo "== notify-mcp job {job_id} =="
  echo "started_at: $(date -Is)"
  echo "cwd: {str(cwd_path)}"
  echo "command: {command}"
  echo
  bash -lc {shell_quote_env(command)}
)
rc=$?
python3 -c 'import json,sys,time; from datetime import datetime,timezone; p=sys.argv[1]; rc=int(sys.argv[2]); data={{"job_id": {json.dumps(job_id)}, "state":"finished", "returncode":rc, "finished_at":datetime.now(timezone.utc).isoformat(), "finished_epoch":time.time()}}; open(p,"w").write(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))' {shell_quote_env(str(status_file))} "$rc"
exit "$rc"
""")
    runner.chmod(0o755)

    launch = subprocess.run(
        ["/bin/bash", "-lc", f"setsid /usr/bin/env bash {shlex.quote(str(runner))} > {shlex.quote(str(log_file))} 2>&1 < /dev/null & echo $!"],
        cwd=str(cwd_path),
        text=True,
        capture_output=True,
        timeout=10,
    )
    if launch.returncode != 0:
        raise RuntimeError(f"failed to launch detached job: {launch.stderr or launch.stdout}")
    try:
        pid = int(launch.stdout.strip().splitlines()[-1])
    except Exception as e:
        raise RuntimeError(f"failed to parse launched PID from: {launch.stdout!r}") from e

    meta.update({"pid": pid, "state": "running", "started_at": now_iso(), "runner": str(runner), "launch_stdout": launch.stdout[-2000:], "launch_stderr": launch.stderr[-2000:]})
    json_write(job_dir / "meta.json", meta)

    notify_log_file = str(log_file) if log_mode in ("tail", "live") else None
    notify_result = run_quick(notify_args_for(pid=pid, log_mode=log_mode, log_file=notify_log_file, replace=replace, hard_timeout=hard_timeout))
    meta["notify"] = notify_result
    meta["notify_attached"] = notify_result["returncode"] == 0
    json_write(job_dir / "meta.json", meta)

    waited_seconds = 0.0
    if wait_seconds > 0:
        deadline = time.time() + wait_seconds
        while time.time() < deadline and is_pid_alive(pid):
            sleep_for = min(2.0, max(0.1, deadline - time.time()))
            time.sleep(sleep_for)
        waited_seconds = max(0.0, wait_seconds - max(0.0, deadline - time.time()))

    status_snapshot = json_read(status_file, {"state": "running"})
    alive_snapshot = is_pid_alive(pid)

    return {
        "ok": notify_result["returncode"] == 0,
        "job_id": job_id,
        "pid": pid,
        "cwd": str(cwd_path),
        "log_file": str(log_file),
        "status_file": str(status_file),
        "runner": str(runner),
        "notify_attached": notify_result["returncode"] == 0,
        "hard_timeout": hard_timeout,
        "hard_timeout_seconds": hard_timeout_seconds,
        "wait_seconds": wait_seconds,
        "waited_seconds": round(waited_seconds, 3),
        "alive": alive_snapshot,
        "status": status_snapshot,
        "notify_stdout": notify_result["stdout"][-3000:],
        "notify_stderr": notify_result["stderr"][-3000:],
        "message": "Started in background with Telegram notification. If still alive after wait_seconds, stop waiting and return this job_id instead of polling and burning tokens.",
    }


def job_paths(job_id: str) -> Dict[str, Path]:
    if not job_id or "/" in job_id or ".." in job_id:
        raise ValueError("invalid job_id")
    job_dir = JOBS_DIR / job_id
    return {"dir": job_dir, "meta": job_dir / "meta.json", "status": job_dir / "status.json", "log": job_dir / "job.log"}


def tool_job_status(args: Dict[str, Any]) -> Dict[str, Any]:
    job_id = str(args.get("job_id") or "")
    paths = job_paths(job_id)
    if not paths["meta"].exists():
        raise FileNotFoundError(f"job not found: {job_id}")
    meta = json_read(paths["meta"])
    status = json_read(paths["status"], {"state": "unknown"})
    pid = int(meta.get("pid") or 0)
    alive = is_pid_alive(pid) if pid else False
    return {"job_id": job_id, "alive": alive, "pid": pid, "meta": meta, "status": status, "log_file": str(paths["log"]), "log_size": paths["log"].stat().st_size if paths["log"].exists() else 0}


def tool_job_tail(args: Dict[str, Any]) -> Dict[str, Any]:
    job_id = str(args.get("job_id") or "")
    max_bytes = int(args.get("max_bytes") or 6000)
    max_bytes = max(1, min(max_bytes, MAX_TAIL_BYTES))
    paths = job_paths(job_id)
    if not paths["dir"].exists():
        raise FileNotFoundError(f"job not found: {job_id}")
    return {"job_id": job_id, "log_file": str(paths["log"]), "tail": tail_file(paths["log"], max_bytes=max_bytes)}


def tool_list_jobs(args: Dict[str, Any]) -> Dict[str, Any]:
    limit = int(args.get("limit") or 20)
    rows = []
    for d in sorted(JOBS_DIR.glob("*"), key=lambda p: p.name, reverse=True):
        if not d.is_dir():
            continue
        meta = json_read(d / "meta.json")
        status = json_read(d / "status.json", {"state": meta.get("state", "unknown")})
        pid = int(meta.get("pid") or 0)
        rows.append({"job_id": d.name, "pid": pid, "alive": is_pid_alive(pid) if pid else False, "state": status.get("state"), "returncode": status.get("returncode"), "created_at": meta.get("created_at"), "command": meta.get("command"), "log_file": meta.get("log_file")})
        if len(rows) >= limit:
            break
    return {"count": len(rows), "jobs": rows}


def tool_kill_job(args: Dict[str, Any]) -> Dict[str, Any]:
    job_id = str(args.get("job_id") or "")
    sig_name = str(args.get("signal") or "TERM").upper().removeprefix("SIG")
    sig = getattr(signal, "SIG" + sig_name, None)
    if sig is None:
        raise ValueError("unknown signal; use TERM, INT, KILL")
    st = tool_job_status({"job_id": job_id})
    pid = int(st["pid"])
    if not pid:
        raise ValueError("job has no pid")
    try:
        os.killpg(pid, sig)
        sent = True
    except ProcessLookupError:
        sent = False
    return {"job_id": job_id, "pid": pid, "signal": "SIG" + sig_name, "sent": sent}


TOOLS = {
    "run_and_notify": {
        "description": "For commands likely to exceed 3 minutes: start detached in the background, attach /usr/local/bin/notify, optionally wait up to wait_seconds, then return job_id/pid/log_file instead of burning tokens. Default hard_timeout is 30m.",
        "inputSchema": {"type": "object", "properties": {"command": {"type": "string"}, "cwd": {"type": ["string", "null"], "default": "/home/roomhacker"}, "log_mode": {"type": "string", "enum": ["none", "tail", "live"], "default": "tail"}, "replace": {"type": "boolean", "default": True}, "note": {"type": ["string", "null"]}, "wait_seconds": {"type": ["integer", "null"], "default": 0, "description": "Optional small wait before returning. Use <=180 for tasks expected around 3 minutes; use 0 to return immediately."}, "hard_timeout": {"type": ["string", "integer", "null"], "default": "30m", "description": "Maximum notify watcher lifetime, e.g. 1800, 30m, 1h. Default 30m."}}, "required": ["command"], "additionalProperties": False},
        "handler": tool_run_and_notify,
    },
    "attach_pid": {
        "description": "Attach Telegram completion notification to an already running PID and return immediately.",
        "inputSchema": {"type": "object", "properties": {"pid": {"type": "integer"}, "log_mode": {"type": "string", "enum": ["none", "tail", "live"], "default": "none"}, "log_file": {"type": ["string", "null"]}, "replace": {"type": "boolean", "default": True}, "hard_timeout": {"type": ["string", "integer", "null"], "default": "30m"}}, "required": ["pid"], "additionalProperties": False},
        "handler": tool_attach_pid,
    },
    "attach_query": {
        "description": "Attach notification to a process found by command substring. Non-interactive; fails on multiple matches unless first=true.",
        "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}, "first": {"type": "boolean", "default": False}, "log_mode": {"type": "string", "enum": ["none", "tail", "live"], "default": "none"}, "log_file": {"type": ["string", "null"]}, "replace": {"type": "boolean", "default": True}, "hard_timeout": {"type": ["string", "integer", "null"], "default": "30m"}}, "required": ["query"], "additionalProperties": False},
        "handler": tool_attach_query,
    },
    "job_status": {"description": "Small status check for a notify-mcp background job.", "inputSchema": {"type": "object", "properties": {"job_id": {"type": "string"}}, "required": ["job_id"], "additionalProperties": False}, "handler": tool_job_status},
    "job_tail": {"description": "Return a bounded tail of a notify-mcp job log. Default is small to save tokens.", "inputSchema": {"type": "object", "properties": {"job_id": {"type": "string"}, "max_bytes": {"type": ["integer", "null"], "default": 6000}}, "required": ["job_id"], "additionalProperties": False}, "handler": tool_job_tail},
    "list_jobs": {"description": "List recent notify-mcp jobs without dumping logs.", "inputSchema": {"type": "object", "properties": {"limit": {"type": ["integer", "null"], "default": 20}}, "additionalProperties": False}, "handler": tool_list_jobs},
    "kill_job": {"description": "Send a signal to a notify-mcp job process group.", "inputSchema": {"type": "object", "properties": {"job_id": {"type": "string"}, "signal": {"type": ["string", "null"], "default": "TERM"}}, "required": ["job_id"], "additionalProperties": False}, "handler": tool_kill_job},
}


def reply(req_id: Any, result: Any = None, error: Exception | None = None) -> None:
    if req_id is None:
        return
    if error is not None:
        payload = {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32000, "message": str(error), "data": error.__class__.__name__}}
    else:
        payload = {"jsonrpc": "2.0", "id": req_id, "result": result}
    print(json.dumps(payload, ensure_ascii=False), flush=True)


def handle(req: Dict[str, Any]) -> None:
    method = req.get("method")
    req_id = req.get("id")
    try:
        if method == "initialize":
            reply(req_id, {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION}})
        elif method == "tools/list":
            reply(req_id, {"tools": [{"name": n, "description": t["description"], "inputSchema": t["inputSchema"]} for n, t in TOOLS.items()]})
        elif method == "tools/call":
            params = req.get("params") or {}
            name = params.get("name")
            targs = params.get("arguments") or {}
            if name not in TOOLS:
                raise ValueError(f"unknown tool: {name}")
            result = TOOLS[name]["handler"](targs)
            reply(req_id, {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}], "structuredContent": result})
        elif method and method.startswith("notifications/"):
            return
        else:
            reply(req_id, {})
    except Exception as e:
        print(f"notify_mcp error: {e}", file=sys.stderr, flush=True)
        reply(req_id, error=e)


def main() -> None:
    ensure_dirs()
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            handle(json.loads(line))
        except Exception as e:
            print(f"bad request: {e}", file=sys.stderr, flush=True)


if __name__ == "__main__":
    main()
