import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI(title="云付支付平台")

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
DB_PATH = BASE_DIR / "yunfu.db"

# 本地测试默认验证码。部署正式环境时请通过环境变量 REGISTRATION_CODE 设置，
# 并接入真实短信服务，不要继续使用固定验证码。
REGISTRATION_CODE = os.getenv("REGISTRATION_CODE", "123456")
SESSION_SECRET = os.getenv("SESSION_SECRET", "yunfu-local-development-secret-change-me")

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    session_cookie="yunfu_session",
    max_age=60 * 60 * 24 * 7,
    same_site="lax",
    https_only=False,  # 本地 HTTP 测试保持 False；正式 HTTPS 部署应改为 True
)


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS merchants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def hash_password(password: str) -> str:
    """使用 PBKDF2-HMAC-SHA256 保存密码，不保存明文。"""
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        300_000,
    )
    return f"pbkdf2_sha256$300000${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations, salt_hex, digest_hex = stored_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            int(iterations),
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def validate_phone(phone: str) -> bool:
    return bool(re.fullmatch(r"1[3-9]\d{9}", phone))


def read_page(filename: str) -> str:
    file_path = TEMPLATES_DIR / filename

    if not file_path.exists():
        return """
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>云付支付平台</title>
            <style>
                body{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;background:#F3F8FE;margin:0;padding:40px;color:#172338}
                .box{max-width:520px;margin:80px auto;background:#fff;border:1px solid #DCE8F4;border-radius:22px;padding:30px;text-align:center}
                a{color:#2F6FED;text-decoration:none}
            </style>
        </head>
        <body><div class="box"><h2>页面暂未加入</h2><p>找不到：%s</p><a href="/登录">进入商户登录</a></div></body>
        </html>
        """ % filename

    return file_path.read_text(encoding="utf-8")


def require_login(request: Request):
    phone = request.session.get("phone")
    if not phone:
        return RedirectResponse(url="/登录?next=/", status_code=303)
    return phone


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    phone = request.session.get("phone")

    if not phone:
        return RedirectResponse(
            url="/登录",
            status_code=303
        )

    return read_page("index.html")


@app.get("/注册", response_class=HTMLResponse)
async def register_page():
    return read_page("注册.html")


@app.get("/登录", response_class=HTMLResponse)
async def login_page():
    return read_page("登录.html")


@app.post("/api/注册")
async def register_api(request: Request):
    try:
        data = await request.json()

        phone = str(data.get("phone", "")).strip()
        code = str(data.get("code", "")).strip()
        password = str(data.get("password", ""))
        confirm_password = str(data.get("confirm_password", ""))

        # 后面的注册逻辑继续保持

    except json.JSONDecodeError:
        return JSONResponse({
            "success": False,
            "message": "数据格式错误"
        })
    if not validate_phone(phone):
        return JSONResponse({"success": False, "message": "请输入正确的11位手机号码"}, status_code=400)

    if code != REGISTRATION_CODE:
        return JSONResponse({"success": False, "message": "验证码错误"}, status_code=400)

    if len(password) < 6 or len(password) > 72:
        return JSONResponse({"success": False, "message": "登录密码长度应为6-72位"}, status_code=400)

    if password != confirm_password:
        return JSONResponse({"success": False, "message": "两次输入的密码不一致"}, status_code=400)

    password_hash = hash_password(password)
    created_at = datetime.now(timezone.utc).isoformat()

    try:
        with get_db() as conn:
            conn.execute(
                "INSERT INTO merchants (phone, password_hash, created_at) VALUES (?, ?, ?)",
                (phone, password_hash, created_at),
            )
            conn.commit()
    except sqlite3.IntegrityError:
        return JSONResponse({"success": False, "message": "该手机号已经注册，请直接登录"}, status_code=409)

    return JSONResponse({"success": True, "message": "注册成功", "redirect": "/登录"})


@app.post("/api/登录")
async def login_api(request: Request):
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return JSONResponse({"success": False, "message": "请求数据格式错误"}, status_code=400)

    phone = str(data.get("phone", "")).strip()
    password = str(data.get("password", ""))
    next_url = str(data.get("next", "/")).strip() or "/"

    # 防止使用外部地址进行开放重定向。
    if not next_url.startswith("/") or next_url.startswith("//"):
        next_url = "/"

    if not validate_phone(phone):
        return JSONResponse({"success": False, "message": "请输入正确的手机号"}, status_code=400)

    with get_db() as conn:
        merchant = conn.execute(
            "SELECT id, phone, password_hash FROM merchants WHERE phone = ?",
            (phone,),
        ).fetchone()

    if merchant is None or not verify_password(password, merchant["password_hash"]):
    return JSONResponse({
        "success": False,
        "message": "账号或密码错误"
    })


request.session["phone"] = phone

return JSONResponse({
    "success": True,
    "redirect": "/"
})

    request.session.clear()
    request.session["merchant_id"] = merchant["id"]
    request.session["phone"] = merchant["phone"]

    return JSONResponse({"success": True, "message": "登录成功", "redirect": next_url})


@app.post("/api/退出")
async def logout_api(request: Request):
    request.session.clear()
    return JSONResponse({"success": True, "redirect": "/登录"})


@app.get("/api/当前用户")
async def current_user(request: Request):
    phone = request.session.get("phone")
    if not phone:
        return JSONResponse({"logged_in": False}, status_code=401)
    return {"logged_in": True, "phone": phone}


@app.get("/收款中心", response_class=HTMLResponse)
async def payment_center(request: Request):
    result = require_login(request)
    if not isinstance(result, str):
        return result
    return read_page("收款中心.html")


@app.get("/订单", response_class=HTMLResponse)
async def orders(request: Request):
    result = require_login(request)
    if not isinstance(result, str):
        return result
    return read_page("订单.html")


@app.get("/我的", response_class=HTMLResponse)
async def profile(request: Request):
    result = require_login(request)
    if not isinstance(result, str):
        return result
    return read_page("我的.html")


@app.get("/健康检查")
async def health():
    return {"状态": "正常", "平台": "云付支付平台"}
