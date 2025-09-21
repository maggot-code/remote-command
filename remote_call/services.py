"""
业务服务层，负责参数组装、上下文生成、权限校验、调用ansible等。
"""
from .context import RemoteCallContext
from ansible.runner import AnsibleTaskContext,run_ansible_with_context
from ansible.config import get_ansible_config
from ansible.inventory import generate_inventory


def RemoteCallService(data: dict):
    """
    负责整体业务流程的编排，接收请求参数字典，组装上下文、inventory、AnsibleTaskContext等关键信息
    暂不执行ansible，仅返回关键编排信息，便于后续扩展
    """
    # 1. 参数校验与上下文构建
    user_context = RemoteCallContext(**data)

    # 2. 生成ansible配置
    config_context = get_ansible_config()

    # 3. 组装AnsibleTaskContext（自动推断参数）
    try:
        task_context = AnsibleTaskContext(user_context, config_context)
    except Exception as e:
        return {
            "data": None,
            "target": None,
            "error": str(e),
            "status": "error"
        }

    # 4. 生成inventory
    inventory_path, cleanup = generate_inventory(user_context, config_context)

    # 5. 调用runner纯函数（此处可后续补充实际执行）
    result = run_ansible_with_context(
        user_context,
        config_context,
        task_context,
        inventory_path
    )
    cleanup()

    return {
        "data": result.get("data"),  # 主任务输出
        "all_results": result.get("all_results"),  # 全部步骤结果
        "target": result.get("target"),  # 主任务event_data
        "error": result.get("error"),
        "status": result.get("status", "success")
    }


