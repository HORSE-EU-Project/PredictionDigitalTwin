# dots_app.py
import os
import asyncio
import datetime
import shutil
from typing import List, Dict, Any

from fastapi import FastAPI
from pydantic import BaseModel

from functools import partial

app = FastAPI(title="Dots status API")


async def to_thread(func, /, *args, **kwargs):
    """
    Backport of asyncio.to_thread for Python < 3.9
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None,
        partial(func, *args, **kwargs),
    )

# ------------------------
# Configure the services to check
# ------------------------
# Example entries:
#  - file check: check if 'filename' exists inside 'dir'
#  - docker check: check if a running container matches 'container' (name or partial)
SERVICES = [
    {"name": "pcapninja", "type": "file", "dir": "../PcapNinja", "filename": "pcapninja.py"},
    {"name": "grafana", "type": "docker", "container": "grafana"},
    {"name": "prometheus", "type": "docker", "container": "prometheus"},
    {"name": "Open5GS", "type": "docker", "container": "upf_cld"},
    {"name": "UERANSIM", "type": "docker", "container": "ue1"},
    {"name": "wireshark", "type": "command", "command": "tshark"},
    {"name": "tcpdump", "type": "command", "command": "tcpdump"},
]


# ------------------------
# Helpers
# ------------------------
def _now_iso() -> str:
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def check_file_exists(dirpath: str, filename: str) -> Dict[str, Any]:
    """Synchronous check whether a file exists at dirpath/filename."""
    path = os.path.join(dirpath, filename)
    exists = os.path.isfile(path)
    return {
        "type": "file",
        "path": path,
        "ok": exists,
        "status": "up" if exists else "down",
        "checked_at": _now_iso(),
    }

def check_command_available(command: str) -> dict:
    """
    Check if a system command is available in PATH.
    Does NOT execute the command.
    """
    path = shutil.which(command)
    available = path is not None
    return {
        "type": "command",
        "command": command,
        "path": path,
        "ok": available,
        "status": "up" if available else "down",
        "checked_at": _now_iso(),
    }

def check_docker_running_sync(container_name: str) -> Dict[str, Any]:
    """
    Synchronous docker check. Tries docker SDK, falls back to docker CLI.
    Returns dict with ok True if a running container matching container_name exists.
    """
    # Try docker SDK first
    try:
        import docker  # type: ignore
        try:
            client = docker.from_env()
            # list returns running containers by default; filters allow partial name matches
            containers = client.containers.list(filters={"name": container_name, "status": "running"})
            found = len(containers) > 0
            names = [c.name for c in containers]
            return {
                "type": "docker",
                "container_query": container_name,
                "ok": found,
                "status": "up" if found else "down",
                "matched": names,
                "checked_at": _now_iso(),
                "backend": "docker_sdk",
            }
        except Exception as e:
            # If SDK present but call fails, fall back to CLI
            _sdk_err = str(e)
    except Exception:
        _sdk_err = None

    # Fallback: use docker CLI to check running containers
    try:
        import subprocess

        # filter by name and status=running; format returns matching names (one per line)
        cmd = [
            "docker",
            "ps",
            "--filter",
            f"name={container_name}",
            "--filter",
            "status=running",
            "--format",
            "{{.Names}}",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        output = proc.stdout.strip()
        matched = [line for line in output.splitlines() if line.strip()]
        found = len(matched) > 0
        return {
            "type": "docker",
            "container_query": container_name,
            "ok": found,
            "status": "up" if found else "down",
            "matched": matched,
            "checked_at": _now_iso(),
            "backend": "docker_cli",
            "cli_returncode": proc.returncode,
            "cli_stderr": proc.stderr.strip() if proc.stderr else "",
            "sdk_error": _sdk_err,
        }
    except FileNotFoundError:
        # docker CLI not found
        return {
            "type": "docker",
            "container_query": container_name,
            "ok": False,
            "status": "down",
            "checked_at": _now_iso(),
            "backend": None,
            "error": "docker SDK and docker CLI not available",
            "sdk_error": _sdk_err,
        }
    except Exception as e:
        return {
            "type": "docker",
            "container_query": container_name,
            "ok": False,
            "status": "down",
            "checked_at": _now_iso(),
            "backend": "docker_cli",
            "error": str(e),
            "sdk_error": _sdk_err,
        }


async def check_service(item: Dict[str, Any]) -> Dict[str, Any]:
    """Async wrapper to run sync checks in a thread."""
    t = item.get("type")
    if t == "file":
        dirpath = item.get("dir", ".")
        filename = item.get("filename", "")
        return await to_thread(check_file_exists, dirpath, filename)
    elif t == "docker":
        container = item.get("container", "")
        return await to_thread(check_docker_running_sync, container)
    elif t == "command":
        return await to_thread(
            check_command_available,
            item.get("command", ""),
        )
    else:
        return {
            "type": t,
            "ok": False,
            "status": "unknown",
            "checked_at": _now_iso(),
            "error": "unsupported service type",
        }


# ------------------------
# Response model (optional)
# ------------------------
class DotsResponse(BaseModel):
    summary: Dict[str, Any]
    services: Dict[str, Any]


# ------------------------
# Endpoint
# ------------------------
@app.get("/dots", response_model=DotsResponse)
async def dots():
    """
    Return JSON with service status dots.

    Example output:
    {
      "summary": {"total": 3, "up": 1, "down": 2},
      "services": {
        "app_ready_file": { "type": "file", "path": "/tmp/app_ready", "ok": true, ... },
        "redis": { "type": "docker", "ok": false, ... }
      }
    }
    """
    checks = await asyncio.gather(*(check_service(s) for s in SERVICES))
    services_out: Dict[str, Any] = {}
    up = down = 0
    for svc_def, result in zip(SERVICES, checks):
        name = svc_def.get("name") or svc_def.get("container") or svc_def.get("filename") or "unknown"
        services_out[name] = result
        if result.get("ok"):
            up += 1
        else:
            down += 1

    summary = {"total": len(SERVICES), "up": up, "down": down, "checked_at": _now_iso()}
    return {"summary": summary, "services": services_out}
