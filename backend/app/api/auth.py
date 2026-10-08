import os
import uuid
import secrets
import hashlib
import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Header, Depends, status
from pydantic import BaseModel, Field

from app.database.mongodb import get_database

router = APIRouter()

# ─── Dual Persistence: MongoDB or In-Memory ───────────────────────────────────

_mem_users: Dict[str, Dict[str, Any]] = {}       # user_id -> user dict
_mem_sessions: Dict[str, str] = {}               # token -> user_id


def _now() -> str:
    return datetime.datetime.utcnow().isoformat() + "Z"


def _hash_password(password: str, salt: Optional[bytes] = None) -> tuple[str, str]:
    """Hashes password with PBKDF2-HMAC-SHA256."""
    salt_bytes = salt or secrets.token_bytes(16)
    pw_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt_bytes, 100000)
    return pw_hash.hex(), salt_bytes.hex()


def _verify_password(password: str, pw_hash: str, salt_hex: str) -> bool:
    salt_bytes = bytes.fromhex(salt_hex)
    check_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt_bytes, 100000)
    return secrets.compare_digest(check_hash.hex(), pw_hash)


# ─── Seed Initial Admin Demo & User Demo Accounts ─────────────────────────────

def _seed_initial_users():
    defaults = [
        {
            "username": "admin",
            "email": "admin@agent101.ai",
            "full_name": "System Administrator (Demo)",
            "role": "admin",
            "password": "admin123"
        },
        {
            "username": "demo_user",
            "email": "user@agent101.ai",
            "full_name": "Studio Creator (Demo)",
            "role": "user",
            "password": "user123"
        }
    ]
    for d in defaults:
        h, s = _hash_password(d["password"])
        uid = f"user-{d['username']}"
        user_record = {
            "_id": uid,
            "id": uid,
            "username": d["username"],
            "email": d["email"],
            "full_name": d["full_name"],
            "role": d["role"],
            "password_hash": h,
            "salt": s,
            "created_at": _now()
        }
        _mem_users[uid] = user_record

_seed_initial_users()


async def _find_user_by_email_or_username(identifier: str) -> Optional[Dict[str, Any]]:
    identifier_clean = identifier.strip().lower()
    db = get_database()
    if db is not None:
        user = await db.users.find_one({
            "$or": [
                {"email": identifier_clean},
                {"username": identifier_clean}
            ]
        })
        if user:
            user["id"] = str(user.get("_id", user.get("id")))
            return user
    for u in _mem_users.values():
        if u["email"].lower() == identifier_clean or u["username"].lower() == identifier_clean:
            return u
    return None


async def _find_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    db = get_database()
    if db is not None:
        user = await db.users.find_one({"$or": [{"_id": user_id}, {"id": user_id}]})
        if user:
            user["id"] = str(user.get("_id", user.get("id")))
            return user
    return _mem_users.get(user_id)


async def _save_user(user_doc: Dict[str, Any]) -> None:
    db = get_database()
    if db is not None:
        await db.users.insert_one(user_doc)
    _mem_users[user_doc["id"]] = user_doc


async def _update_user_fields(user_id: str, fields: Dict[str, Any]) -> None:
    db = get_database()
    if db is not None:
        await db.users.update_one({"$or": [{"_id": user_id}, {"id": user_id}]}, {"$set": fields})
    if user_id in _mem_users:
        _mem_users[user_id].update(fields)


async def _delete_user(user_id: str) -> None:
    db = get_database()
    if db is not None:
        await db.users.delete_one({"$or": [{"_id": user_id}, {"id": user_id}]})
    _mem_users.pop(user_id, None)
    # Clear associated sessions
    tokens_to_remove = [t for t, uid in _mem_sessions.items() if uid == user_id]
    for t in tokens_to_remove:
        _mem_sessions.pop(t, None)


async def _save_session(token: str, user_id: str) -> None:
    db = get_database()
    if db is not None:
        await db.sessions.insert_one({
            "token": token,
            "user_id": user_id,
            "created_at": _now()
        })
    _mem_sessions[token] = user_id


async def _find_user_by_token(token: str) -> Optional[Dict[str, Any]]:
    if not token:
        return None
    db = get_database()
    user_id = None
    if db is not None:
        session = await db.sessions.find_one({"token": token})
        if session:
            user_id = session.get("user_id")
    if not user_id:
        user_id = _mem_sessions.get(token)
    if not user_id:
        return None

    if db is not None:
        user = await db.users.find_one({"$or": [{"_id": user_id}, {"id": user_id}]})
        if user:
            user["id"] = str(user.get("_id", user.get("id")))
            return user
    return _mem_users.get(user_id)


