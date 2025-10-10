from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def setup_cors(app: FastAPI):

    origins = [
        #"http://localhost",
        #"http://127.0.0.1",
        "http://localhost:3000", # Assistbot development
        "https://assistbot.cloud", # Assistbot production
        "http://localhost:5173", # ChatWidget development
        "http://localhost:8000" # ChatWidget development
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,             # 设置允许的来源
        allow_credentials=True,            # 是否允许发送 Cookies
        allow_methods=["*"],               # 允许的 HTTP 方法，例如 GET、POST
        allow_headers=["*"],               # 允许的请求头
    )
