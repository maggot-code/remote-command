"""
ansible_runner 相关的上下文模型与执行封装。
本模块主要负责根据用户上下文和配置上下文，推断 Ansible 执行类型、模块、参数，并封装任务链的生成与执行。
"""

import ansible_runner
from .utils import fetch_bastion_key,extract_ansible_events

class AnsibleTaskContext:
    """
    Ansible 任务上下文。
    只接收 user_context 和 config_context，推断 exec_type、module、module_args，记录错误。
    用于生成适合当前上下文的 Ansible 任务链。
    """
    def __init__(self, user_context, config_context):
        """
        初始化任务上下文。
        :param user_context: 用户上下文，需实现 is_command_mode/is_script_mode/is_linux/is_windows 等方法
        :param config_context: ansible 配置上下文
        """
        self.user_context = user_context
        self.config_context = config_context
        self.host_pattern = user_context.get_group_name()
        self.error = None

        try:
            # 推断执行类型、模块、参数
            self.exec_type = self._resolve_exec_type()
            self.module = self._resolve_module()
            self.module_args = self._resolve_module_args()
        except Exception as e:
            self.error = str(e)
            self.exec_type = None
            self.module = None
            self.module_args = None

    def _resolve_exec_type(self):
        """
        推断执行类型（command/script）。
        """
        if self.user_context.is_command_mode():
            return "command"
        elif self.user_context.is_script_mode():
            return "script"
        else:
            raise ValueError("参数不完整，无法判断执行模式")

    def _resolve_module(self):
        """
        根据执行类型和操作系统推断 ansible module。
        """
        if self.user_context.is_command_mode():
            return self._get_command_module()
        elif self.user_context.is_script_mode():
            return self._get_script_module()
        else:
            raise ValueError("未知的执行模式")

    def _get_command_module(self):
        """
        获取命令模式下的 ansible module。
        Linux: shell，Windows: win_shell。
        """
        if self.user_context.is_linux():
            return "shell"
        elif self.user_context.is_windows():
            return "win_shell"
        else:
            raise ValueError("不支持的操作系统类型")

    def _get_script_module(self):
        """
        获取脚本模式下的 ansible module。
        Linux: script，Windows: win_shell（通过 win_copy+win_shell+win_file 实现）。
        """
        if self.user_context.is_linux():
            return "script"
        elif self.user_context.is_windows():
            return "win_shell"
        else:
            raise ValueError("不支持的操作系统类型")

    def _resolve_module_args(self):
        """
        推断 ansible module 的参数。
        command 模式取 command，script 模式取 file_path。
        """
        if self.user_context.is_command_mode():
            return self.user_context.command
        elif self.user_context.is_script_mode():
            return self.user_context.file_path
        else:
            raise ValueError("未知的执行模式")

    def has_error(self):
        """
        判断当前上下文是否存在错误。
        """
        return self.error is not None
    
    def get_task_chain(self, inventory_path):
        """
        根据上下文生成 ansible 任务链：
        - Linux 命令/脚本：单步任务
        - Windows 命令：单步任务
        - Windows 脚本：三步任务链（win_copy, win_shell, win_file）
        :param inventory_path: ansible inventory 路径
        :return: list[dict] 任务链
        """
        if self.user_context.is_linux():
            # Linux 命令或脚本均为单步
            return [{
                "inventory": inventory_path,
                "host_pattern": self.host_pattern,
                "module": self.module,
                "args": self.module_args,
                "focus": True
            }]
        elif self.user_context.is_windows():
            if self.user_context.is_command_mode():
                # Windows 命令为单步
                return [{
                    "inventory": inventory_path,
                    "host_pattern": self.host_pattern,
                    "module": self.module,
                    "args": self.module_args,
                    "focus": True
                }]
            elif self.user_context.is_script_mode():
                # Windows 脚本为三步：先拷贝脚本，再执行，最后清理
                remote_path = "C:\\Windows\\Temp\\script.ps1"
                return [
                    {
                        "inventory": inventory_path,
                        "host_pattern": self.host_pattern,
                        "module": "win_copy",
                        "args": f"src={self.module_args} dest={remote_path}",
                        "focus": False
                    },
                    {
                        "inventory": inventory_path,
                        "host_pattern": self.host_pattern,
                        "module": "win_shell",
                        "args": remote_path,
                        "focus": True
                    },
                    {
                        "inventory": inventory_path,
                        "host_pattern": self.host_pattern,
                        "module": "win_file",
                        "args": f"path={remote_path} state=absent",
                        "focus": False
                    }
                ]
        # 兜底：返回单步
        return [{
            "inventory": inventory_path,
            "host_pattern": self.host_pattern,
            "module": self.module,
            "args": self.module_args,
            "focus": True
        }]


def run_ansible_with_context(user_context, config_context, task_context, inventory_path):
    """
    执行 ansible_runner.run 并处理结果，返回统一结构。
    :param user_context: RemoteCallContext 用户上下文
    :param config_context: ansible 配置上下文
    :param task_context: AnsibleTaskContext 任务上下文
    :param inventory_path: inventory 文件路径
    :return: dict 统一结构 {status, data, error, all_results, target, raw}
    """

    if user_context.is_use_bastion():
        # 若使用堡垒机，先准备密钥，返回 cleanup 回调
        cleanup = fetch_bastion_key(user_context, config_context)

    task_chain = task_context.get_task_chain(inventory_path)
    all_results = []  # 所有任务的结果
    focus_result = None  # 主任务的结果
    error = None
    target = None  # event_data
    try:
        for task in task_chain:
            # 执行每个任务（支持多步任务链）
            r = ansible_runner.run(
                private_data_dir=config_context.working_dir,
                inventory=task["inventory"],
                host_pattern=task["host_pattern"],
                module=task["module"],
                module_args=task["args"],
                quiet=True
            )
            # 解析 ansible 执行事件，提取结果、错误、事件数据
            results, task_error, event_data = extract_ansible_events(r)
            all_results.append({
                "task": f"{task['module']}:{task['args']}",
                "focus": task.get("focus", False),
                "result": results
            })
            # 聚焦主任务输出和 event_data
            if task.get("focus", False):
                # 只聚焦第一个主机的结果（字典），无论单主机还是多主机
                if isinstance(results, list) and results:
                    focus_result = results[0]
                else:
                    focus_result = results
                target = event_data
            # 只保留第一个错误
            if task_error and not error:
                error = task_error
        status = "error" if error else "success"
        return {
            "status": status,
            "data": focus_result,
            "error": error,
            "all_results": all_results,
            "target": target,
            "raw": None
        }
    except Exception as e:
        # 捕获所有异常，返回 error 状态
        return {"status": "error", "data": None, "error": str(e), "raw": None}
    finally:
        if user_context.is_use_bastion():
            # 清理堡垒机密钥
            cleanup()