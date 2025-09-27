"""
动态生成 Ansible playbook 文件。
本模块根据用户上下文和命令参数，动态拼接 playbook 内容并写入临时文件，
用于后续 ansible_runner.run 的 playbook 调用。
"""
from typing import Tuple, Callable, List
from remote_call.context import RemoteCallContext
from ansible.config import AnsibleConfig
from remote_call.utils import write_temp_file
import logging
import yaml

logger = logging.getLogger('django')

def generate_playbook(
	user_ctx: 'RemoteCallContext',
	ansible_cfg: 'AnsibleConfig',
	extra_vars: dict = None
) -> Tuple[str, Callable]:
    """
    动态生成 ansible playbook 内容并写入临时文件。

    Args:
        group_name (str): 主机分组名，对应 inventory 的 group。
        commands (List[str]): 需要在 h3c 设备上执行的命令列表。
        become (bool, optional): 是否提权。
        become_method (str, optional): 提权方式。
        become_password (str, optional): 提权密码。

    Returns:
        tuple[str, callable]: (playbook 文件路径, 清理函数)
    """
    # 获取主机分组名
    group_name = user_ctx.get_group_name()

    play = {
        'hosts': group_name,
        'gather_facts': False,
        'tasks': [
            {
                'name': '执行 H3C 命令（raw）',
                'raw': (
                    user_ctx.command if isinstance(user_ctx.command, str)
                    else ' && '.join(user_ctx.command) if hasattr(user_ctx, 'command') and isinstance(user_ctx.command, (list, tuple))
                    else ''
                )
            }
        ]
    }
    playbook = [play]
    content = yaml.dump(playbook, allow_unicode=True, sort_keys=False)
    logger.info("[Playbook Content]:\n%s", content)
    file_path, close_func, cleanup_func = write_temp_file(content, suffix=".yml")
    close_func()
    return file_path, cleanup_func