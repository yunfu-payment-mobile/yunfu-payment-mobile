from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pathlib import Path

app = FastAPI(
    title="云付支付平台"
)

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"


def read_page(filename: str) -> str:
    file_path = TEMPLATES_DIR / filename

    if not file_path.exists():
        return f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport"
                  content="width=device-width, initial-scale=1.0">
            <title>云付支付平台</title>
        </head>
        <body>
            <h1>页面不存在</h1>
            <p>找不到：{filename}</p>
        </body>
        </html>
        """

    return file_path.read_text(encoding="utf-8")


@app.get("/", response_class=HTMLResponse)
async def home():
    return read_page("index.html")


@app.get("/注册", response_class=HTMLResponse)
async def register():
    return read_page("注册.html")


@app.get("/登录", response_class=HTMLResponse)
async def login():
    return read_page("登录.html")


@app.get("/收款中心", response_class=HTMLResponse)
async def payment_center():
    return read_page("收款中心.html")


@app.get("/订单", response_class=HTMLResponse)
async def orders():
    return read_page("订单.html")


@app.get("/我的", response_class=HTMLResponse)
async def profile():
    return read_page("我的.html")


@app.get("/健康检查")
async def health():
    return {
        "状态": "正常",
        "平台": "云付支付平台"
    }
