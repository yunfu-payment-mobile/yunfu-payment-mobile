from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI(
    title="云付支付平台"
)

templates = Jinja2Templates(
    directory="templates"
)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request
        }
    )


@app.get("/注册", response_class=HTMLResponse)
async def register(request: Request):
    return templates.TemplateResponse(
        "注册.html",
        {
            "request": request
        }
    )


@app.get("/登录", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse(
        "登录.html",
        {
            "request": request
        }
    )


@app.get("/收款中心", response_class=HTMLResponse)
async def payment_center(request: Request):
    return templates.TemplateResponse(
        "收款中心.html",
        {
            "request": request
        }
    )


@app.get("/订单", response_class=HTMLResponse)
async def orders(request: Request):
    return templates.TemplateResponse(
        "订单.html",
        {
            "request": request
        }
    )


@app.get("/我的", response_class=HTMLResponse)
async def profile(request: Request):
    return templates.TemplateResponse(
        "我的.html",
        {
            "request": request
        }
    )


@app.get("/健康检查")
async def health():
    return {
        "状态": "正常",
        "平台": "云付支付平台"
    }
