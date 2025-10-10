# 專案介紹

assistbot_service 作為一個 micro-service 提供智能助理相關的APIs與後端服務。

# Project function specification

- 使用 Fastapi v15.3.0 + Langchain 開發 chatbot_service 微型服務。
- 使用 Supabase 資料庫。

# 程式資料結構範本

# 程式架構需求
- 使用 app/lib/supabase/admin.py 所定義的 supabase_admin 進行 supabase database 的存取。
- 使用 supabase database 作為檢索資料的來源。
- 使用 pytest 編寫測試程式。