# ─── Pydantic Schemas ────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=40)
    email: str = Field(..., min_length=5, max_length=120)
    password: str = Field(..., min_length=6, max_length=120)
    full_name: Optional[str] = Field(None, max_length=80)
    role: Optional[str] = Field(None, description="Public registrations are strictly 'user' role")


class UserLogin(BaseModel):
    email: str = Field(..., description="Email or Username")
    password: str = Field(..., min_length=1)


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: str
    role: str
    created_at: str


class AuthResponse(BaseModel):
    token: str
    user: UserResponse
    message: str


class AdminCreateUserRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=40)
    email: str = Field(..., min_length=5, max_length=120)
    password: str = Field(..., min_length=6, max_length=120)
    full_name: Optional[str] = Field(None, max_length=80)
    role: str = Field("user", description="'user' or 'admin'")


class AdminUpdateRoleRequest(BaseModel):
    role: str = Field(..., description="'user' or 'admin'")


class AdminResetPasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=6)


# ─── Auth Dependency ─────────────────────────────────────────────────────────

async def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please sign in to access studio functionality.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization.split("Bearer ", 1)[1].strip()
    user = await _find_user_by_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid token. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.post("/register", response_model=AuthResponse)
async def register(body: UserRegister):
    """
    Public registration endpoint.
    Admin accounts CANNOT be created via public registration.
    Any attempt to pass role='admin' is rejected.
    """
    username_clean = body.username.strip().lower()
    email_clean = body.email.strip().lower()

    # Rule: Admin accounts cannot be created publicly
    if body.role and body.role.strip().lower() == "admin":
        raise HTTPException(
            status_code=400,
            detail="Admin accounts cannot be created via public registration. Please use the pre-configured Demo Admin account or contact your system administrator."
        )

    assigned_role = "user"

    # Check for existing username or email
    existing = await _find_user_by_email_or_username(email_clean)
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email address already exists.")

    existing_user = await _find_user_by_email_or_username(username_clean)
    if existing_user:
        raise HTTPException(status_code=400, detail="This username is already taken. Please choose another.")

    pw_hash, salt_hex = _hash_password(body.password)
    user_id = str(uuid.uuid4())
    full_name = body.full_name.strip() if body.full_name else username_clean.capitalize()

    user_record = {
        "_id": user_id,
        "id": user_id,
        "username": username_clean,
        "email": email_clean,
        "full_name": full_name,
        "role": assigned_role,
        "password_hash": pw_hash,
        "salt": salt_hex,
        "created_at": _now(),
    }

    await _save_user(user_record)

    # Issue auth token
    token = secrets.token_urlsafe(32)
    await _save_session(token, user_id)

    user_resp = UserResponse(
        id=user_id,
        username=username_clean,
        email=email_clean,
        full_name=full_name,
        role=assigned_role,
        created_at=user_record["created_at"]
    )

    return AuthResponse(
        token=token,
        user=user_resp,
        message=f"Welcome {full_name}! Your account has been created successfully."
    )


