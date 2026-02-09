# whitelist_blacklist.py
import os
import json
import ipaddress
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, Request, HTTPException, Header, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, constr

CLIENTS_FILE = os.environ.get("CLIENTS_FILE", "clients.json")
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "changeme")  # change this in prod!

app = FastAPI(title="Dots + Client ACL")

# -------------------------
# Models
# -------------------------
class ClientsPayload(BaseModel):
    entries: List[constr(strip_whitespace=True, min_length=1)]

# -------------------------
# Persistence helpers
# -------------------------
def load_clients() -> Dict[str, List[str]]:
    if os.path.exists(CLIENTS_FILE):
        try:
            with open(CLIENTS_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
                # ensure keys exist
                return {
                    "whitelist": raw.get("whitelist", []),
                    "blacklist": raw.get("blacklist", []),
                }
        except Exception:
            # if file corrupted, return empty structure
            return {"whitelist": [], "blacklist": []}
    return {"whitelist": [], "blacklist": []}


def save_clients(data: Dict[str, List[str]]) -> None:
    # atomic-ish write
    tmp = CLIENTS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
    os.replace(tmp, CLIENTS_FILE)


# -------------------------
# Validation / matching helpers
# -------------------------
def parse_network(entry: str) -> ipaddress._BaseNetwork:
    """
    Parse an entry that may be a single IP or a CIDR.
    Raise ValueError for invalid input.
    """
    entry = entry.strip()
    # try ip_network first (this accepts both '1.2.3.4' and '1.2.3.0/24')
    # ip_network("1.2.3.4") creates a /32 for IPv4
    return ipaddress.ip_network(entry, strict=False)


def client_matches_list(client_ip: str, entries: List[str]) -> bool:
    """
    Return True if client_ip matches any entry in entries.
    Entries can be single IPs or CIDR networks.
    """
    try:
        addr = ipaddress.ip_address(client_ip)
    except ValueError:
        # invalid client IP
        return False

    for e in entries:
        try:
            net = parse_network(e)
        except ValueError:
            # skip invalid entry
            continue
        if addr in net:
            return True
    return False


# -------------------------
# Utility: determine client IP (respects X-Forwarded-For)
# -------------------------
def get_client_ip(request: Request) -> Optional[str]:
    # If there is an X-Forwarded-For header (commonly set by proxies), take first IP.
    xff = request.headers.get("x-forwarded-for")
    if xff:
        # could be "client, proxy1, proxy2"
        first = xff.split(",")[0].strip()
        # sanity-check
        try:
            ipaddress.ip_address(first)
            return first
        except ValueError:
            pass

    # fallback to request.client
    if request.client:
        return request.client.host
    return None


# -------------------------
# Middleware enforcing ACL
# -------------------------
@app.middleware("http")
async def acl_middleware(request: Request, call_next):
    # Allow internal admin actions if the correct token is present
    admin_token = request.headers.get("x-admin-token")
    is_admin = admin_token is not None and admin_token == ADMIN_TOKEN

    # Let admin calls through (so admin can manage the lists remotely).
    # If you want admin to also be subject to ACL, remove this bypass.
    if is_admin:
        return await call_next(request)

    client_ip = get_client_ip(request)
    if client_ip is None:
        # if we cannot determine the client IP, be conservative and deny
        return JSONResponse({"detail": "Unable to determine client IP"}, status_code=403)

    clients = load_clients()
    whitelist = clients.get("whitelist", []) or []
    blacklist = clients.get("blacklist", []) or []

    # If whitelist is present, only allow IPs in whitelist
    if whitelist:
        if client_matches_list(client_ip, whitelist):
            return await call_next(request)
        else:
            return JSONResponse(
                {"detail": "IP not in whitelist", "client_ip": client_ip},
                status_code=status.HTTP_403_FORBIDDEN,
            )

    # If no whitelist, check blacklist (deny if matched)
    if blacklist and client_matches_list(client_ip, blacklist):
        return JSONResponse(
            {"detail": "IP blacklisted", "client_ip": client_ip},
            status_code=status.HTTP_403_FORBIDDEN,
        )

    # default: allow
    return await call_next(request)


# -------------------------
# Admin endpoints to manage lists (protected by X-Admin-Token)
# -------------------------
def require_admin(token: Optional[str]):
    if token is None or token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Missing or invalid admin token")


@app.get("/clients", response_model=Dict[str, List[str]])
def list_clients(x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    return load_clients()


@app.post("/clients/whitelist", status_code=201)
def replace_whitelist(payload: ClientsPayload, x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    clients = load_clients()
    # validate entries parseable as networks
    valid = []
    for e in payload.entries:
        try:
            parse_network(e)
            valid.append(e)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid network or IP: {e}")
    clients["whitelist"] = valid
    save_clients(clients)
    return {"whitelist": valid}


@app.post("/clients/blacklist", status_code=201)
def replace_blacklist(payload: ClientsPayload, x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    clients = load_clients()
    valid = []
    for e in payload.entries:
        try:
            parse_network(e)
            valid.append(e)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid network or IP: {e}")
    clients["blacklist"] = valid
    save_clients(clients)
    return {"blacklist": valid}


@app.delete("/clients/whitelist", status_code=204)
def clear_whitelist(x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    clients = load_clients()
    clients["whitelist"] = []
    save_clients(clients)
    return JSONResponse(status_code=204, content=None)


@app.delete("/clients/blacklist", status_code=204)
def clear_blacklist(x_admin_token: Optional[str] = Header(None)):
    require_admin(x_admin_token)
    clients = load_clients()
    clients["blacklist"] = []
    save_clients(clients)
    return JSONResponse(status_code=204, content=None)
