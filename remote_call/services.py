"""
业务服务层：负责参数组装、上下文生成、权限校验、调用 ansible 等操作。
主要职责：
1. 组装和校验请求参数，生成上下文。
2. 生成 ansible 配置和 inventory。
3. 组装 Ansible 任务上下文。
4. 调用 ansible runner 执行任务。
"""
from .context import RemoteCallContext
from ansible.runner import AnsibleTaskContext,run_ansible_with_context
from ansible.config import get_ansible_config
from ansible.inventory import generate_inventory


def RemoteCallService(data: dict):
    """
    业务流程编排服务。
    
    接收请求参数字典，完成如下操作：
    1. 校验参数并构建用户上下文。
    2. 生成 ansible 配置。
    3. 组装 Ansible 任务上下文（自动推断参数）。
    4. 生成 ansible inventory。
    5. 调用 ansible runner 执行任务，并返回结果。

    Args:
        data (dict): 请求参数字典。

    Returns:
        dict: 包含主任务输出、全部步骤结果、主任务 event_data、错误信息及状态。
    """
    # 1. 参数校验与上下文构建
    # RemoteCallContext 用于封装和校验用户请求参数，生成标准上下文对象
    user_context = RemoteCallContext(**data)

    # 2. 生成 ansible 配置
    # get_ansible_config 返回 ansible 相关的配置信息
    config_context = get_ansible_config()

    # 3. 组装 AnsibleTaskContext（自动推断参数）
    # 该步骤可能因参数不合法等原因抛出异常
    try:
        task_context = AnsibleTaskContext(user_context, config_context)
    except Exception as e:
        # 组装任务上下文失败，直接返回错误信息
        return {
            "data": None,
            "target": None,
            "error": str(e),
            "status": "error"
        }

    # 4. 生成 inventory 文件
    # generate_inventory 返回 inventory 路径和清理函数
    inventory_path, cleanup = generate_inventory(user_context, config_context)

    # 5. 调用 ansible runner 执行任务
    # run_ansible_with_context 为纯函数，实际执行 ansible 任务
    result = run_ansible_with_context(
        user_context,
        config_context,
        task_context,
        inventory_path
    )
    # 执行完毕后清理临时 inventory 文件
    cleanup()

    # 返回结构化结果，便于后续扩展
    return {
        "data": result.get("data"),          # 主任务输出
        "all_results": result.get("all_results"),  # 全部步骤结果
        "target": result.get("target"),      # 主任务 event_data
        "error": result.get("error"),
        "status": result.get("status", "success")
    }