@router.post("/login", response_model=AuthResponse)
async def login(body: UserLogin):
    user = await _find_user_by_email_or_username(body.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    if not _verify_password(body.password, user["password_hash"], user["salt"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = secrets.token_urlsafe(32)
    await _save_session(token, user["id"])

    user_resp = UserResponse(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        full_name=user.get("full_name", user["username"]),
        role=user.get("role", "user"),
        created_at=user.get("created_at", _now())
    )

    return AuthResponse(
        token=token,
        user=user_resp,
        message="Sign in successful."
    )


@router.get("/me", response_model=UserResponse)
async def get_me(user: Dict[str, Any] = Depends(get_current_user)):
    return UserResponse(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        full_name=user.get("full_name", user["username"]),
        role=user.get("role", "user"),
        created_at=user.get("created_at", _now())
    )


@router.get("/users")
async def list_all_users(user: Dict[str, Any] = Depends(get_current_user)):
    """Admin-only endpoint to inspect all registered accounts."""
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Forbidden. Admin role required to view registered users.")

    db = get_database()
    users_list = []
    if db is not None:
        docs = await db.users.find({}, {"password_hash": 0, "salt": 0}).to_list(length=200)
        for d in docs:
            d["id"] = str(d.get("_id", d.get("id")))
            users_list.append(d)
    else:
        for u in _mem_users.values():
            users_list.append({
                "id": u["id"],
                "username": u["username"],
                "email": u["email"],
                "full_name": u.get("full_name", u["username"]),
                "role": u.get("role", "user"),
                "created_at": u.get("created_at", "")
            })

    return {"users": users_list, "total": len(users_list)}


# ─── Admin Management Endpoints ──────────────────────────────────────────────

@router.post("/admin/users", response_model=UserResponse)
async def admin_create_user(body: AdminCreateUserRequest, user: Dict[str, Any] = Depends(get_current_user)):
    """Admin-only endpoint to provision new user or admin accounts."""
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Forbidden. Admin role required.")

    username_clean = body.username.strip().lower()
    email_clean = body.email.strip().lower()
    target_role = body.role.strip().lower()
    if target_role not in ["user", "admin"]:
        target_role = "user"

    existing = await _find_user_by_email_or_username(email_clean)
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists.")

    existing_u = await _find_user_by_email_or_username(username_clean)
    if existing_u:
        raise HTTPException(status_code=400, detail="This username is already in use.")

    pw_hash, salt_hex = _hash_password(body.password)
    user_id = str(uuid.uuid4())
    full_name = body.full_name.strip() if body.full_name else username_clean.capitalize()

    record = {
        "_id": user_id,
        "id": user_id,
        "username": username_clean,
        "email": email_clean,
        "full_name": full_name,
        "role": target_role,
        "password_hash": pw_hash,
        "salt": salt_hex,
        "created_at": _now()
    }

    await _save_user(record)

    return UserResponse(
        id=user_id,
        username=username_clean,
        email=email_clean,
        full_name=full_name,
        role=target_role,
        created_at=record["created_at"]
    )


@router.patch("/admin/users/{target_id}/role")
async def admin_update_user_role(target_id: str, body: AdminUpdateRoleRequest, user: Dict[str, Any] = Depends(get_current_user)):
    """Admin-only: update user role between 'user' and 'admin'. Prevents self-demotion."""
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Forbidden. Admin role required.")

    target = await _find_user_by_id(target_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found.")

    new_role = body.role.strip().lower()
    if new_role not in ["user", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid role. Must be 'user' or 'admin'.")

    # Safety: admin cannot demote their own account
    if user["id"] == target_id and new_role != "admin":
        raise HTTPException(status_code=400, detail="Safety restriction: You cannot demote your own administrator account.")

    await _update_user_fields(target_id, {"role": new_role})
    return {"message": f"User '{target['username']}' role updated to {new_role.upper()}.", "role": new_role}


@router.delete("/admin/users/{target_id}")
async def admin_delete_user(target_id: str, user: Dict[str, Any] = Depends(get_current_user)):
    """Admin-only: delete a user account. Prevents self-deletion."""
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Forbidden. Admin role required.")

    target = await _find_user_by_id(target_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found.")

    # Safety: admin cannot delete their own account
    if user["id"] == target_id:
        raise HTTPException(status_code=400, detail="Safety restriction: You cannot delete your own active administrator account.")

    await _delete_user(target_id)
    return {"message": f"User account '{target['username']}' ({target['email']}) deleted successfully."}


@router.post("/admin/users/{target_id}/reset-password")
async def admin_reset_password(target_id: str, body: AdminResetPasswordRequest, user: Dict[str, Any] = Depends(get_current_user)):
    """Admin-only: reset a user's password."""
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Forbidden. Admin role required.")

    target = await _find_user_by_id(target_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found.")

    pw_hash, salt_hex = _hash_password(body.new_password)
    await _update_user_fields(target_id, {"password_hash": pw_hash, "salt": salt_hex})
    return {"message": f"Password for user '{target['username']}' has been reset successfully."}


# ─── Admin Analytics & Health Telemetry ───────────────────────────────────────

@router.get("/admin/analytics")
async def get_admin_analytics(user: Dict[str, Any] = Depends(get_current_user)):
    """
    Admin-only endpoint providing account health, token consumption, cost breakdown,
    and input/output token usage per individual use.
    """
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Forbidden. Admin role required.")

    from app.services.llm_service import llm_service
    from app.services.token_analytics_service import token_analytics

    health_info = llm_service.get_provider_status()
    db = get_database()
    health_info["storage"] = "mongodb" if db is not None else "in-memory"

    return token_analytics.get_analytics_summary(health_info=health_info)


@router.post("/logout")
async def logout(authorization: Optional[str] = Header(None)):
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split("Bearer ", 1)[1].strip()
        _mem_sessions.pop(token, None)
        db = get_database()
        if db is not None:
            await db.sessions.delete_one({"token": token})
    return {"message": "Signed out successfully."}
