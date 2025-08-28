
import os
import tempfile
import uuid
import ansible_runner
import logging

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
)

DEFAULT_LINUX_PORT = 22
DEFAULT_WINDOWS_PORT = 5985
DEFAULT_WINDOWS_SSL_PORT = 5986


def confirm_port(os_type, password, port):
    """
    根据操作系统类型和用户输入,确认远程连接端口。
    linux 默认 22,windows 默认 5985/5986。
    Args:
        os_type (str): 操作系统类型(linux/windows)
        password (str|None): 密码(用于判断 winrm 端口)
        port (int|None): 用户指定端口
    Returns:
        int: 端口号
    """
    if port:  # 用户显式传入
        return int(port)
    if os_type == "linux":
        return DEFAULT_LINUX_PORT
    elif os_type == "windows":
        return DEFAULT_WINDOWS_SSL_PORT if not password else DEFAULT_WINDOWS_PORT
    else:
        raise ValueError(f"Unsupported os_type {os_type}")


def confirm_host_pattern(os_type):
    """
    根据操作系统类型返回 ansible 主机组名。
    Args:
        os_type (str): 操作系统类型
    Returns:
        str: 主机组名
    """
    return "linux_servers" if os_type == "linux" else "windows_servers"


def confirm_public_template(os_type):
    """
    返回 ansible 公共连接参数模板。
    Args:
        os_type (str): 操作系统类型
    Returns:
        str: 公共参数字符串
    """
    return {
        "linux": "ansible_connection=ssh ansible_python_interpreter=/usr/bin/python3",
        "windows": "ansible_connection=winrm ansible_winrm_transport=ntlm ansible_winrm_server_cert_validation=ignore"
    }[os_type]


def confirm_os_template(os_type, port):
    """
    返回 ansible 端口参数模板。
    Args:
        os_type (str): 操作系统类型
        port (int): 端口号
    Returns:
        str: 端口参数字符串
    """
    return f"ansible_port={port}"


def build_inventory(host_pattern, public_temp, os_temp, conn_info):
    """
    构建 ansible inventory 文件。
    Args:
        host_pattern (str): 主机组名
        public_temp (str): 公共参数模板
        os_temp (str): 端口参数模板
        conn_info (dict): 连接信息(ip, username, password, port)
    Returns:
        (str, function): inventory 文件路径,关闭函数
    """
    content = f"[{host_pattern}]\n"
    content += f"target ansible_host={conn_info['ip']} ansible_user={conn_info['username']} "
    if conn_info.get("password"):
        content += f"ansible_password={conn_info['password']} "
    content += f"{public_temp} {os_temp}\n"

    logging.info(f"[build_inventory] inventory content:\n{content}")
    f = tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".ini")
    f.write(content)
    f.close()
    return f.name, (lambda: os.unlink(f.name))


def build_command(inventory, host_pattern, command, os_type="linux"):
    """
    构建 ansible 执行命令任务。
    Args:
        inventory (str): inventory 文件路径
        host_pattern (str): 主机组名
        command (str): 要执行的命令
        os_type (str): 操作系统类型
    Returns:
        dict: 任务描述
    """
    module = "shell" if os_type == "linux" else "win_shell"
    return {
        "inventory": inventory,
        "host_pattern": host_pattern,
        "module": module,
        "args": command,
        "focus": True
    }


def build_script(inventory, host_pattern, file_path, os_type="linux"):
    """
    构建 ansible 执行脚本任务。
    Args:
        inventory (str): inventory 文件路径
        host_pattern (str): 主机组名
        file_path (str): 脚本路径
        os_type (str): 操作系统类型
    Returns:
        dict|list: 任务描述或任务列表(windows 下为多步)
    """
    if os_type == "linux":
        return {
            "inventory": inventory,
            "host_pattern": host_pattern,
            "module": "script",
            "args": file_path,
            "focus": True
        }
    elif os_type == "windows":
        remote_path = "C:\\Windows\\Temp\\script.ps1"
        return [
            {
                "inventory": inventory,
                "host_pattern": host_pattern,
                "module": "win_copy",
                "args": f"src={file_path} dest={remote_path}",
                "focus": False
            },
            {
                "inventory": inventory,
                "host_pattern": host_pattern,
                "module": "win_shell",
                "args": remote_path,
                "focus": True
            },
            {
                "inventory": inventory,
                "host_pattern": host_pattern,
                "module": "win_file",
                "args": f"path={remote_path} state=absent",
                "focus": False
            }
        ]
    else:
        raise ValueError(f"Unsupported OS type: {os_type}")


def execute_ansble(tasks):
    """
    执行 ansible 任务列表。
    Args:
        tasks (list): 任务列表(dict 或 list)
    Returns:
        dict: 执行结果,包括状态、job_id、原始结果等
    """
    job_id = str(uuid.uuid4())
    results = {"status": "success", "job_id": job_id, "data": {}, "error": None, "raw": []}

    expanded_tasks = []
    for t in tasks:
        if isinstance(t, list):
            expanded_tasks.extend(t)
        else:
            expanded_tasks.append(t)

    for task in expanded_tasks:
        logging.info(f"[execute_ansble] job_id={job_id} running task: {task}")
        r = ansible_runner.run(
            private_data_dir=".",
            inventory=task["inventory"],
            host_pattern=task["host_pattern"],
            module=task["module"],
            module_args=task["args"],
            quiet=True
        )

        task_result = {}
        for event in r.events:
            if event["event"] == "runner_on_ok":
                host = event["event_data"]["host"]
                res = event["event_data"]["res"]
                task_result[host] = res
                logging.info(f"[execute_ansble] OK {res}")
            if event["event"] in ("runner_on_failed", "runner_on_unreachable"):
                res = event["event_data"]["res"]
                error_type = event["event"].split("_")[-1].upper()
                results["status"] = "error"
                results["error"] = res
                logging.error(f"[execute_ansble] {error_type} {res}")

        results["raw"].append({
            "task": f"{task['module']}:{task['args']}",
            "focus": task.get("focus", False),
            "result": task_result
        })

    return results


def extract_result(exec_result):
    """
    提取 ansible 执行结果,聚焦主要任务。
    Args:
        exec_result (dict): execute_ansble 返回结果
    Returns:
        dict: 提炼后的结果,包含状态、job_id、data、error
    """
    if exec_result["status"] == "error":
        logging.error(f"[extract_result] error result: {exec_result}")
        return exec_result

    focus_results = [t for t in exec_result["raw"] if t["focus"]]
    if not focus_results:
        logging.error(f"[extract_result] No focused task found")
        return {
            "status": "error",
            "job_id": exec_result["job_id"],
            "data": None,
            "error": "No focused task found"
        }

    last_result = focus_results[-1]["result"]
    # 检查是否有 failed 或 unreachable 字段
    for host, res in last_result.items():
        if res.get("failed") or res.get("unreachable"):
            logging.error(f"[extract_result] host={host} failed or unreachable: {res}")
            return {
                "status": "error",
                "job_id": exec_result["job_id"],
                "data": None,
                "error": res
            }

    return {
        "status": exec_result["status"],
        "job_id": exec_result["job_id"],
        "data": last_result,
        "error": exec_result["error"]
    }
