"""ansible_runner相关的充血上下文模型与执行封装。"""

import ansible_runner
from .utils import fetch_bastion_key,extract_ansible_events

class AnsibleTaskContext:
    """
    只接收user_context和config_context，分别推断exec_type、module、module_args，记录错误。
    """
    def __init__(self, user_context, config_context):
        self.user_context = user_context
        self.config_context = config_context
        self.host_pattern = user_context.get_group_name()
        self.error = None

        try:
            self.exec_type = self._resolve_exec_type()
            self.module = self._resolve_module()
            self.module_args = self._resolve_module_args()
        except Exception as e:
            self.error = str(e)
            self.exec_type = None
            self.module = None
            self.module_args = None

    def _resolve_exec_type(self):
        if self.user_context.is_command_mode():
            return "command"
        elif self.user_context.is_script_mode():
            return "script"
        else:
            raise ValueError("参数不完整，无法判断执行模式")

    def _resolve_module(self):
        if self.user_context.is_command_mode():
            return self._get_command_module()
        elif self.user_context.is_script_mode():
            return self._get_script_module()
        else:
            raise ValueError("未知的执行模式")

    def _get_command_module(self):
        if self.user_context.is_linux():
            return "shell"
        elif self.user_context.is_windows():
            return "win_shell"
        else:
            raise ValueError("不支持的操作系统类型")

    def _get_script_module(self):
        if self.user_context.is_linux():
            return "script"
        elif self.user_context.is_windows():
            return "win_shell"
        else:
            raise ValueError("不支持的操作系统类型")

    def _resolve_module_args(self):
        if self.user_context.is_command_mode():
            return self.user_context.command
        elif self.user_context.is_script_mode():
            return self.user_context.file_path
        else:
            raise ValueError("未知的执行模式")

    def has_error(self):
        return self.error is not None
    
    def get_task_chain(self, inventory_path):
        """
        根据上下文生成任务链：
        - Linux命令/脚本：单步任务
        - Windows命令：单步任务
        - Windows脚本：三步任务链（win_copy, win_shell, win_file）
        """
        if self.user_context.is_linux():
            # Linux命令或脚本均为单步
            return [{
                "inventory": inventory_path,
                "host_pattern": self.host_pattern,
                "module": self.module,
                "args": self.module_args,
                "focus": True
            }]
        elif self.user_context.is_windows():
            if self.user_context.is_command_mode():
                # Windows命令为单步
                return [{
                    "inventory": inventory_path,
                    "host_pattern": self.host_pattern,
                    "module": self.module,
                    "args": self.module_args,
                    "focus": True
                }]
            elif self.user_context.is_script_mode():
                # Windows脚本为三步
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
    纯函数：执行ansible_runner.run并处理结果
    :param user_context: RemoteCallContext
    :param config_context: ansible配置上下文
    :param task_context: AnsibleTaskContext
    :param inventory_path: inventory文件路径
    :return: dict 统一结构 {status, data, error, raw}
    """
    # 这里 user_context 和 config_context 预留给后续扩展（如审计、权限、动态参数等）
    if user_context.is_use_bastion():
        cleanup = fetch_bastion_key(user_context, config_context)

    task_chain = task_context.get_task_chain(inventory_path)
    all_results = []
    focus_result = None
    task_chain = task_context.get_task_chain(inventory_path)
    all_results = []
    focus_result = None
    error = None
    target = None
    try:
        for task in task_chain:
            r = ansible_runner.run(
                private_data_dir=config_context.working_dir,
                inventory=task["inventory"],
                host_pattern=task["host_pattern"],
                module=task["module"],
                module_args=task["args"],
                quiet=True
            )
            results, task_error, event_data = extract_ansible_events(r)
            all_results.append({
                "task": f"{task['module']}:{task['args']}",
                "focus": task.get("focus", False),
                "result": results
            })
            # 聚焦主任务输出和event_data
            if task.get("focus", False):
                # 只聚焦第一个主机的结果（字典），无论单主机还是多主机
                if isinstance(results, list) and results:
                    focus_result = results[0]
                else:
                    focus_result = results
                target = event_data
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
        return {"status": "error", "data": None, "error": str(e), "raw": None}
    finally:
        if user_context.is_use_bastion():
            cleanup()