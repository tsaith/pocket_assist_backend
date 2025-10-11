# 專案介紹

pocket_assist_backend 作為一個 micro-service 提供智能助理相關的APIs與後端服務。

# Project function specification

- 使用 Fastapi v15.3.0 + Langchain 開發智能助理服務。
- 使用 Supabase 資料庫。


# 程式架構需求
- 使用 app/lib/supabase/admin.py 所定義的 supabase_admin 進行 supabase database 的存取。
- 使用 supabase database 作為檢索資料的來源。
- 使用 pytest 編寫測試程式。

# 資料與檔案結構

## 主要目錄結構

```
pocket_assist_backend/
├── main.py                 # 應用程式主入口，FastAPI 應用初始化
├── Dockerfile             # Docker 容器配置
├── pyproject.toml         # Poetry 依賴管理配置
├── poetry.lock            # Poetry 依賴鎖定文件
├── README.md              # 專案說明文檔
├── project-spec.md        # 專案規格文檔
│
├── app/                   # 主應用程式目錄
│   ├── __init__.py
│   ├── api/               # API 路由層
│   │   └── v1/            # API v1 版本
│   │       ├── api.py     # API 路由聚合
│   │       ├── endpoints/ # API 端點實現
│   │       │   ├── auth.py              # 認證相關端點
│   │       │   ├── chat.py              # 聊天功能端點
│   │       │   ├── chatbot_manager.py   # 聊天機器人管理端點
│   │       │   ├── chatbots.py          # 聊天機器人 CRUD 端點
│   │       │   ├── credit_manager.py    # 積分管理端點
│   │       │   ├── documents.py         # 文檔管理端點
│   │       │   ├── health.py            # 健康檢查端點
│   │       │   ├── line.py              # LINE 整合端點
│   │       │   ├── notebooks.py         # 筆記本管理端點
│   │       │   ├── reminders.py         # 提醒功能端點
│   │       │   ├── revenuecat.py        # RevenueCat 整合端點
│   │       │   ├── token_manager.py     # Token 管理端點
│   │       │   └── webhooks.py          # Webhook 端點
│   │       └── webhook_del/             # Webhook 相關模組
│   │           └── linebot.py           # LINE Bot Webhook 處理
│   │
│   ├── core/              # 核心配置模組
│   │   ├── config.py      # 應用配置管理
│   │   └── setup_cors.py  # CORS 設定
│   │
│   ├── lib/               # 業務邏輯與工具庫
│   │   ├── agent_exp/     # Agent 實驗模組
│   │   │   ├── rag_agent.py    # RAG Agent 實現
│   │   │   └── react_agent.py  # ReAct Agent 實現
│   │   │
│   │   ├── chatbot/       # 聊天機器人核心模組
│   │   │   ├── chatbot_base.py # 聊天機器人基礎類
│   │   │   ├── chatbot.py      # 聊天機器人主實現
│   │   │   ├── linebot.py      # LINE Bot 實現
│   │   │   ├── utils.py        # 聊天機器人工具函數
│   │   │   └── tools/          # 聊天機器人工具集
│   │   │       ├── bookkeeping_tools.py    # 記帳工具
│   │   │       ├── calendar_event_tools.py # 日曆事件工具
│   │   │       ├── help_tools.py           # 幫助工具
│   │   │       ├── location_tools.py       # 位置工具
│   │   │       ├── memory_tools.py         # 記憶工具
│   │   │       ├── note_tools.py           # 筆記工具
│   │   │       ├── other_tools.py          # 其他工具
│   │   │       ├── reminder_tools.py       # 提醒工具
│   │   │       ├── time_tools.py           # 時間工具
│   │   │       └── user_preference_tools.py # 用戶偏好工具
│   │   │
│   │   ├── chatbot_manager.py  # 聊天機器人管理器
│   │   ├── credit_manager.py   # 積分管理器
│   │   ├── reminder_manager.py # 提醒管理器
│   │   ├── encryption.py       # 加密工具
│   │   │
│   │   ├── google/        # Google 服務整合
│   │   │   ├── gcs_upload.py  # GCS 上傳功能
│   │   │   └── gcs_utils.py   # GCS 工具函數
│   │   │
│   │   ├── line/          # LINE 服務整合
│   │   │   └── official_account.py # LINE 官方帳號
│   │   │
│   │   ├── robots/        # 機器人模組
│   │   │   └── ragbot/    # RAG 機器人
│   │   │       ├── bot_builder.py # 機器人建構器
│   │   │       ├── ragbot.py      # RAG 機器人實現
│   │   │       └── utils.py       # RAG 機器人工具
│   │   │
│   │   ├── supabase/      # Supabase 資料庫整合
│   │   │   ├── admin.py   # Supabase 管理員客戶端
│   │   │   └── utils.py   # Supabase 工具函數
│   │   │
│   │   └── utils/         # 通用工具函數
│   │       ├── db_utils.py    # 資料庫工具
│   │       ├── time_utils.py  # 時間工具
│   │       └── user_utils.py  # 用戶工具
│   │
│   ├── models/            # 資料模型（ORM 模型）
│   └── schemas/           # Pydantic 資料模式（API 請求/響應模型）
│
├── bash/                  # 部署腳本
│   ├── deploy_image_to_cloud_run.sh  # 部署 Docker 映像到 Cloud Run
│   └── deploy_source_to_cloud_run.sh # 部署原始碼到 Cloud Run
│
├── scripts/               # 工具腳本
│   └── deploy_source_to_cloud_run_function.py # Cloud Run 部署函數
│
├── data/                  # 測試與範例資料
│   └── [user_id]/         # 按用戶 ID 組織的資料目錄
│       └── notebook.txt   # 筆記本資料
│
├── examples/              # 範例程式碼
│   ├── agent_endpoint.py               # Agent 端點範例
│   ├── agent.py                        # Agent 範例
│   ├── assistant_bot_llamaindex.py     # LlamaIndex 助理機器人範例
│   ├── chatbot_agent.py                # 聊天機器人 Agent 範例
│   ├── chatbot_with_rag.py             # 帶 RAG 的聊天機器人範例
│   ├── check_ragbot.py                 # RAG 機器人檢查範例
│   ├── gcs_upload.py                   # GCS 上傳範例
│   ├── gcs_download.py                 # GCS 下載範例
│   ├── grok_llm.py                     # Grok LLM 範例
│   ├── rag_with_react_agent.py         # RAG + ReAct Agent 範例
│   ├── vector_store.py                 # 向量存儲範例
│   └── supabase/                       # Supabase 操作範例
│       ├── create_user.py              # 創建用戶
│       ├── get_chatbot_data.py         # 獲取聊天機器人資料
│       ├── get_user_by_id.py           # 按 ID 獲取用戶
│       ├── get_user_profile.py         # 獲取用戶資料
│       ├── match_sections.py           # 匹配段落
│       ├── select_users.py             # 查詢用戶
│       ├── set_user_as_admin.py        # 設置管理員
│       └── update_user.py              # 更新用戶
│
├── notebooks/             # Jupyter Notebook 實驗與原型
│   ├── AgenticRag.ipynb
│   ├── assistbot_chatbot.ipynb
│   ├── langgraph_adaptive_rag.ipynb
│   ├── langgraph_agentic_rag.ipynb
│   ├── rag_agent_part1.ipynb
│   ├── rag_agent_part2.ipynb
│   ├── rag_with_react_agent.ipynb
│   ├── react_agent.ipynb
│   └── test_encryption.ipynb
│
└── tests/                 # 測試程式
    └── test_encription.py # 加密功能測試

```

