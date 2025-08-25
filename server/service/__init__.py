import os
import importlib

# 自动导入当前目录下的模块（除了 dispatcher 和 __init__）
current_dir = os.path.dirname(__file__)
for filename in os.listdir(current_dir):
    if filename.endswith(".py") and filename not in ("__init__.py", "dispatcher.py"):
        module_name = f"server.service.{filename[:-3]}"
        importlib.import_module(module_name)
