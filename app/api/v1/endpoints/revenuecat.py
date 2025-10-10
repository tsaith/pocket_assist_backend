import os
import requests
import json
from fastapi import APIRouter, Request, HTTPException, Depends
from typing import Dict, Any
from datetime import datetime
from app.lib.supabase.admin import supabase_admin


router = APIRouter(prefix="/api/v1/revenuecat")


@router.post("/webhook")
async def revenuecat_webhook(request: Request):
    """
    接收並處理 RevenueCat webhook 資料
    
    RevenueCat 會在以下事件發生時發送 webhook：
    - INITIAL_PURCHASE: 首次購買
    - RENEWAL: 訂閱續訂
    - CANCELLATION: 取消訂閱
    - UNCANCELLATION: 恢復訂閱
    - NON_RENEWING_PURCHASE: 非續訂型購買
    - SUBSCRIPTION_PAUSED: 訂閱暫停
    - EXPIRATION: 訂閱過期
    - BILLING_ISSUE: 帳單問題
    - PRODUCT_CHANGE: 產品變更
    - TRANSFER: 訂閱轉移
    """
    try:
        # 獲取原始請求體
        raw_body = await request.body()
        
        # 解析 JSON 資料
        webhook_data = await request.json()
        
        # 獲取當前時間戳
        timestamp = datetime.now().isoformat()
        
        # 打印基本資訊
        print("\n" + "="*80)
        print(f"[RevenueCat Webhook] 收到 webhook 請求 - {timestamp}")
        print("="*80)
        
        # 打印完整的 webhook 資料
        print("\n📦 完整 Webhook 資料:")
        print(json.dumps(webhook_data, indent=2, ensure_ascii=False))
        
        # 提取並打印關鍵資訊
        event = webhook_data.get('event', {})
        event_type = event.get('type', 'UNKNOWN')
        
        print(f"\n📋 事件類型: {event_type}")
        
        # 提取用戶資訊
        if 'app_user_id' in event:
            app_user_id = event.get('app_user_id')
            print(f"👤 用戶 ID: {app_user_id}")
        
        # 提取產品資訊
        if 'product_id' in event:
            product_id = event.get('product_id')
            print(f"📱 產品 ID: {product_id}")
        
        # 提取訂閱資訊
        if 'period_type' in event:
            period_type = event.get('period_type')
            print(f"📅 週期類型: {period_type}")
        
        if 'purchased_at_ms' in event:
            purchased_at_ms = event.get('purchased_at_ms')
            purchased_at = datetime.fromtimestamp(purchased_at_ms / 1000)
            print(f"🕐 購買時間: {purchased_at.isoformat()}")
        
        if 'expiration_at_ms' in event:
            expiration_at_ms = event.get('expiration_at_ms')
            if expiration_at_ms:
                expiration_at = datetime.fromtimestamp(expiration_at_ms / 1000)
                print(f"⏰ 過期時間: {expiration_at.isoformat()}")
        
        # 提取價格資訊
        if 'price' in event:
            price = event.get('price')
            currency = event.get('currency', 'USD')
            print(f"💰 價格: {price} {currency}")
        
        # 提取環境資訊
        if 'environment' in event:
            environment = event.get('environment')
            print(f"🌍 環境: {environment}")
        
        # 打印請求標頭（用於驗證）
        print("\n📨 請求標頭:")
        for header, value in request.headers.items():
            if header.lower() in ['x-revenuecat-signature', 'content-type', 'user-agent']:
                print(f"  {header}: {value}")
        
        print("\n" + "="*80 + "\n")
        
        # Extract user_id and product_id for subscription update
        user_id = event.get('app_user_id')
        product_id = event.get('product_id')
        
        tier = "free"
        # Update subscriptions table if we have user_id
        if user_id:
            if event_type in ['INITIAL_PURCHASE', 'RENEWAL']:
                if product_id:
                    # Normal subscription event, determine tier based on product_id prefix
                    tier = "pro" if product_id[:3].lower() == 'pro' else "free"
                else:
                    # No product_id and not a cancellation/expiration, skip update
                    print(f"⚠️ 缺少 product_id，無法判斷訂閱等級")
                    tier = None
            elif event_type == 'EXPIRATION':
                tier = "free"
                print(f"⏰ 檢測到訂閱過期事件 - 過期原因: {event.get('expiration_reason', 'N/A')}")

            elif event_type == 'CANCELLATION':
                print(f"🔴 檢測到取消訂閱事件 - 取消原因: {event.get('cancel_reason', 'N/A')}")
                tier = None
            elif event_type == 'UNCANCELLATION':
                print(f"🔴 檢測到恢復訂閱事件 - 恢復原因: {event.get('uncancel_reason', 'N/A')}")
                tier = None
            else:
                # Other event types, skip update
                print(f"⚠️ 事件類型: {event_type}")
                print(f"⚠️ 其他事件類型，無法判斷訂閱等級")
                tier = None

            if tier is not None:
                try:
                    # Update subscriptions table
                    update_result = supabase_admin.table('subscriptions').update({
                        'tier': tier,
                        'updated_at': datetime.now().isoformat()
                    }).eq('user_id', user_id).execute()
                    
                    print(f"✅ 已更新訂閱資料 - 用戶: {user_id}, 等級: {tier}, 事件類型: {event_type}")
                    
                except Exception as db_error:
                    error_msg = f"更新訂閱資料時發生錯誤: {str(db_error)}"
                    print(f"❌ {error_msg}")
                    # Don't raise exception here, just log the error
                    # The webhook should still return success to RevenueCat
        else:
            print(f"⚠️ 缺少 user_id，無法更新訂閱資料")
        
        # 返回成功響應
        return {
            "success": True,
            "message": "Webhook received successfully",
            "event_type": event_type,
            "timestamp": timestamp
        }
        
    except json.JSONDecodeError as e:
        error_msg = f"JSON 解析錯誤: {str(e)}"
        print(f"❌ {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)
    
    except Exception as e:
        error_msg = f"處理 webhook 時發生錯誤: {str(e)}"
        print(f"❌ {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)