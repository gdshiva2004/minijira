from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import current_app, g, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from .database import get_db
from .services import to_object_id


def hash_password(password):
    return generate_password_hash(password, method=current_app.config["PASSWORD_HASH_METHOD"])


def check_credentials(member, password):
    stored = member.get("password_hash") if member else None
    if stored is None:
        hash_password("unused-password")
        return False
    return check_password_hash(stored, password)


def create_token(member_id, expires_minutes=None):
    minutes = current_app.config["JWT_EXPIRES_MINUTES"] if expires_minutes is None else expires_minutes
    issued = datetime.now(timezone.utc)
    payload = {
        "sub": str(member_id),
        "iat": issued,
        "exp": issued + timedelta(minutes=minutes),
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET"], algorithm="HS256")


def decode_token(token):
    return jwt.decode(
        token,
        current_app.config["JWT_SECRET"],
        algorithms=["HS256"],
        options={"require": ["exp", "sub"]},
    )


def unauthorized(message):
    response = jsonify({"error": message})
    response.status_code = 401
    response.headers["WWW-Authenticate"] = "Bearer"
    return response


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        scheme, _, token = request.headers.get("Authorization", "").partition(" ")
        if scheme.lower() != "bearer" or not token.strip():
            return unauthorized("Authentication required")
        try:
            payload = decode_token(token.strip())
        except jwt.ExpiredSignatureError:
            return unauthorized("Session expired, please log in again")
        except jwt.InvalidTokenError:
            return unauthorized("Invalid token")

        member_id = to_object_id(payload["sub"])
        member = get_db().members.find_one({"_id": member_id}) if member_id else None
        if member is None:
            return unauthorized("Account no longer exists")

        g.member = member
        return view(*args, **kwargs)

    return wrapper
