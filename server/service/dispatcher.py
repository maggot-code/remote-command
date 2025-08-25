# server/service/dispatcher.py
from typing import Callable, Dict, Any

# 注册表，记录每个系统对应的执行函数以及系统信息
SYSTEM_EXECUTORS: Dict[str, Dict[str, Any]] = {}

def register_executor(os_type: str, default_port: int, support_nopwd: bool = True):
    """
    装饰器，用于注册系统执行函数
    os_type: 系统类型
    default_port: 系统默认端口
    support_nopwd: 是否支持免密执行
    """
    def decorator(func: Callable[[dict], dict]):
        SYSTEM_EXECUTORS[os_type.lower()] = {
            "executor": func,
            "default_port": default_port,
            "support_nopwd": support_nopwd
        }
        return func
    return decorator

def dispatch_command(os_type: str, dto: dict) -> dict:
    """
    根据 os_type 调度对应系统的执行函数
    自动填充默认端口，并可在此处理免密校验
    """
    info = SYSTEM_EXECUTORS.get(os_type.lower())
    if not info:
        raise ValueError(f"No executor registered for OS type '{os_type}'")
    
    # 如果 dto 中没有指定 port，则使用默认端口
    if "port" not in dto or dto["port"] is None:
        dto["port"] = info["default_port"]
    
    # 如果系统不支持免密且 password 未提供
    if not info["support_nopwd"] and dto.get("password") is None:
        raise ValueError(f"{os_type} does not support passwordless execution")
    
    # 调用对应系统的执行函数
    return info["executor"](dto)
