"""
政府/学校采购公告 AI 可行性分析工具
FastAPI 入口文件

启动方式：
    # 安装依赖
    pip install -r requirements.txt

    # 配置 API key
    cp .env.example .env
    # 编辑 .env，填入 DEEPSEEK_API_KEY

    # 启动服务
    uvicorn main:app --reload --port 8000

    # 用 ngrok 暴露给外部（可选）
    ngrok http 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from routes.analyze import router as analyze_router

app = FastAPI(
    title="招标公告 AI 分析",
    description="上传采购公告，AI 帮你判断值不值得投标",
    version="0.1.0",
)

# CORS：允许前端页面（包括 file:// 协议）调用 API
# 生产环境应限制为具体域名，但 MVP 阶段全部放开
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册分析路由
app.include_router(analyze_router)

# 挂载静态文件目录（前端 HTML 表单）
app.mount("/", StaticFiles(directory="static", html=True), name="static")
