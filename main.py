from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(
    title="云付支付平台"
)


@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
    <meta charset="UTF-8">
    <meta name="viewport"
    content="width=device-width,initial-scale=1.0">

    <title>云付支付平台</title>

    <style>
    body{
        margin:0;
        background:#f3f8ff;
        font-family:
        -apple-system,BlinkMacSystemFont,
        "PingFang SC",
        sans-serif;
    }

    .box{
        margin:80px 25px;
        background:white;
        padding:35px;
        border-radius:20px;
        text-align:center;
    }

    h1{
        color:#1f5eff;
    }

    button{
        width:100%;
        padding:15px;
        margin-top:15px;
        border:0;
        border-radius:12px;
        background:#2868ff;
        color:white;
        font-size:18px;
    }

    .register{
        background:#eaf2ff;
        color:#2868ff;
    }

    </style>

    </head>

    <body>

    <div class="box">

    <h1>云付</h1>

    <p>
    商户支付平台
    </p>

    <button>
    登录
    </button>

    <button class="register">
    注册
    </button>

    </div>

    </body>
    </html>
    """
