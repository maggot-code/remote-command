import tempfile
import os
from typing import Any, Optional

def build_response(
    status: str = "success",
    data: Any = None,
    error: Optional[Any] = None,
    target: Optional[Any] = None,
    all_results: Optional[Any] = None
) -> dict:
    """
    构造标准API响应结构，支持多步任务链结果。
    :param status: 响应状态，"success" 或 "error"
    :param data: 业务数据内容
    :param error: 错误信息
    :param target: ansible运行元数据（可选）
    :param all_results: 多步任务链全部步骤结果（可选）
    :return: dict类型的标准响应体
    """
    resp = {
        "status": status,
        "data": data,
        "error": error
    }
    if target is not None:
        resp["target"] = target  # 仅在有ansible元数据时添加
    if all_results is not None:
        resp["all_results"] = all_results  # 多步任务链时返回所有步骤结果
    return resp

def write_temp_file(content: str, suffix: str = "", prefix: str = "tmp", dir: Optional[str] = None):
    """
    写入内容到临时文件，返回文件路径、关闭文件的函数和清理文件的函数。
    :param content: 文件内容字符串
    :param suffix: 文件后缀名（如 .txt）
    :param prefix: 文件前缀名
    :param dir: 临时文件存放目录（默认系统临时目录）
    :return: (file_path, close_func, cleanup_func)
        file_path: 临时文件路径
        close_func: 关闭文件对象的函数
        cleanup_func: 删除临时文件的函数
    """
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix, prefix=prefix, dir=dir, mode="w+")
    temp.write(content)  # 写入内容
    temp.flush()  # 刷新缓冲区，确保内容写入磁盘
    file_path = temp.name
    def close_func():
        temp.close()  # 关闭文件对象
    def cleanup_func():
        try:
            os.remove(file_path)  # 删除临时文件
        except Exception:
            pass  # 文件可能已被删除，忽略异常
    return file_path, close_func, cleanup_func

def read_file_content(file_path: str):
    """
    读取指定文件内容，返回内容和关闭文件的函数。
    :param file_path: 文件路径
    :return: (content, close_func)
        content: 文件内容字符串
        close_func: 关闭文件对象的函数
    """
    f = open(file_path, "r")
    content = f.read()  # 读取全部内容
    def close_func():
        f.close()  # 关闭文件对象
    return content, close_func