## 核心模組說明

### 1. API 層（app/api/v1/）
- 遵循 FastAPI 的路由結構
- 所有 API 端點位於 `endpoints/` 目錄下
- `api.py` 負責聚合所有端點路由

### 2. 業務邏輯層（app/lib/）
- **chatbot/** - 聊天機器人核心功能，包含工具集
- **agent_exp/** - Agent 實驗性功能（RAG、ReAct）
- **robots/ragbot/** - RAG 機器人實現
- **supabase/** - 資料庫操作（使用 `supabase_admin` 進行資料存取）
- **google/** - Google Cloud Storage 整合
- **line/** - LINE 官方帳號整合
- **utils/** - 通用工具函數

### 3. 配置層（app/core/）
- `config.py` - 應用配置管理（使用環境變數）
- `setup_cors.py` - CORS 配置

### 4. 資料層
- **app/models/** - SQLAlchemy ORM 模型
- **app/schemas/** - Pydantic 資料模式
- **Supabase** - 主要資料庫，用於持久化存儲和檢索

## 關鍵檔案

- **main.py** - FastAPI 應用程式入口點
- **app/lib/supabase/admin.py** - 定義 `supabase_admin` 實例，所有資料庫操作應使用此實例
- **app/lib/chatbot/chatbot_base.py** - 聊天機器人基礎類別
- **app/core/config.py** - 環境配置與設定管理

## 資料存儲

- **主資料庫**: Supabase（PostgreSQL）
- **向量存儲**: 用於 RAG 檢索（ChromaDB）
- **檔案存儲**: Google Cloud Storage（GCS）
- **本地資料**: `data/` 目錄（僅用於測試與開發）

