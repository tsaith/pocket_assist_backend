import platform
import time
from datetime import datetime
import psutil

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict


# 创建健康检查路由器
router = APIRouter(prefix="/api/v1", tags=["v1"])

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    uptime: float = None
    system_info: dict
    memory_usage: dict = None

# 定义健康检查函数
async def health():
    """
    获取系统健康状态
    提供服务器运行情况、系统信息、内存使用
    """
    uptime = None
    memory_info = {}
    
    # 获取系统启动时间
    boot_time = psutil.boot_time()
    uptime = time.time() - boot_time
    
    # 获取内存使用情况
    memory = psutil.virtual_memory()
    memory_info = {
        "total": f"{memory.total / (1024**3):.2f} GB",
        "available": f"{memory.available / (1024**3):.2f} GB",
        "percent": f"{memory.percent}%"
    }
    
    system_info = {
        "platform": platform.system(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "processor": platform.processor(),
    }
    
    # 返回整体健康状态
    return HealthResponse(
        status="success",
        timestamp=datetime.now().isoformat(),
        uptime=uptime,
        system_info=system_info,
        memory_usage=memory_info
    )

@router.get("/health", response_model=HealthResponse)
async def health_endpoint():
    """系统健康检查接口"""
    return await health()