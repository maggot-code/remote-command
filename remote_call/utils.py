import tempfile
import os
from typing import Any, Optional

def is_valid_ip(ip: str) -> bool:
    """简单校验IP格式"""
    # TODO: 可用正则或ipaddress模块增强
    return isinstance(ip, str) and len(ip.split('.')) == 4

def build_response(status: str = "success", data: Any = None, error: Optional[Any] = None, target: Optional[Any] = None, all_results: Optional[Any] = None):
    """
    构造标准API响应结构，支持多步任务链结果
    :param status: "success" or "error"
    :param data: 业务数据
    :param error: 错误信息
    :param target: ansible运行元数据（可选）
    :param all_results: 多步任务链全部步骤结果（可选）
    :return: dict
    """
    resp = {
        "status": status,
        "data": data,
        "error": error
    }
    if target is not None:
        resp["target"] = target
    if all_results is not None:
        resp["all_results"] = all_results
    return resp

def write_temp_file(content: str, suffix: str = "", prefix: str = "tmp", dir: Optional[str] = None):
    """
    写入临时文件，返回文件路径、关闭文件的函数和清理文件的函数
    :param content: 文件内容
    :param suffix: 文件后缀
    :param prefix: 文件前缀
    :param dir: 临时文件目录
    :return: (file_path, close_func, cleanup_func)
    """
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix, prefix=prefix, dir=dir, mode="w+")
    temp.write(content)
    temp.flush()
    file_path = temp.name
    def close_func():
        temp.close()
    def cleanup_func():
        try:
            os.remove(file_path)
        except Exception:
            pass
    return file_path, close_func, cleanup_func

def read_file_content(file_path: str):
    """
    读取文件内容，返回内容和关闭文件的函数
    :param file_path: 文件路径
    :return: (content, close_func)
    """
    f = open(file_path, "r")
    content = f.read()
    def close_func():
        f.close()
    return content, close_func